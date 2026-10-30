"""Authored woodland expansion and the finite Dunmere first chapter.

The art palette is independent of progression region. Stable IDs/coordinates and
finite named encounters remain authoritative; no procedural rooms or respawns.
"""
import copy
import math
import time
import random

HUBS={'home':'Oakvale','dunmere':'Dunmere'}
AREAS={
 'brook':dict(name='Clouded brook',pos=[-1,1],danger=1,region='woodland',exits=[('road','east','west'),('mill_trail','north','south')]),
 'mill_trail':dict(name='Old mill trail',pos=[-1,.4],danger=2,region='woodland',exits=[('brook','south','north'),('road','east','west')]),
 'yard':dict(name='Logging yard · stranded camp',pos=[1,2.7],danger=3,region='woodland',exits=[('camp','north','south'),('hollow','east','west')]),
 'hollow':dict(name='Deepwood hollow',pos=[2,2.7],danger=4,region='woodland',exits=[('yard','west','east'),('clearing','north','south'),('watch','south','north')]),
 'watch':dict(name='Burned watch approach',pos=[2,3.5],danger=5,region='woodland',exits=[('hollow','north','south'),('network','west','east')]),
 'network':dict(name='Old network approach',pos=[1,3.5],danger=5,region='ruins',exits=[('watch','east','west'),('ruins','west','east')]),
 'border':dict(name='Dunmere border road',pos=[0,4],danger=5,region='woodland',exits=[('ruins','north','south'),('dunmere','south','north')]),
 'dunmere':dict(name='Dunmere · village hub',pos=[0,5],danger=0,region='woodland',exits=[('border','north','south'),('fields','east','west')]),
 'fields':dict(name='Dunmere · failed fields',pos=[1,5],danger=6,region='woodland',exits=[('dunmere','west','east'),('mill','south','north'),('cellar','east','north'),('eastern_threshold','east','west')]),
 'mill':dict(name='Dunmere · ruined mill',pos=[1,6],danger=7,region='ruins',exits=[('fields','north','south'),('cellar','east','west')]),
 'eastern_threshold':dict(name='Dunmere · eastern threshold',pos=[2,5],danger=6,region='woodland',exits=[('fields','west','east')]),
 'cellar':dict(name='Dunmere · mill cellar',pos=[2,6],danger=7,region='cavern',exits=[('mill','west','east'),('fields','north','east')]),
}
SIZES={'brook':(1280,800),'yard':(1440,900),'hollow':(1600,1000),'watch':(1280,800),'network':(1200,720),
       'border':(960,720),'fields':(1600,960),'mill':(1200,800),'eastern_threshold':(1280,800)}
