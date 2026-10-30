"""Finite Dunmere continuation using the existing dungeon/save/combat lifecycle."""
import copy
import math
import time

OUTDOORS={
 'irrigation_channels':dict(name='Dunmere · upper irrigation',pos=[2,5.65],danger=7,region='woodland',exits=[('eastern_threshold','north','south'),('farmstead','east','west'),('pump_chamber','south','south')]),
 'farmstead':dict(name='The abandoned farmstead',pos=[3,5.65],danger=7,region='woodland',exits=[('irrigation_channels','west','east'),('pump_exterior','north','south')]),
 'pump_exterior':dict(name='Dunmere pumping station',pos=[3,5],danger=8,region='ruins',exits=[('farmstead','south','north'),('sluice_entry','east','west')]),
}
INTERIORS={
 'sluice_entry':dict(name='Sluice · intake tunnels',pos=[0,0],danger=7,region='cavern',dungeon='sluice',exits=[('pump_exterior','west','east'),('sluice_gallery','east','west')]),
 'sluice_gallery':dict(name='Sluice · divided channels',pos=[1,0],danger=8,region='cavern',dungeon='sluice',exits=[('sluice_entry','west','east'),('sluice_alcove','north','south'),('pump_chamber','east','west')]),
 'sluice_alcove':dict(name='Sluice · dry survey reserve',pos=[1,-1],danger=7,region='cavern',dungeon='sluice',exits=[('sluice_gallery','south','north')]),
 'pump_chamber':dict(name='Sluice · the pumping heart',pos=[2,0],danger=8,region='cavern',dungeon='sluice',exits=[('sluice_gallery','west','east'),('irrigation_channels','south','south')]),
}
FEATURES={
 'irrigation_channels':[('upstream_sample','Inspect the upstream deposit',420,315,'clue')],
 'farmstead':[('farm_record','Read the abandoned farm record',650,190,'clue'),('root_sump_begin','Optional · open the root sump',680,410,'mechanism')],
 'pump_exterior':[('steward_account','Read the steward’s account',520,250,'clue')],
 'sluice_entry':[('valve_west','Restore the intake channel',450,390,'mechanism'),('sluice_supplies','Sealed maintenance supplies',650,400,'dungeon_treasure')],
 'sluice_gallery':[('valve_east','Isolate the tainted branch',480,365,'mechanism')],
 'sluice_alcove':[('sluice_survey','Surveyor’s dry reserve',510,330,'dungeon_treasure')],
 'pump_chamber':[('warden_begin','Awaken the Harvest Warden · exits seal',360,400,'mechanism'),('intake_restored','Restore the main intake',700,370,'mechanism')],
}
TEXT={
 'upstream_sample':'Pale fibres collect above the mill, where the water should be clean. A farm record east of here may identify the shipment. Bring both findings to Tovin.',
 'farm_record':'The last farmer refused a second delivery: the additive made roots split the water jars. The steward ordered it kept out of the public ledger. His station account is north of this farm.',
 'steward_account':'The steward knew the additive came from living roots below the station. He concealed the risk to prevent a second empty harvest. He left a relief reserve: clean shelters and masks for workers, or safe water for farmers. Discuss the choice with Tovin; either leaves enough to repair the intake.',
 'valve_west':'The clean intake is restored. Its stone wheel now feeds the safe channel. The tainted branch farther east must be isolated before the main pump runs.',
 'valve_east':'The tainted branch is isolated. The dry survey reserve is north, marked by pale chisel arrows. Reach the eastern chamber and report the secured route to Tovin before awakening its guardian.',
 'intake_restored':'Safe water returns at a limited rate. One more Dunmere strip can recover; the ruined farms will take longer. Report to Tovin. The opened service drain leads back to the upper irrigation channel.',
}
LORE={
 'sluice_entry':'A clean intake wheel stands beside abandoned maintenance supplies. Ordinary tunnels allow retreat. Restore the intake and isolate the branch farther east.',
 'sluice_gallery':'Pale survey marks lead north to a dry reserve. East, the pumping heart still moves. The ordinary passage stays open until you awaken its Warden.',
 'sluice_alcove':'A dry shelf, chisel arrows and folded canvas protected a surveyor’s reserve. Each hunter may claim its Magic Rune; supplies are delivered automatically.',
 'pump_chamber':'Report the secured route to Tovin, then return ready. Awakening the Warden seals the chamber. Roots shield it twice; destroy them or fight through reduced damage. Every marked attack leaves a recovery window.',
}


