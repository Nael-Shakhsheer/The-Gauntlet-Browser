"""Finite authored Adventure dungeons; no campaign schedules or repeat farming.

Permanent facts and deterministic encounter IDs survive recovery. An interrupted
sealed encounter is discarded and restarted in full, never merged with a cache.
"""
import copy
import math
import time
import feedback
import boss_ai
import combat_environment as terrain
import enemy_roles

SPECS = {
    'cave':dict(name='Rootwater passage',type='underground',danger=4,
        description='Explore four chambers from the Southern road to the hunter clearing. Ordinary chambers allow retreat; awakening the cave troll seals its den.',
        areas=['cave_entry','cave_gallery','cave_cache','cave_heart'],entrances=['road','clearing']),
    'tower':dict(name='Briarwatch tower',type='tower',danger=5,
        description='Three floors, five finite waves. Gather at the floor bell to begin. Waves seal the stairs; cleared floors allow retreat to camp. The summit opens the bridge east bank.',
        areas=['tower_1','tower_2','tower_3'],entrances=['camp','bridge']),
}
AREAS = {
    'cave_entry':dict(name='Rootwater · Entrance chamber',pos=[0,0],danger=4,region='cavern',dungeon='cave',exits=[('road','west','east'),('cave_gallery','east','west')]),
    'cave_gallery':dict(name='Rootwater · Split gallery',pos=[1,0],danger=4,region='cavern',dungeon='cave',exits=[('cave_entry','west','east'),('cave_cache','north','south'),('cave_heart','east','west')]),
    'cave_cache':dict(name='Rootwater · Surveyor alcove',pos=[1,-1],danger=4,region='cavern',dungeon='cave',exits=[('cave_gallery','south','north')]),
    'cave_heart':dict(name='Rootwater · Troll den',pos=[2,0],danger=5,region='cavern',dungeon='cave',exits=[('cave_gallery','west','east'),('clearing','east','west')]),
    'tower_1':dict(name='Briarwatch · Floor 1',pos=[0,0],danger=4,region='ruins',dungeon='tower',floor=1,exits=[('camp','west','east'),('tower_2','north','south')]),
    'tower_2':dict(name='Briarwatch · Floor 2',pos=[0,-1],danger=5,region='ruins',dungeon='tower',floor=2,exits=[('tower_1','south','north'),('tower_3','north','south')]),
    'tower_3':dict(name='Briarwatch · Floor 3',pos=[0,-2],danger=6,region='ruins',dungeon='tower',floor=3,exits=[('tower_2','south','north'),('bridge','west','east')]),
}
WALLS = {
    'cave_entry':[(250,35,90,145),(250,360,90,145),(650,35,75,120),(650,385,75,120)],
    'cave_gallery':[(335,110,80,80),(335,350,80,155),(560,35,75,155),(560,355,75,150)],
    'cave_cache':[(170,140,75,200),(710,140,75,200)],
    'cave_heart':[(270,105,65,75),(610,355,65,75)],
    'tower_1':[(260,155,60,60),(640,325,60,60)],
    'tower_2':[(245,205,75,100),(640,205,75,100)],
    'tower_3':[(225,140,70,80),(665,335,70,80)],
}
INTERIOR_POINTS={key:spec['pos'][:] for key,spec in AREAS.items()}
# Global graph positions describe travel directions; floor/chamber diagrams use
# their separate local coordinates rather than squeezing into the outdoor atlas.
for key,pos in {'cave_entry':[.35,1.5],'cave_gallery':[.8,1.5],'cave_cache':[.8,1.1],
                'cave_heart':[1.65,1.5],'tower_1':[1.35,2],'tower_2':[1.35,1.8],'tower_3':[1.35,1.6]}.items():
    AREAS[key]['pos']=pos