GROUPS={
 'brook':[('brook-shrine','wolf',620,205,2),('reed-bank','spider',250,370,1)],
 'mill_trail':[('wheel-road','serpent',570,310,2)],
 'yard':[('timber-guards','wolf',530,210,2),('workers-approach','serpent',710,360,2)],
 'hollow':[('hollow-shrine','serpent',630,250,2),('hollow-shrine-flank','wolf',710,340,2),('old-roots','spider',220,170,2)],
 'watch':[('watch-shrine','minotaur',600,240,1),('watch-shrine-archers','serpent',705,340,2)],
 'network':[('network-sentries','serpent',350,240,2),('broken-stones','troll',650,360,1)],
 'border':[('border-road','wolf',320,330,2)],
 'fields':[('ditch-stalkers','spider',310,290,3),('granary-guards','serpent',700,210,2),('field-roots','wolf',650,400,2)],
 'mill':[('mill-approach','serpent',365,250,2),('mill-approach-flank','troll',650,370,1)],
 'eastern_threshold':[('dry-hedge','wolf',350,380,2),('abandoned-shed','serpent',780,230,2)],
 'cellar':[('cellar-approach','spider',450,270,2)],
}
SHRINES={
 'brook':dict(area='brook',x=690,y=180,name='Brook travel shrine',guards='brook-shrine',description='Clear the Brook shrine’s wolf sentries, then attune the spring stone.'),
 'deepwood':dict(area='hollow',x=680,y=270,name='Deepwood travel shrine',guards='hollow-shrine',description='Clear the hollow shrine defenders, then restore its waystone.'),
 'watch':dict(area='watch',x=690,y=290,name='Watch travel shrine',guards='watch-shrine',description='Read the watch register and clear its displaced guards, then attune.'),
}
# Compact coordinates scale with authored larger areas, exactly like old clues.
FEATURES={
 'brook':[('brook_outlet','Inspect the cloudy outlet',380,290,'clue')],
 'mill_trail':[('mill_wheel','Inspect the damaged wheel',570,180,'clue')],
 'yard':[],
 'hollow':[('dry_spring','Concealed spring casket',870,95,'discovery')],
 'watch':[('watch_register','Read the burned watch register',390,265,'clue')],
 'network':[('network_seal','Inspect the network seal',480,300,'clue')],
 'ruins':[('pumping_register','Recover the pumping register',480,320,'clue')],
 'dunmere':[('runner','Village Runner',640,405,'talk')],
 'fields':[('dry_ditch','Inspect the dry ditch',275,180,'clue'),('rooted_crop','Inspect the rooted crop',570,355,'clue'),
           ('empty_granary','Inspect the empty granary',760,180,'clue'),('field_restored','Inspect the restored field',470,420,'clue')],
 'mill':[('channel_west','Clear the west channel',290,360,'mechanism'),('channel_east','Clear the east channel',690,360,'mechanism'),('sluice_open','Operate the sluice',480,225,'mechanism')],
 'eastern_threshold':[('east_landmark','Read the abandoned farm marker',790,345,'discovery'),('ridge_barrier','Ashen Ridge · distant volcanic road',915,420,'clue')],
 'cellar':[('cellar_begin','Open the sealed pump chamber',570,290,'mechanism'),('additive_ledger','Recover the additive ledger',665,250,'clue')],
}
TEXT={
 'brook_outlet':'Cloudy water and a pale residue flow from the old network. The grain wagons stopped before the watch burned. The damaged wheel upstream may show when the flow changed.',
 'mill_wheel':'The wheel stopped before the attack. Its channel is clogged with dry roots and pale silt. Take both observations back to the Oakvale runner.',
 'watch_register':'The last register records the dragon striking a spring seal, not pursuing the caravan. The creatures fled the deep woods before its arrival. An old network inscription lies west.',
 'network_seal':'The shrine, watch and Minotaur ruins regulated one underground spring. A damaged seal points to excessive pumping downstream. The Minotaur now protects the wrong boundary.',
 'pumping_register':'Dunmere drew more water than the woodland could supply. The grain crisis began before the dragon broke the watch seal. Return this register to Oakvale.',
 'dry_ditch':'The irrigation ditch is dry above a knot of roots. Drought alone does not explain the blockage.',
 'rooted_crop':'Harvest additive coats the failed crop. Small roots spread where the mixture settled.',
 'empty_granary':'The grain bins are empty. A delivery note mentions a concentrated additive from the mill cellar.',
 'field_restored':'Water reaches one repaired strip. Green shoots survive along the ditch; the rest of Dunmere still needs help. Bring the ledger to the runner.',
 'additive_ledger':'The steward concealed the risks of material raised from the pumping tunnels. The additive first improved yields, then fed the roots. Report the local mill crisis, then ask Tovin about tracing it upstream. Ashen Ridge remains beyond these repairs.',
}


def install(adventure):
    adventure.AREAS.update(copy.deepcopy(AREAS));adventure.LARGE_AREAS.update(SIZES);adventure.GROUPS.update(copy.deepcopy(GROUPS))
    for source,destination,edge,reverse in [('road','brook','west','east'),('road','mill_trail','west','east'),('camp','yard','south','north'),('clearing','hollow','south','north'),('ruins','network','east','west'),('ruins','border','south','north')]:
        if (destination,edge,reverse) not in adventure.AREAS[source]['exits']:adventure.AREAS[source]['exits'].append((destination,edge,reverse))
    adventure.EXIT_OFFSETS.update({('road','brook'):.75,('road','mill_trail'):.24,('clearing','hollow'):.84,('fields','eastern_threshold'):.32,('fields','cellar'):.67,('cellar','fields'):.5,('eastern_threshold','fields'):.32})