def install(adventure):
    import dungeons,region_content
    region_content.AREAS.update(copy.deepcopy(OUTDOORS));adventure.AREAS.update(copy.deepcopy(OUTDOORS))
    adventure.LARGE_AREAS.update({k:(1200,720) for k in OUTDOORS})
    region_content.GROUPS.update({'irrigation_channels':[('channel-roam','serpent',320,210,2),('silt-bank','wolf',730,405,2)],
      'farmstead':[('barn-guards','troll',650,280,1),('dry-field','serpent',320,380,2)],'pump_exterior':[('station-guards','serpent',650,180,2),('station-flank','minotaur',330,360,1)]})
    adventure.GROUPS.update(copy.deepcopy({k:region_content.GROUPS[k] for k in OUTDOORS}))
    adventure.AREAS['eastern_threshold']['exits'].append(('irrigation_channels','south','north'))
    adventure.AREAS['eastern_threshold']['exits'].append(('pump_exterior','east','west'))
    adventure.AREAS['pump_exterior']['exits'].append(('eastern_threshold','west','east'))
    adventure.EXIT_OFFSETS[('eastern_threshold','pump_exterior')]=.5
    # The service drain bends underground; local chamber maps describe its turns.
    dungeons.SPECS['sluice']=dict(name='Dunmere sluice works',type='underground',danger=8,description='Explore the branching maintenance route. Ordinary tunnels permit retreat. Awakening the Harvest Warden seals the heart; victory opens a service drain to upper irrigation.',areas=list(INTERIORS),entrances=['pump_exterior','irrigation_channels'])
    dungeons.AREAS.update(copy.deepcopy(INTERIORS));adventure.AREAS.update(copy.deepcopy(INTERIORS))
    dungeons.INTERIOR_POINTS.update({k:s['pos'][:] for k,s in INTERIORS.items()})
    # Geographic positions also follow every physical doorway. The service drain
    # goes west from the heart then bends south, arriving at the north bank.
    for k,pos in {'sluice_entry':[3.35,5],'sluice_gallery':[3.8,5],'sluice_alcove':[3.8,4.6],'pump_chamber':[4.3,5]}.items():
        dungeons.AREAS[k]['pos']=pos;adventure.AREAS[k]['pos']=pos
    adventure.AREAS['irrigation_channels']['exits'][-1]=('pump_chamber','east','west')
    adventure.AREAS['pump_chamber']['exits'][-1]=('irrigation_channels','west','east')
    dungeons.AREAS['pump_chamber']['exits'][-1]=('irrigation_channels','west','east')
    adventure.EXIT_OFFSETS[('irrigation_channels','pump_chamber')]=.78
    adventure.EXIT_OFFSETS[('pump_chamber','irrigation_channels')]=.80
    walls={'sluice_entry':[(250,35,75,145),(250,365,75,140),(700,35,70,115)],
      'sluice_gallery':[(315,80,70,110),(315,385,70,120),(600,75,70,100),(600,420,70,85)],
      'sluice_alcove':[(170,120,70,200),(720,120,70,200)],'pump_chamber':[(250,110,65,80),(645,110,65,80)]}
    dungeons.WALLS.update(walls);dungeons.LORE.update(LORE)
    dungeons.FEATURES.update({k:v for k,v in FEATURES.items() if k in INTERIORS})
    dungeons.PACKS.update({'sluice_entry':[(520,260,['wolf','serpent','spider'])],
        'sluice_gallery':[(400,270,['troll','serpent','wolf']),(735,310,['serpent','spider','wolf'])],
        'sluice_alcove':[(490,160,['spider','serpent'])]})


def facts(room):return __import__('chapter_flow').ensure(room)['evidence']


def features(room):
    import adventure,chapter_flow
    here=room['adventure']['current'];s=chapter_flow.ensure(room);result=[]
    for key,name,x,y,kind in FEATURES.get(here,[]):
        if here in INTERIORS:continue # The ordinary dungeon adapter owns these.
        if key=='root_sump_begin' and (s['stages']['root_sump'] not in ('accepted','ready-to-turn-in') or 'sump_cleared' in facts(room)):continue
        x,y=adventure.point(room,x,y);result.append(dict(id=key,name=name,x=x,y=y,kind=kind))
    return result


def barriers(room):
    import adventure
    here=room['adventure']['current'];w,h=room.get('areaSize',adventure.LARGE_AREAS.get(here,(960,540)))
    boxes={'irrigation_channels':[(170,110,270,55,'water'),(620,320,130,55,'water')],
      'farmstead':[(565,110,170,65,'wood')],'pump_exterior':[(430,125,170,65,'stone')]}.get(here,[])
    return [dict(id=here+'-works-'+str(i),x=x*w/960,y=y*h/540,width=bw*w/960,height=bh*h/540,material=m,blocksShots=True) for i,(x,y,bw,bh,m) in enumerate(boxes)]