FEATURES = {
    'cave_entry':[('cave_supplies','Abandoned supply crate',450,390,'dungeon_treasure')],
    'cave_gallery':[('survey_marks','Surveyor’s trail marks',475,180,'dungeon_story')],
    'cave_cache':[('cave_survey','Surveyor’s hidden cache',510,350,'dungeon_treasure')],
    'cave_heart':[('dungeon_begin','Awaken the cave troll',380,400,'dungeon_begin')],
    **{f'tower_{i}':[('dungeon_begin',f'Floor {i} · ring the watch bell',480,430,'dungeon_begin')] for i in (1,2,3)},
}
LORE={
 'cave_entry':'Abandoned survey supplies mark the old toll passage. Roots broke its lamps; cave creatures now shelter here. Ordinary trails remain open.',
 'cave_gallery':'Chisel marks lead north to the surveyors’ dry alcove. East, heavy drag marks lead to the troll’s den. You can skirt the packs or retreat.',
 'cave_cache':'A dry shelf kept the surveyors’ reserve intact. Their notes chart a passage to the hunter’s clearing. Claim a ward or mana supply in Journal.',
 'cave_heart':'The troll hoards the old toll passage. Awakening it seals both exits; defeat opens a permanent route. A wipe returns to your inn/home recovery point.',
 'tower_1':'Hold space against the frontline, then remove the ranged guards behind it. Clear two waves; advance at the stairs when ready.',
 'tower_2':'Trap lanes divide the central court. Bait committed attacks into a lane, then reposition through either side. Keep a clear route to downed allies.',
 'tower_3':'Bait the captain’s charge into cover and counter during recovery. Guards begin after a short opening; keep revival space on the south side.'}
FLOOR_PACKS={
 'tower_1':[['troll','serpent','serpent'],['minotaur','serpent','troll','serpent']],
 'tower_2':[['minotaur','serpent','wolf','serpent'],['troll','serpent','minotaur','serpent']]}
FLOOR_SPOTS={
 'tower_1':[(420,200),(365,90),(650,105),(560,205),(780,170),(175,360),(780,405)],
 'tower_2':[(410,160),(140,165),(550,380),(810,375),(480,90),(150,400),(800,120)]}
PACKS = {'cave_entry':[(525,265,['spider','serpent','wolf'])],
    'cave_gallery':[(375,255,['wolf','serpent','spider']),(650,270,['troll','serpent','wolf'])],
         'cave_cache':[(520,190,['spider','serpent','wolf'])]}
# Authored gallery formations keep even the four-player entry spread outside
# ordinary aggro range, while leaving the north branch and stone corners open.
FORMATIONS={'cave_gallery':[
    [(345,280),(377,305),(408,320),(340,320),(375,332)],
    [(562,304),(592,305),(622,304),(590,338)],
]}
WAVE_ANCHORS=[(130,90),(210,90),(380,90),(580,90),(750,90),(840,90),
              (130,400),(480,370),(830,430),(480,210),(150,270),(800,270)]


def area_id(room): return (room.get('adventure') or {}).get('current')
def inside(room): return area_id(room) in AREAS
def ensure(room):
    states=room['adventure'].setdefault('dungeons',{})
    if not isinstance(states,dict) or any(key not in SPECS for key in states):
        raise ValueError('Unsupported Adventure dungeon records')
    for key,spec in SPECS.items():
        states.setdefault(key,dict(version=1,id=key,type=spec['type'],entrances=[],visited=[],
            completedEncounters=[],completedFloors=[],claimedTreasure=[],bossComplete=False,routeOpen=False,attempt=None))
        if not isinstance(states[key],dict) or states[key].get('version')!=1 or states[key].get('type')!=spec['type'] or states[key].get('id')!=key:
            raise ValueError('Unsupported dungeon record: '+key)
        s=states[key];attempt=s.get('attempt')
        if any(area not in spec['areas'] for area in s.get('visited',[])) or (attempt and
                (attempt.get('area') not in spec['areas'] or attempt.get('wave') not in (1,2))):
            raise ValueError('Unsupported dungeon location or attempt: '+key)
    return states


def state(room): return ensure(room)[AREAS[area_id(room)]['dungeon']]


def enemy(world,room,key,kind,x,y,boss=False):
    from game import DIFFICULTIES,AFFINITIES
    n=max(1,len(world._active_players(room)));danger=AREAS[area_id(room)]['danger']
    scale=DIFFICULTIES[room['difficulty']]['multiplier']/1.25
    hp=round((360 if boss else 36+danger*7)*(1+(.55 if boss else .16)*(n-1))*scale)
    name={'spider':'Cave Spider','wolf':'Wolf','serpent':'Serpent Guard','troll':'Cave Troll','minotaur':'Minotaur'}[kind]
    if boss:name='Rootwater Cave Troll' if state(room)['id']=='cave' else 'Briarwatch Minotaur Captain'
    e=dict(id=key,name=name,kind=kind,affinity='Nature',color=AFFINITIES['Nature'],baseColor='#85977a',
        x=x,y=y,hp=hp,maxHp=hp,damage=max(2,round((10 if boss else 4+danger)*scale)),speed=68 if boss else 68+danger*2,
        attackRate=1,boss=boss,bossPhase=1,group=key,homeX=x,homeY=y,aggroRadius=190,leashRadius=300,
        lastAttack=0,stunUntil=0,bleedUntil=0,bleedDamage=0,lastBleedTick=0,nextBossAttack=time.monotonic()+1.8)
    return e