def ensure(room):
    a=room['adventure'];s=a.setdefault('regionProgress',dict(version=1,cellarComplete=False,cellarAttempt=False))
    if s.get('version')!=1:raise ValueError('Unsupported region progress; original preserved.')
    return s


def blocked(room,source,target):
    import chapter_flow
    s=chapter_flow.ensure(room)
    if target=='border' and s['stages']['border'] not in ('accepted','ready-to-turn-in','complete'):return 'Report the woodland conclusion and accept the Grain Road assignment from Oakvale’s runner.'
    if {source,target}=={'network','ruins'} and not room['adventure']['bridge']:return 'The flooded old approach is closed. Restore the supply bridge before using this route.'
    if source=='fields' and target=='cellar' and not ensure(room)['cellarComplete']:return 'The cellar’s outer hatch is barred from inside. Enter through the ruined mill first.'
    return None


def features(room):
    import adventure
    a=room['adventure'];here=a['current'];s=ensure(room);result=[]
    for key,name,x,y,kind in FEATURES.get(here,[]):
        if key=='pumping_register' and not a['bossComplete']:continue
        if key=='additive_ledger' and not s['cellarComplete']:continue
        if key=='cellar_begin' and s['cellarComplete']:continue
        if key=='field_restored' and 'sluice_open' not in __import__('chapter_flow').ensure(room)['evidence']:continue
        if here in HUBS:x,y=adventure.home_npc_position(room,x,y)
        else:x,y=adventure.point(room,x,y)
        result.append(dict(id=key,name=name,x=x,y=y,kind=kind))
    for key,spec in SHRINES.items():
        if spec['area']!=here:continue
        x,y=adventure.point(room,spec['x'],spec['y'])
        result.append(dict(id='attune_'+key,name=spec['name'],kind='travel_shrine',x=x,y=y,shrine=key,active=key in shrine_state(room)['active']))
    return result


def description(key):
    return {'irrigation_channels':'Upper irrigation south of the threshold. Trace the pale deposit; east leads to the farm. The lower east service drain opens after the Warden falls.',
      'farmstead':'Abandoned crop stores and a refusal of the steward’s additive. North: pumping station. After the works recover, Tovin offers a finite harder sump challenge here.',
      'pump_exterior':'The steward’s account stands outside the east sluice entrance. Ordinary tunnels allow retreat; the pumping heart seals only when deliberately awakened.',
      'brook':'Cloudy spring water and a guarded Brook waystone. An old wheel lies north along the mill trail.',
      'mill_trail':'A loop between the Southern road and cloudy brook. Inspect the stopped wheel beside the trail.',
      'yard':'A stranded timber camp south of the abandoned camp. Workers describe creatures fleeing the deep woods.',
      'hollow':'A wide eastern hollow with a guarded waystone and a readable side trail toward a dry spring.',
      'watch':'The burned watch overlooks the old spring network. Its register explains the shrine’s guardians.',
      'network':'An inscription links the spring mechanism to the Minotaur ruins. The flooded approach requires a repaired bridge.',
      'border':'The grain road south of the old ruins. Accept the border assignment in Oakvale before traveling.',
      'dunmere':'A working village with shops, Guild, central portal and upstairs inn recovery beds.',
      'eastern_threshold':'Beyond Dunmere’s irrigation, dry farms lead to the pumping station. After restoring the works, Ilyan reveals the Aurelian trade road. Ashen Ridge belongs to the later Cinder Crown pursuit.',
      'fields':'Failed crop strips, a dry ditch and empty granary. Investigate all three before reporting to Dunmere.',
      'mill':'Two channel blockages feed the stalled mill. Its east door leads below; ordinary trails allow retreat.',
      'cellar':'The mill’s underground pump chamber. Its Overseer seals the doors during combat; victory opens a field hatch.'}.get(key)