def closed(room,source,target):
    import dungeons,chapter_flow
    if {source,target}=={'eastern_threshold','pump_exterior'} and not __import__('campaign_quests').done(room,'upstream'):return 'The maintenance causeway is choked with roots. Report both upstream findings to Tovin; workers reopen this direct station route.'
    if {source,target}=={'pump_chamber','irrigation_channels'} and not dungeons.ensure(room)['sluice']['routeOpen']:return 'The service drain opens from the pumping heart after defeating the Warden. Enter through the station, north of the farmstead.'
    # No unrelated woodland prerequisites: explore and collect evidence early.
    return None


def begin(world,room,p,sump=False):
    import chapter_flow,dungeons,adventure,boss_ai
    key='root_sump' if sump else 'pumping_finale';chapter_flow.require(room,key)
    if ('sump_cleared' if sump else 'warden_defeated') in facts(room):return
    humans=world._voting_players(room)
    if not humans or any(x['status']!='alive' or x.get('dialogue') or math.dist((x['x'],x['y']),(p['x'],p['y']))>130 for x in humans):raise ValueError('Gather the connected party at the seal before committing. Offline hunters and companions do not block it.')
    if room['enemies']:raise ValueError('Clear the immediate approach before awakening this sealed encounter.')
    if sump:
        if not __import__('campaign_quests').done(room,'pumping_finale'):raise ValueError('Restore the main works before attempting the optional sump.')
    elif not all(f in facts(room) for f in ('valve_west','valve_east','chamber_reached')):raise ValueError('Secure both mechanisms and reach this chamber first.')
    n=max(1,len(world._active_players(room)));from game import DIFFICULTIES,AFFINITIES
    scale=DIFFICULTIES[room['difficulty']]['multiplier']/1.25;hp=round((850 if sump else 680)*(1+.55*(n-1))*scale)
    if sump:x,y=adventure.point(room,680,300)
    else:x,y=480,225
    boss=dict(id='root-sump-boss' if sump else 'harvest-warden',name='Root Sump Keeper' if sump else 'Harvest Warden',kind='troll',affinity='Nature',color=AFFINITIES['Nature'],baseColor='#8b9f66',x=x,y=y,hp=hp,maxHp=hp,damage=round((12 if sump else 10)*scale),speed=70,attackRate=1,boss=True,bossPhase=1,lastAttack=0,stunUntil=0,bleedUntil=0,bleedDamage=0,lastBleedTick=0,nextBossAttack=time.monotonic()+2)
    room.update(enemies=[boss],hazards=[],projectiles=[],encounterType='large_boss',encounterName=boss['name']);room['adventure']['locked']=True
    if not sump:dungeons.state(room)['attempt']=dict(area='pump_chamber',wave=1)
    else:
        for i in range(2):
            e=copy.deepcopy(boss);e.update(id='root-sump-guard-'+str(i),name='Sump Serpent',kind='serpent',boss=False,hp=80,maxHp=80,damage=7,x=x+(-145 if i==0 else 145),y=y-100)
            e.update(homeX=e['x'],homeY=e['y'],combatRole='ranged',**{'class':'Archer'},roleReadyAt=time.monotonic()+3+i)
            room['enemies'].append(e)
    adventure.announce(world,room,boss['name']+' awakened · exits sealed. Dodge the marked attacks; recovery returns to the inn with completed objectives kept.')
    __import__('feedback').emit(room,'encounter',dungeon='sluice');adventure.save(world,room)


def interact(world,room,p,key):
    import adventure,chapter_flow,progression,dungeons,magic_runes
    here=room['adventure']['current']
    if key not in {k for rows in FEATURES.values() for k,*_ in rows}:return False
    if key in ('warden_begin','root_sump_begin'):begin(world,room,p,key=='root_sump_begin');return True
    if key in ('sluice_supplies','sluice_survey'):
        s=dungeons.state(room)
        earned=False
        if key=='sluice_survey':
            if 'sluice_survey_found' not in room['adventure']['claimed']:room['adventure']['claimed'].append('sluice_survey_found')
            earned=magic_runes.claim(p,'cache:sluice_survey')
        if key not in s['claimedTreasure']:
            s['claimedTreasure'].append(key);adventure.reward(world,room,'dungeon:'+key,12,'healing_draught' if key=='sluice_supplies' else 'warding_tonic')
        progression.inspect(p,'Dry maintenance reserve','The surveyors marked this safe shelf above the tainted water. '+(('Your personal Magic Rune is added.' if earned else 'Your personal rune was already claimed; no duplicate was awarded.')+' Supplies deliver automatically; a full pouch converts only the new reward.' if key=='sluice_survey' else 'Maintenance supplies recovered; ordinary retreat remains open.'))
    else:
        if key in ('valve_west','valve_east'):chapter_flow.require(room,'sluice_route')
        if key=='intake_restored':
            chapter_flow.require(room,'pumping_finale')
            if not dungeons.ensure(room)['sluice']['bossComplete']:raise ValueError('Defeat the Harvest Warden before opening the intake.')
        chapter_flow.evidence(room,key);progression.inspect(p,key.replace('_',' ').title(),TEXT[key])
        if key=='intake_restored':adventure.announce(world,room,'Safe intake restored · another Dunmere strip can recover. Service-drain shortcut open to upper irrigation. Report to Tovin.')
    adventure.save(world,room);return True