def environment(area):
    # Authored rectangles are the same footprint drawn by the client. No invisible walls.
    env=dict(stage=AREAS[area]['danger'],region=AREAS[area]['region'],obstacles=[],zones=[],
        barriers=[dict(id=f'{area}-wall-{i}',x=x,y=y,width=w,height=h,material='stone',blocksShots=True)
                  for i,(x,y,w,h) in enumerate(WALLS[area])])
    if area=='tower_2':env['zones']=[dict(id='watch-trap-'+str(i),kind='trap',x=x,y=270,radius=32,warnAt=0,readyAt=0) for i,x in enumerate((410,550))]
    if area in ('cave_heart','tower_3'):
        env['obstacles']=[dict(id=area+'-cover-'+str(i),kind='rock',x=x,y=y,radius=22,hp=65,maxHp=65) for i,(x,y) in enumerate(((365,185),(600,310)))]
    return env


def build(world,room,area):
    previous=room['adventure']['current'];room['adventure']['current']=area
    try:
        env=environment(area)
        enemies=[];n=max(1,len(world._active_players(room)))
        for pack,(cx,cy,kinds) in enumerate(PACKS.get(area,[])):
            for i in range(len(kinds)+(n-1)//max(1,len(PACKS[area]))+int(pack<(n-1)%max(1,len(PACKS[area])))):
                x,y=FORMATIONS[area][pack][i] if area in FORMATIONS else (cx+(i%3-1)*32,cy+(i//3)*36)
                enemies.append(enemy(world,room,f'{area}-pack{pack}-{i}',kinds[i%len(kinds)],x,y))
        enemy_roles.assign({'enemies':enemies})
        return dict(size=[960,540],enemies=enemies,environment=env,encounterLayout=2,defeated=[],entered=True,details=[0]*6)
    finally:room['adventure']['current']=previous


def entered(world,room,source):
    states=ensure(room);here=area_id(room)
    if here in AREAS:
        s=state(room)
        if here not in s['visited']:s['visited'].append(here)
        if source in SPECS[s['id']]['entrances'] and source not in s['entrances']:s['entrances'].append(source)
        room['adventure']['locked']=False
        room['stageWaves']=1 if here=='tower_3' else 2 if here.startswith('tower_') else 1
    # Approaching an exterior entrance charts it without revealing its interior.
    for key,spec in SPECS.items():
        if here==spec['entrances'][0]:
            if here not in states[key]['entrances']:states[key]['entrances'].append(here)
            entry=spec['areas'][0]
            if entry not in room['adventure']['discovered']:room['adventure']['discovered'].append(entry)


def closed(room,source,destination):
    states=ensure(room)
    if {source,destination}=={'cave_heart','clearing'} and not states['cave']['routeOpen']:
        return 'The cave troll guards the far opening. Defeat it inside Rootwater passage.'
    if {source,destination}=={'tower_3','bridge'} and not states['tower']['routeOpen']:
        return 'Clear Briarwatch’s three floors to open the descent to the bridge east bank.'
    if destination in AREAS and AREAS[destination].get('floor',0)>1:
        floor=AREAS[destination]['floor']
        if source!='tower_'+str(floor+1) and floor-1 not in states['tower']['completedFloors']:
            return 'Clear the previous floor before using these stairs.'
    return None


def features(room):
    if not inside(room):return []
    s=state(room);here=area_id(room);result=[]
    for key,name,x,y,kind in FEATURES[here]:
        if kind=='dungeon_begin' and (s['attempt'] or s['bossComplete'] or AREAS[here].get('floor') in s['completedFloors']):continue
        if kind=='dungeon_treasure' and key in s['claimedTreasure']:continue
        result.append(dict(id=key,name=name,x=x,y=y,kind=kind,description=LORE[here] if kind in ('dungeon_story','dungeon_begin') else 'Personal supplies · choose a reward in Journal.'))
    return result


def interact(world,room,player,key):
    import adventure
    if key in ('cave_supplies','cave_survey'):
        s=state(room)
        if key in s['claimedTreasure']:return
        s['claimedTreasure'].append(key)
        adventure.reward(world,room,'dungeon:'+key,10 if key=='cave_supplies' else 16,'healing_draught' if key=='cave_supplies' else 'mana_draught')
        adventure.announce(world,room,'Surveyor’s notes: this passage once joined the road and clearing; the troll now holds the eastern opening.' if key=='cave_survey' else 'Old cave supplies recovered.')
    elif key=='dungeon_begin':
        humans=world._voting_players(room)
        feature=next(f for f in features(room) if f['id']==key)
        if not humans or any(p['status']!='alive' or math.hypot(p['x']-feature['x'],p['y']-feature['y'])>110 or p.get('dialogue') for p in humans):
            raise ValueError('Gather all connected hunters at the bell or seal to begin. Offline hunters and companions do not block it.')
        s=state(room)
        if s['attempt']:return
        if s['id']=='cave':
            s['attempt']=dict(area=area_id(room),wave=1);spawn_wave(world,room)
        else:
            here=area_id(room);wave=next((i for i in range(1,room['stageWaves']+1) if here+':'+str(i) not in s['completedEncounters']),None)
            if not wave:return
            s['attempt']=dict(area=here,wave=wave);room['stageWave']=wave
            world._spawn_wave(room,preserve_players=True)
        adventure.announce(world,room,'Encounter begun · exits sealed until the '+('guardian falls.' if s['id']=='cave' else 'floor is cleared. A three-second pause separates its waves.'))
        feedback.emit(room, 'encounter', dungeon=s['id'])
    elif key=='survey_marks':
        adventure.announce(world,room,LORE[area_id(room)])
    else:return False
    adventure.save(world,room);return True


def spawn_wave(world,room):
    """Explicit adapter from GameWorld._spawn_wave to fixed dungeon encounters.

    Reuses the combat lifecycle, roles, warnings, terrain and boss encounter tools;
    deliberately bypasses campaign spawning, pressure, chest and victory schedules.
    """
    s=state(room);here=area_id(room);attempt=s['attempt'];wave=attempt['wave']
    n=max(1,len(world._active_players(room)));enemies=[]
    if here in ('cave_heart','tower_3'):
        enemies=[enemy(world,room,here+'-boss','troll' if here=='cave_heart' else 'minotaur',480,245,True)]
        if here=='tower_3':
            for i in range(min(2,n)):
                e=enemy(world,room,here+'-guard-'+str(i),'serpent',160 if i==0 else 800,130)
                enemies.append(e)
    else:
        kinds=FLOOR_PACKS[here][wave-1]
        for i in range(len(kinds)+n-1):
            x,y=FLOOR_SPOTS[here][i]
            # A cleared wave can leave a rescuer/downed hunter on a spawn point.
            # Use finite authored alternatives, not a random/generated layout.
            actors=world._active_players(room)+room.get('summons',[])
            candidates=[(x,y)]+WAVE_ANCHORS
            spots=[p for p in candidates if terrain.walkable(room,*p) and
                   all(math.dist(p,(e['x'],e['y']))>=36 for e in enemies)]
            safe=next((p for p in spots if all(math.dist(p,(a['x'],a['y']))>=90 for a in actors)),None)
            x,y=safe or max(spots,key=lambda p:min((math.dist(p,(a['x'],a['y'])) for a in actors),default=999))
            enemies.append(enemy(world,room,f'{here}-w{wave}-{i}',kinds[i%len(kinds)],x,y))
    room.update(enemies=enemies,hazards=[],projectiles=[],waveStartsAt=0,stageWave=wave,
                encounterType='large_boss' if here in ('cave_heart','tower_3') else 'adventure_tower')
    room['adventure']['locked']=True
    enemy_roles.assign(room)
    for i,e in enumerate(enemies):
        if e.get('boss'):boss_ai.prepare(room,e)
        else:
            # Explicit tower role layout; automatic last-enemy support conversion
            # previously erased a ranged threat and stacked early windups.
            role=enemy_roles.ROLES[e['kind']]
            e.update(combatRole=role,**{'class':enemy_roles.KITS[role]},roleReadyAt=time.monotonic()+(.7+i*.35 if here!='tower_3' else 3.5+i*.5))


def on_kill(world,room):
    import adventure
    s=state(room);here=area_id(room)
    if room['enemies']:return
    if not s['attempt']:
        if here not in s['completedEncounters']:s['completedEncounters'].append(here)
        return
    wave=s['attempt']['wave'];key=here+':'+str(wave)
    if key not in s['completedEncounters']:s['completedEncounters'].append(key)
    if s['id']=='tower' and wave<room['stageWaves']:
        s['attempt']['wave']=wave+1;room['stageWave']=wave+1;room['waveStartsAt']=time.monotonic()+3
        adventure.announce(world,room,f'Floor {AREAS[here]["floor"]} · wave {wave} cleared. Next wave in 3 seconds. Stairs remain sealed.')
        return
    s['attempt']=None;room['adventure']['locked']=False;room['hazards']=[];room['projectiles']=[]
    feedback.emit(room, 'complete', major=here in ('cave_heart','tower_3'), dungeon=s['id'])
    if s['id']=='tower':
        floor=AREAS[here]['floor']
        if floor not in s['completedFloors']:s['completedFloors'].append(floor)
        adventure.reveal(room,*(target for target,_,_ in AREAS[here]['exits']
                               if target in AREAS and not closed(room,here,target)))
        adventure.reward(world,room,f'dungeon:tower:floor{floor}',8,'warding_tonic' if floor<3 else None)
        adventure.announce(world,room,f'Floor {floor} cleared. Gather at the stairs when ready, or return down to camp.')
    if here in ('cave_heart','tower_3'):
        s.update(bossComplete=True,routeOpen=True)
        far=SPECS[s['id']]['entrances'][1]
        if far not in s['entrances']:s['entrances'].append(far)
        adventure.reveal(room,far)
        adventure.reward(world,room,'dungeon:'+s['id'],40,'class_weapon')
        adventure.announce(world,room,SPECS[s['id']]['name']+' complete · permanent route open to '+adventure.area_name(room,far)+'.')


def recover(room):
    """Drop interrupted attempt bodies and clocks, retaining completed waves/IDs."""
    for s in ensure(room).values():
        attempt=s.get('attempt')
        if attempt:
            area=room['adventure']['areas'].get(attempt['area'])
            if area:area.update(enemies=[],environment=environment(attempt['area']))
            s['attempt']=None
    room['waveStartsAt']=0


def view(room):
    states=ensure(room);known=room['adventure']['discovered'];here=area_id(room)
    summaries=[]
    for key,spec in SPECS.items():
        s=states[key]
        if not s['entrances'] and not s['visited']:continue
        nodes=[dict(id=k,name=AREAS[k]['name'],position=INTERIOR_POINTS[k],current=k==here,
                    cleared=k in s['completedEncounters'] or (k=='cave_heart' and s['bossComplete']) or AREAS[k].get('floor') in s['completedFloors'],visited=k in s['visited'])
               for k in spec['areas'] if k in known]
        links=[dict(fromId=k,toId=t,locked=bool(closed(room,k,t))) for k in spec['areas'] if k in known
               for t,_,_ in AREAS[k]['exits'] if t in known and t in spec['areas'] and k<t]
        wave=s.get('attempt',{});wave=wave['wave'] if wave else 0
        summaries.append(dict(id=key,**{k:v for k,v in spec.items() if k not in ('areas','entrances')},complete=s['bossComplete'],routeOpen=s['routeOpen'],
            roomHint=(('The toll passage is open between road and clearing. Unclaimed supplies remain in the explored chambers.' if key=='cave' else
                       'The watch is quiet. Both entrances stay open; cleared floors and claimed rewards remain completed.') if s['bossComplete'] else LORE.get(here))
                      if inside(room) and AREAS[here]['dungeon']==key else None,
            entrances=list(s['entrances']),nodes=nodes,links=links,treasure=len(s['claimedTreasure']),surveyFound='cave_survey' in s['claimedTreasure'],
            floors=list(s['completedFloors']),current=inside(room) and AREAS[here]['dungeon']==key,
            floor=AREAS.get(here,{}).get('floor'),wave=wave,waves=room['stageWaves'] if inside(room) else 0,
            breakLeft=max(0,room.get('waveStartsAt',0)-time.monotonic()),
            objective=('Dungeon complete · both entrances are open. Completed encounters stay cleared.' if s['bossComplete'] else
                       'Defeat the guardian to open the far exit.' if here in ('cave_heart','tower_3') else
                       'Fight the current wave; stairs are sealed.' if s['attempt'] else
                       'Floor cleared · stairs are open.' if AREAS.get(here,{}).get('floor') in s['completedFloors'] else
                       'Gather at the bell to begin.' if key=='tower' else 'Explore east; the northern gallery trail hides a cache.')))
    return summaries