def environment(room):
    import adventure
    here=room['adventure']['current']
    if here=='cellar':return [dict(id='pump-wall-'+str(i),x=x,y=y,width=w,height=h,material='stone',blocksShots=True) for i,(x,y,w,h) in enumerate([(260,100,65,120),(260,330,65,130),(680,100,60,100),(680,350,60,100)])]
    if here in __import__('pumping_works').OUTDOORS:return __import__('pumping_works').barriers(room)
    boxes={'brook':[(295,205,120,65,'water')],'mill_trail':[(540,120,60,50,'wood')],
      'eastern_threshold':[(600,140,120,65,'wood')],'watch':[(500,150,48,55,'stone')],'network':[(430,210,30,60,'stone')]}.get(here,[])
    for spec in SHRINES.values():
        if spec['area']==here:boxes=[*boxes,(spec['x']-16,spec['y']-6,32,20,'stone')]
    w,h=room.get('areaSize',adventure.LARGE_AREAS.get(here,(960,540)))
    return [dict(id=here+'-landmark-'+str(i),x=x*w/960,y=y*h/540,width=bw*w/960,height=bh*h/540,material=material,blocksShots=material!='water') for i,(x,y,bw,bh,material) in enumerate(boxes)]


def enter_hub(room,hub):
    import town_layout
    a=room['adventure'];states=a.setdefault('hubStates',{})
    old=room.get('_currentHub')
    if old in HUBS:states[old]=dict(innRooms=copy.deepcopy(room['innRooms']))
    if old==hub:return
    seed=(a['seed']+(104729 if hub=='dunmere' else sum((i+1)*ord(c) for i,c in enumerate(hub))*7919 if hub!='home' else 0))%(2**31)
    if hub!='home' or old is not None:room.update(town_layout.generate(seed))
    room['townInstance']='adventure-'+hub+'-'+str(seed)
    if hub not in states:
        import progression
        states[hub]=dict(innRooms=copy.deepcopy(room['innRooms']) if hub=='home' and old is None else progression.rooms())
    room['innRooms']=copy.deepcopy(states[hub]['innRooms']);room['_currentHub']=hub
    room['town']=HUBS[hub]
    if hub=='dunmere':room['townPaths']=[p for p in room['townPaths'] if p!=[[480,540],[480,500]]]
    room['hubExitPoints']=hub_exits(room,seed) if hub!='home' else {}


def hub_exits(room,seed):
    """Select and draw real edge approaches around the existing village solids.

    Do not move houses or loosen collision to accommodate a new fixed marker.
    Candidate positions include both the marker and its 60px arrival approach.
    Every road uses the same full-width routing as existing village services.
    """
    import town_layout
    houses=room['townLayout'];result={};rng=random.Random(seed+8191)
    import adventure
    edges=sorted({edge for _,edge,_ in adventure.AREAS[room.get('adventure',{}).get('current','dunmere')]['exits']})
    for edge in edges:
        vertical=edge in ('east','west')
        values=sorted(range(60,481 if vertical else 901,10),key=lambda v:(abs(v-(270 if vertical else 480)),v))
        for value in values:
            marker={'east':(912,value),'west':(48,value),'north':(value,48),'south':(value,492)}[edge]
            arrival={'east':(852,value),'west':(108,value),'north':(value,108),'south':(value,432)}[edge]
            goal={'east':(930,value),'west':(30,value),'north':(value,30),'south':(value,510)}[edge]
            if not all(town_layout.clear(houses,*p,town_layout.ROAD_MARGIN) for p in (marker,arrival,goal)):continue
            try:path,_=town_layout._route(houses,(480,500),goal,rng)
            except ValueError:continue # This candidate has no full-width route.
            path.append({'east':[960,value],'west':[0,value],'north':[value,0],'south':[value,540]}[edge])
            room['townPaths'].append(path);result[edge]=value;break
        else:raise ValueError('Dunmere has no accessible '+edge+' approach; layout preserved for investigation.')
    return result


def shrine_state(room):
    s=room['adventure'].setdefault('travelShrines',dict(version=1,active=[]))
    if s.get('version')!=1:raise ValueError('Unsupported travel shrine state.')
    return s