def entered(room):
    if room['adventure']['current']=='pump_chamber':__import__('chapter_flow').evidence(room,'chamber_reached')


def tick_boss(world,room,e,now):
    if e['id'] not in ('harvest-warden','root-sump-boss'):return
    phase=e.get('bossPhase',1)
    if phase<3 and e['hp']<=e['maxHp']*(.65 if phase==1 else .30) and not any(a['id'].startswith(e['id']+'-root') for a in room['enemies']):
        e['bossPhase']=phase+1;e.update(recoverUntil=now+2,nextBossAttack=now+3)
        # Root hearts are stationary, destructible, with explicit silhouettes.
        for i in range(2 if phase==1 else 1):
            x,y=((370,330),(620,330))[i] if e['id']=='harvest-warden' else (e['x']+(-95 if i==0 else 95),e['y']+100)
            hp=round((48 if phase==1 else 65)*(1+.25*(max(1,len(world._active_players(room)))-1)))
            room['enemies'].append(dict(id=e['id']+'-root'+str(phase)+'-'+str(i),name='Root heart · shields the Warden',kind='troll',structure=True,affinity='Nature',color='#83ae6b',baseColor='#83ae6b',x=x,y=y,hp=hp,maxHp=hp,damage=0,speed=0,attackRate=1,boss=False,group=e['id']+'-roots'))
        __import__('adventure').announce(world,room,'Root hearts rise · break them for a recovery opening. The Warden takes reduced damage while they remain.')


def damage_factor(room,e):
    return .65 if e['id'] in ('harvest-warden','root-sump-boss') and any(a['id'].startswith(e['id']+'-root') for a in room['enemies']) else 1


def on_kill(world,room,e):
    import adventure,dungeons,chapter_flow
    if e['id'].startswith(('harvest-warden-root','root-sump-boss-root')):
        boss=next((a for a in room['enemies'] if a['id'] in ('harvest-warden','root-sump-boss')),None)
        if boss and not any(a.get('structure') for a in room['enemies']):boss.update(recoverUntil=time.monotonic()+3,vulnerableUntil=time.monotonic()+5,nextBossAttack=time.monotonic()+4)
    if e['id']=='harvest-warden':
        room['enemies']=[a for a in room['enemies'] if not a['id'].startswith('harvest-warden-root')];s=dungeons.state(room)
        s.update(bossComplete=True,routeOpen=True,attempt=None)
        if 'pump_chamber:1' not in s['completedEncounters']:s['completedEncounters'].append('pump_chamber:1')
        if 'irrigation_channels' not in s['entrances']:s['entrances'].append('irrigation_channels')
        room['adventure']['locked']=False;room.update(projectiles=[],hazards=[]);chapter_flow.evidence(room,'warden_defeated');adventure.reveal(room,'irrigation_channels')
        adventure.announce(world,room,'Harvest Warden defeated · restore the main intake. The service drain now connects this chamber to upper irrigation.');__import__('feedback').emit(room,'complete',major=True,dungeon='sluice')
    if e['id'].startswith('root-sump-'):
        if not any(a['id'].startswith('root-sump-') for a in room['enemies']):
            room['adventure']['locked']=False;room.update(projectiles=[],hazards=[]);chapter_flow.evidence(room,'sump_cleared');adventure.announce(world,room,'Optional root sump cleared · the dry store is safe. Report to Tovin for its finite reward.')
        return True
    return e['id'].startswith('harvest-warden')


def recover(room):
    if 'sump_cleared' in facts(room):return
    s=room['adventure']['areas'].get('farmstead')
    if s:s['enemies']=[e for e in s['enemies'] if not e['id'].startswith('root-sump-')]
    if room['adventure']['current']=='farmstead':room['enemies']=[e for e in room.get('enemies',[]) if not e['id'].startswith('root-sump-')]