def interact(world,room,p,point):
    import adventure,chapter_flow,progression,magic_runes
    key=point['id'];here=room['adventure']['current'];state=ensure(room)
    if key.startswith('attune_'):
        shrine=key.removeprefix('attune_');spec=SHRINES[shrine]
        if any(e.get('group','').startswith(spec['guards']) for e in room['enemies']):raise ValueError(spec['description'])
        if shrine=='watch' and 'watch_register' not in chapter_flow.ensure(room)['evidence']:raise ValueError('Read the burned watch register before attuning this stone.')
        active=shrine_state(room)['active']
        if shrine not in active:active.append(shrine);adventure.announce(world,room,spec['name']+' activated. This destination is permanently open to the party.')
        earned=magic_runes.claim(p,'shrine:'+shrine)
        if earned:adventure.announce(world,room,p['name']+' attuned '+spec['name']+' · +1 personal Magic Rune. Other hunters can claim their own attunement.')
        if not earned:p['portalMenu']=time.monotonic()
        adventure.save(world,room);return True
    if key=='dry_spring':
        earned=magic_runes.claim(p,'cache:dry_spring')
        if 'dry_spring_found' not in room['adventure']['claimed']:room['adventure']['claimed'].append('dry_spring_found')
        progression.inspect(p,'Hidden spring casket','A surveyor hid a single Magic Rune above the dry spring. '+('Your personal rune is added to progression; it does not use pouch space.' if earned else 'You already claimed your rune. Other characters may still claim theirs.'))
        adventure.save(world,room);return True
    if key=='ridge_barrier':
        progression.inspect(p,'Beyond the eastern threshold','South: upper irrigation, farmstead and pumping station. Restore the intake and speak to Ilyan in Dunmere to follow the city trade road east from the station. Ashen Ridge is the Cinder Crown’s foothills, reached after the city and Verdant Veil.');return True
    if key=='east_landmark':
        adventure.reward(world,room,'discovery:east_landmark',0)
        progression.inspect(p,'The last irrigated farm','Green grass clings to the mill water. Farther east, straw fields end in cracked channels and thorn hedges. A marker names the pumping works, Aurelian trade road and distant Ashen Ridge. The repaired intake will let a messenger reopen the city route.')
        adventure.save(world,room);return True
    if key=='stranded_workers':
        progression.inspect(p,'Stranded timber workers','The grain road failed before the dragon came. We sheltered here when creatures fled the deep woods. There is a hollow to the east, and a burned watch farther south.','npc')
        p['dialogue']['portrait']='Villager03';return True
    if key=='cellar_begin':begin_cellar(world,room);adventure.save(world,room);return True
    if key not in TEXT and key not in ('channel_west','channel_east','sluice_open'):return False
    if key in ('channel_west','channel_east','sluice_open'):
        chapter_flow.require(room,'irrigation')
        if any(e.get('group','').startswith('mill-approach') for e in room['enemies']):raise ValueError('Clear the mill approach before working on the channels.')
        if key=='sluice_open' and not all(k in chapter_flow.ensure(room)['evidence'] for k in ('channel_west','channel_east')):raise ValueError('Clear both named channel blockages before operating the sluice.')
    chapter_flow.evidence(room,key)
    text=TEXT.get(key,'The '+key.replace('_',' ')+' is restored. The working strip now receives water.' if key=='sluice_open' else 'The channel blockage is removed; report the working irrigation route after opening both channels and the sluice.')
    progression.inspect(p,point['name'],text)
    if key=='sluice_open':adventure.announce(world,room,'Irrigation restored: water reaches one field strip. Return to Dunmere for the next assignment.')
    adventure.save(world,room);return True


def begin_cellar(world,room):
    import chapter_flow
    from game import AFFINITIES,DIFFICULTIES
    chapter_flow.require(room,'mill_cellar')
    if any(not e.get('boss') for e in room['enemies']):raise ValueError('Clear the cellar approach before opening the pump chamber.')
    state=ensure(room)
    if state['cellarComplete']:return
    n=max(1,len(world._active_players(room)));scale=DIFFICULTIES[room['difficulty']]['multiplier']/1.25
    hp=round(420*(1+.55*(n-1))*scale)
    room['enemies']=[dict(id='dunmere-overseer',name='Blighted Overseer',kind='troll',affinity='Nature',color=AFFINITIES['Nature'],baseColor='#8caa70',
        x=570,y=210,hp=hp,maxHp=hp,damage=round(9*scale),speed=65,attackRate=1,boss=True,bossPhase=1,lastAttack=0,stunUntil=0,bleedUntil=0,bleedDamage=0,lastBleedTick=0,nextBossAttack=time.monotonic()+2)]
    state['cellarAttempt']=True;room['adventure']['locked']=True;room.update(encounterType='large_boss',encounterName='Blighted Overseer')
    __import__('adventure').announce(world,room,'The pump chamber seals! Dodge the Overseer’s marked attacks; defeat opens the mill door and outer field hatch.')


def on_kill(room,enemy):
    if enemy['id']!='dunmere-overseer':return False
    import chapter_flow
    ensure(room).update(cellarComplete=True,cellarAttempt=False);room['adventure']['locked']=False
    chapter_flow.evidence(room,'overseer_defeated');return True


def recover(room):
    __import__('campaign_progress').recover(room)
    __import__('pumping_works').recover(room)
    s=ensure(room)
    if s['cellarAttempt'] and not s['cellarComplete']:
        a=room['adventure'];state=a['areas'].get('cellar')
        if state:state['enemies']=[e for e in state['enemies'] if e['id']!='dunmere-overseer']
        if a['current']=='cellar':room['enemies']=[e for e in room.get('enemies',[]) if e['id']!='dunmere-overseer']
        s['cellarAttempt']=False;a['locked']=False


def validate(a):
    s=a.get('regionProgress')
    if s is not None and (not isinstance(s,dict) or set(s)!={'version','cellarComplete','cellarAttempt'} or s.get('version')!=1 or type(s['cellarComplete']) is not bool or type(s['cellarAttempt']) is not bool):raise ValueError('Unsupported region progress.')
    hubs=a.get('hubStates',{})
    if not isinstance(hubs,dict) or set(hubs)-set(HUBS):raise ValueError('Unknown village records.')
    for hub,state in hubs.items():
        if not isinstance(state,dict) or set(state)!={'innRooms'} or not isinstance(state['innRooms'],list) or len(state['innRooms'])!=3:raise ValueError('Invalid village room record.')
        for i,r in enumerate(state['innRooms']):
            if not isinstance(r,dict) or r.get('id')!='guest_'+str(i+1) or r.get('x')!=260+i*220 or r.get('y')!=190 or r.get('doorY')!=330 or type(r.get('locked')) is not bool:raise ValueError('Invalid village bed geometry.')
        if all(r['locked'] for r in state['innRooms']):raise ValueError('Village has no usable recovery bed.')
    shrines=a.get('travelShrines')
    if shrines is not None and (not isinstance(shrines,dict) or set(shrines)!={'version','active'} or shrines.get('version')!=1 or not isinstance(shrines['active'],list) or any(k not in SHRINES for k in shrines['active']) or len(set(shrines['active']))!=len(shrines['active'])):raise ValueError('Unsupported travel shrine records.')


def dungeon_view(room):
    a=room['adventure'];s=ensure(room)
    if 'cellar' not in a['discovered']:return []
    return [dict(id='mill_cellar',name='Dunmere mill cellar',type='underground',danger=7,complete=s['cellarComplete'],routeOpen=s['cellarComplete'],
      description='Ordinary retreat is open. Opening the pump chamber seals the fight; defeating the Overseer opens the far field hatch. Unfinished attempts restart at full strength after recovery.',
      entrances=['mill']+(['fields'] if s['cellarComplete'] else []),
      nodes=[dict(id='cellar',name='Pump chamber',position=[1,1],visited='cellar' in a['visited'],current=a['current']=='cellar',cleared=s['cellarComplete'])],links=[],
      treasure=int('additive_ledger' in __import__('chapter_flow').ensure(room)['evidence']),floors=[],current=a['current']=='cellar',wave=0,waves=0,breakLeft=0,
      objective='Pump chamber cleared · field hatch open.' if s['cellarComplete'] else 'Defeat the Overseer.' if a.get('locked') and a['current']=='cellar' else 'Clear the approach, then open the pump chamber.')]
