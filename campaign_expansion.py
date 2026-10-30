"""Authored region gameplay adapter, independent of Gauntlet campaign schedules.

Internal scenery/actor presentation reuses existing families until the sprite
chat exports the manifest's art. No new image is silently declared finished.
"""
import copy
import math
import random
import time
import campaign_content as content
import campaign_progress as progress

PACKS={
 'city_approach':[('refugee-raiders',280,260,['knife_raider','bow_poacher']),('road-saboteurs',700,370,['shield_bruiser','fire_saboteur'])],
 'city_gate':[('breach-approach',420,180,['knife_raider','shield_bruiser'])],
 'city_homes':[('homes-raiders',360,240,['shield_bruiser','bow_poacher']),('homes-alley',740,360,['knife_raider'])],
 'city_archive':[('archive-patrol',670,300,['fire_saboteur','militia_archer'])],
 'city_square':[('square-patrol',300,350,['militia_guard','militia_archer']),('orders-guard',650,180,['militia_officer','militia_guard'])],
 'city_barracks':[('frontage',500,230,['militia_guard','militia_archer','militia_officer'])],
 'city_observatory':[('observatory-entry',420,300,['militia_guard','militia_mage'])],
 'veil_threshold':[('threshold-stalkers',480,200,['essence_stalker','veil_scout_hostile'])],
 'veil_glades':[('glade-thorns',350,290,['thorn_guardian','veil_scout_hostile']),('glade-scouts',750,340,['veil_scout_hostile'])],
 'veil_pools':[('pool-drain',400,250,['siphon_construct','siphon_apprentice']),('pool-bank',740,390,['essence_stalker'])],
 'veil_grove':[('grove-fracture',680,220,['thorn_guardian','siphon_apprentice'])],
 'veil_sanctuary':[('sanctuary-roots',460,250,['thorn_guardian','essence_stalker'])],
 'veil_siphon_west':[('west-apprentices',460,220,['siphon_apprentice','siphon_construct'])],
 'veil_siphon_east':[('east-apprentices',610,260,['siphon_apprentice','veil_scout_hostile','essence_stalker'])],
 'veil_sanctum':[('sanctum-entry',400,210,['siphon_apprentice','thorn_guardian'])],
 'cinder_foothills':[('ridge-sentries',650,260,['ash_draco','cinder_serpent'])],
 'cinder_lava_road':[('lava-road',370,200,['basalt_guardian','cinder_serpent']),('road-vents',740,370,['vent_stalker','ash_draco'])],
 'cinder_ravine':[('ravine-front',620,200,['basalt_guardian','ash_draco'])],
 'cinder_slopes':[('slope-creatures',330,200,['ash_draco','cinder_serpent']),('high-rocks',720,390,['basalt_guardian','vent_stalker'])],
 'cinder_vent':[('vent-pack',420,250,['vent_stalker','cinder_serpent','ash_draco'])],
 'cinder_upper':[('upper-pack',710,210,['ash_draco','basalt_guardian'])],
}
LAYOUTS={
 'road':[(410,110,130,65),(620,370,130,55)],'gate':[(250,130,65,115),(650,350,65,100)],
 'courtyard':[(220,90,140,60),(650,370,100,55)],'lanes':[(310,140,65,115),(610,340,65,110)],
 'frontage':[(280,130,85,60),(650,350,85,60)],'pillars':[(280,160,50,55),(650,160,50,55),(280,340,50,55),(650,340,50,55)],
 'terrace':[(250,130,60,75),(650,130,60,75)],'grove':[(290,130,85,65),(670,350,80,65)],
 'pools':[(260,120,170,65),(580,360,150,60)],'lair':[(210,140,65,65),(680,360,65,65)],'hub':[]}

def install(adventure):
    import region_content,magic_runes,hero_skills
    from campaign_equipment import ITEMS
    for key,a in content.AREAS.items():
        spec=dict(name=a['name'],pos=a['position'][:],danger=a['danger'],region='ruins' if a['region']=='aurelian' else 'woodland' if a['region']=='verdant' else 'cavern',exits=[tuple(e) for e in a['exits']])
        adventure.AREAS[key]=spec;adventure.LARGE_AREAS[key]=tuple(a['size'])
        # Ordinary outdoor generations remain explicitly governed by existing
        # eligibility. Unique attempts never belong to this ordinary registry.
    source='pump_exterior';edge=('city_approach','east','west')
    if edge not in adventure.AREAS[source]['exits']:adventure.AREAS[source]['exits'].append(edge)
    adventure.EXIT_OFFSETS[('pump_exterior','city_approach')]=.70
    region_content.HUBS.update({k:t['name'] for k,t in content.TOWNS.items() if k not in ('home','dunmere')})
    for key,q in content.QUESTS.items():
        if q['reward']['magicRunes']:magic_runes.SOURCES['campaign:'+key]=q['reward']['magicRunes']
        if q['reward']['skillPoints']:hero_skills.MILESTONES['campaign:'+key]=q['reward']['skillPoints']
    for key,c in content.CHECKPOINTS.items():hero_skills.MILESTONES['sanctuary:'+key]=c['skillPoints']

def enemy(world,room,key,identity,x,y,*,boss=False,group=None,area=None):
    from game import AFFINITIES,DIFFICULTIES
    spec=content.ENEMIES[key];n=max(1,len(world._active_players(room)));danger=content.AREAS.get(area or room['adventure']['current'],{}).get('danger',9)
    scale=DIFFICULTIES[room['difficulty']]['multiplier']/1.25
    hp=round(((610+danger*22) if boss else (42+danger*7))*(1+(.5 if boss else .18)*(n-1))*scale)
    element=spec['affinity'];element='Nature' if element=='Stone' else element
    return dict(id=identity,archetype=key,name=spec['name'],kind=spec['kind'],**{'class':{'ranged':'Archer','channeler':'Wizard','support':'Healer','flanker':'Rogue','ambusher':'Rogue','draco':'Wizard'}.get(spec['role'],'Knight')},
        combatRole=spec['role'],affinity=element,color=AFFINITIES.get(element,'#d1b979'),baseColor='#8f7970',
        x=x,y=y,homeX=x,homeY=y,hp=hp,maxHp=hp,damage=round((10 if boss else 5+danger*.4)*scale),
        speed=100 if boss else 82 if spec['role']=='defender' else 100,attackRate=1,boss=boss,bossPhase=1,bodyRadius=48 if key=='cinder_dragon' else 20 if boss else 12,
        group=group or identity,aggroRadius=180,leashRadius=285,lastAttack=0,stunUntil=0,bleedUntil=0,bleedDamage=0,lastBleedTick=0,nextBossAttack=time.monotonic()+2)

def build(world,room,area):
    if area not in content.AREAS:return None
    import adventure
    a=content.AREAS[area];w,h=a['size'];barriers=[]
    for i,(x,y,bw,bh) in enumerate(LAYOUTS[a['arrangement']]):
        barriers.append(dict(id=area+'-solid-'+str(i),x=x*w/960,y=y*h/540,width=bw*w/960,height=bh*h/540,
            material='water' if a['arrangement']=='pools' else 'stone',blocksShots=True))
    env=dict(stage=a['danger'] or 1,region='ruins' if a['region']=='aurelian' else 'woodland' if a['region']=='verdant' else 'cavern',obstacles=[],zones=[],barriers=barriers)
    result=dict(size=[w,h],enemies=[],environment=env,encounterLayout=adventure.ENCOUNTER_LAYOUT,defeated=[],entered=True,details=[0]*6)
    rng=random.Random(room['adventure']['seed']+sum(map(ord,area))*7919)
    n=max(1,len(world._active_players(room)))
    for i,(group,x,y,kinds) in enumerate(PACKS.get(area,[])):
        choices=kinds+([kinds[0]] if n>=3 else [])
        positions=adventure.group_positions(area,[w,h],env,x,y,len(choices),rng)
        for j,(kind,point) in enumerate(zip(choices,positions)):
            result['enemies'].append(enemy(world,room,kind,area+'-'+group+'-'+str(j),*point,group=group,area=area))
    for key,spec in content.SIPHON_FOCI.items():
        if spec['area']==area:
            x,y=spec['position'][0]*w/960,spec['position'][1]*h/540;hp=round(55*(1+.2*(n-1)))
            result['enemies'].append(dict(id='focus-'+key,name='Siphon focus',kind='troll',structure=True,affinity='Arcane',color='#b3a1d5',baseColor='#b3a1d5',x=x,y=y,hp=hp,maxHp=hp,damage=0,speed=0,attackRate=1,boss=False,group='siphon-foci'))
    result['enemies']=adventure.clean_enemies(result['enemies'])
    return result

def closed(room,source,target):
    s=progress.ensure(room)
    if target=='city_approach' and source not in content.AREAS and not progress.finished(room,'city_call'):return 'Report the pumping works, then speak to Ilyan in Dunmere and read the city dispatch.'
    if target=='city_square' and source=='city_gate' and 'city_breach' not in s['facts']:return 'Secure the breach at the assault marker. The protected merchant refuge lies south; speak to Rhea there before committing.'
    if target in ('city_barracks','city_observatory') and not all(progress.finished(room,k) for k in ('city_rescue','city_evacuation','city_gate_repair','city_infirmary')):return 'Secure the civilian routes and critical defenses; report to Marshal Rhea before confronting the commanders.'
    if target=='city_terrace' and not progress.finished(room,'city_commanders'):return 'The three militia commanders control the upper city. Recover their orders, defeat each commander and report.'
    if target=='veil_threshold' and not progress.finished(room,'city_terrace'):return 'Report the dragon’s departure at the refuge before following the forest disturbance.'
    if target=='veil_sanctum' and not progress.finished(room,'veil_siphons'):return 'Disable both siphons, recover their extraction records and report to Arven.'
    if target=='cinder_foothills' and source!='cinder_lava_road' and not progress.finished(room,'veil_archmage'):return 'Defeat Orath and report the broken bond before pursuing the still-dangerous dragon.'
    if target=='cinder_upper' and source=='cinder_vent' and 'boss:ravine_keeper' not in s['facts']:return 'The Ravine Keeper controls the upper passage. Defeat it at its marked challenge before ascending.'
    if target=='cinder_antechamber' and 'boss:summit_warden' not in s['facts']:return 'The Summit Warden still controls the final approach.'
    if target=='cinder_lair' and not all(k in s['sanctuaries'] for k in ('cinder_entry','cinder_shelter','cinder_upper','cinder_last')):return 'Activate the four ascent sanctuaries before committing; they provide viable recovery and skill management.'
    if target=='cinder_lair' and 'cinder_lair_seal' not in s['facts']:return 'Recover the cracked lair ward in the vent passage; it identifies a safe way through this threshold.'
    return None

def features(room):
    import adventure,campaign_quests
    a=room['adventure'];here=a['current'];s=progress.ensure(room);result=[]
    def add(key,name,x,y,kind='clue',**fields):
        if here in __import__('region_content').HUBS:x,y=campaign_quests.npc_position(room,'object:'+key,x,y)
        else:x,y=adventure.point(room,x,y)
        result.append(dict(id=key,name=name,x=x,y=y,kind=kind,**fields))
    for i,(key,spec) in enumerate(content.NPCS.items()):
        if spec['area']!=here:continue
        if key=='city_messenger' and not progress.finished(room,'pumping_finale'):continue
        x,y=campaign_quests.npc_position(room,key,350+(i%3)*105,300+(i//3%2)*70)
        result.append(dict(id=key,name=spec['name'],x=x,y=y,kind='talk',portrait='Villager0'+str(2+i%6)))
    for i,(key,(area,name)) in enumerate((k,v) for k,v in content.OBJECTS.items() if v[0]==here):
        if key not in s['facts']:add(key,'Recover '+name,400+i*100,440,'clue')
    for key,spec in content.RESCUES.items():
        if spec['area']==here and 'rescue:'+key not in s['facts']:add('rescue:'+key,'Help '+spec['name'],*spec['position'],'hunter')
    for key,spec in content.REPAIRS.items():
        if spec['area']==here and 'repair:'+key not in s['facts']:add('repair:'+key,'Repair '+key.replace('_',' '),*spec['position'],'mechanism')
    for key,spec in content.DEFENSES.items():
        if spec['area']==here and 'defense:'+key not in s['facts'] and (s['attempt'] or {}).get('id')!=key:add('defense:'+key,'Begin '+spec['name']+' · exits seal',480,420,'mechanism')
    for key,area in progress.BOSSES.items():
        if area==here and 'boss:'+key not in s['facts'] and (s['attempt'] or {}).get('id')!=key:add('boss:'+key,'Challenge '+(content.ENEMIES[key]['name'] if key in content.ENEMIES else 'the breach captain')+' · exits seal',480,390,'boss')
    for key,spec in content.CHECKPOINTS.items():
        if spec['area']==here:add('sanctuary:'+key,'Sanctuary · '+('choose recovery' if key in s['sanctuaries'] else 'activate recovery and supplies'),*spec['position'],'travel_shrine')
    for key in progress.MECHANISMS:
        if key==here and 'mechanism:'+key not in s['facts']:add('mechanism:'+key,'Disable '+key.replace('_',' '),480,350,'mechanism')
    for key,spec in content.SIPHON_FEEDS.items():
        if spec['area']==here and key not in s['facts']:add(key,spec['name'],*spec['position'],'mechanism')
    for i,(key,spec) in enumerate(content.RESCUES.items()):
        hub='city_refuge' if key in ('nara','olen','city_brother') else 'dunmere' if key=='dunmere_carrier' else 'veil_haven'
        if here==hub and 'rescue:'+key in s['facts']:add('muster:'+key,spec['name']+' · safe',160+(i%3)*90,390+(i//3)*30,'talk',portrait='Villager04')
    if here=='city_terrace' and 'cinematic:city_dragon' not in s['facts']:add('cinematic:city_dragon','Inspect the upper beacon',480,300,'mechanism')
    if here=='cinder_foothills' and progress.status(room,'cinder_dragon')=='offered':add('cinder_assignment','Pursue the dragon · begin final assignment',320,350,'clue')
    return result

def objective_location(fact):
    if fact in content.OBJECTS:return content.OBJECTS[fact][0]
    kind,_,key=fact.partition(':')
    return (content.RESCUES.get(key,{}).get('area') if kind=='rescue' else content.REPAIRS.get(key,{}).get('area') if kind=='repair' else content.DEFENSES.get(key,{}).get('area') if kind=='defense' else progress.BOSSES.get(key) if kind=='boss' else key if kind=='mechanism' else 'city_terrace' if kind=='cinematic' else 'veil_sanctum' if fact=='bond_broken' else 'cinder_lair' if kind=='ending' else 'city_gate')

def instruction(fact):
    if fact in content.OBJECTS:return 'Recover '+content.OBJECTS[fact][1]+'.'
    kind,_,key=fact.partition(':')
    if kind=='rescue':return 'Secure the nearby threat and help '+content.RESCUES[key]['name']+'.'
    if kind=='repair':return 'Use the recovered supplies to repair '+key.replace('_',' ')+'.'
    if kind=='defense':return 'Gather at '+content.DEFENSES[key]['name']+' and protect it through the finite assault.'
    if kind=='boss':return 'Challenge and defeat '+content.ENEMIES[key]['name']+'.'
    if kind=='mechanism':return 'Recover the extraction records, close both marked feeds and disable the western siphon.' if key.endswith('west') else 'Destroy the two siphon foci, secure the mechanism and disable the eastern siphon.'
    return {'city_breach':'Clear the breached gate approach, then challenge its assault captain.',
            'cinematic:city_dragon':'Inspect the upper beacon after reporting the commanders.',
            'bond_broken':'Break Orath’s siphon foci and defeat him to disrupt the dragon bond.',
            'ending:campaign':'Defeat the dragon and preserve your completed campaign.'}.get(fact,'Follow the known route.')

def menu(room,p):
    import progression
    result=[];points=None;s=progress.ensure(room)
    for key,q in content.QUESTS.items():
        status=progress.status(room,key)
        if status=='unavailable':continue
        if points is None:points=features(room)
        actionable=room['adventure']['current']==q['hub'] and any(f['id']==q['contact'] and math.dist((p['x'],p['y']),(f['x'],f['y']))<=78 for f in points)
        result.append(dict(id=key,title=q['title'],hub=q['hub'],objective=' '.join(instruction(f) for f in q['requires']),requires=q['requires'],
          status=status,outcome=content.OUTCOMES.get(key,'Completed · '+q['title']+'. Its supplies, people or repaired site remain safe.') if status=='complete' else None,
          found=[f for f in q['requires'] if f in s['facts']],contact=content.NPCS.get(q['contact'],{}).get('name','Foothill pursuit marker'),actionable=actionable,optional=q['optional']))
    return result

def cinder_step(room):
    s=progress.ensure(room)
    for kind,key,text in (
        ('camp','cinder_entry','Activate the foothill sanctuary. It supplies recovery and safe skill management.'),
        ('camp','cinder_shelter','Reach and activate the sheltered ravine sanctuary.'),
        ('boss','ravine_keeper','Defeat the Ravine Keeper to open the upper ascent.'),
        ('camp','cinder_upper','Activate the upper approach sanctuary before continuing.'),
        ('boss','summit_warden','Defeat the Summit Warden to open the antechamber.'),
        ('artifact','cinder_lair_seal','Recover the cracked lair ward in the interior vent.'),
        ('camp','cinder_last','Activate the last sanctuary before committing to the dragon.'),
        ('boss','cinder_dragon','Gather in the lair and challenge the Crownfire Dragon. The encounter seals its exits.')):
        if kind=='camp' and key not in s['sanctuaries']:return content.CHECKPOINTS[key]['area'],text
        if kind=='boss' and 'boss:'+key not in s['facts']:return progress.BOSSES[key],text
        if kind=='artifact' and key not in s['facts']:return content.OBJECTS[key][0],text
    return 'cinder_lair','The dragon is defeated. Your completed campaign remains available for exploration.'

def tracking(room,p):
    if not progress.finished(room,'pumping_finale'):return None
    import campaign_guidance
    s=progress.ensure(room);key=p.get('trackedObjective')
    if key not in content.QUESTS or progress.status(room,key) in ('complete','unavailable'):
        key=next((k for k,q in content.QUESTS.items() if not q['optional'] and progress.status(room,k) not in ('complete','unavailable')),None)
    if key is None:
        return dict(id='campaign_complete',title='The Dragon’s Reign Is Ended',area='cinder_lair',complete=True,nextExit=None,nextStep='The five-region campaign is complete. Revisit settlements, finish optional stories or export your completed save.')
    q=content.QUESTS[key];state=progress.status(room,key);missing=next((f for f in q['requires'] if f not in s['facts']),None)
    target=q['hub'] if state in ('offered','ready-to-turn-in') else objective_location(missing)
    known=target in room['adventure']['discovered'];path=campaign_guidance.route(room,room['adventure']['current'],target,known_only=False)
    text=('Speak to '+content.NPCS.get(q['contact'],{}).get('name','the ascent marker')+' to '+('accept.' if state=='offered' else 'report.')) if state in ('offered','ready-to-turn-in') else instruction(missing)
    if key=='cinder_dragon':
        target,text=(q['hub'],'Inspect the foothill pursuit marker to begin the final ascent.') if state=='offered' else cinder_step(room)
        known=target in room['adventure']['discovered'];path=campaign_guidance.route(room,room['adventure']['current'],target,known_only=False)
    return dict(id=key,title=q['title'],area=target if known else None,complete=False,nextExit=path[0] if path else None,nextStep=text,status=state,optional=q['optional'])

def interact(world,room,p,point):
    import progression,adventure
    key=point['id'];s=progress.ensure(room)
    if key.startswith('muster:') and key.removeprefix('muster:') in content.RESCUES:
        progression.inspect(p,point['name'],'I reached the protected muster point. You can finish other work without escorting me again. Thank you for coming back.','npc');return True
    if key in content.NPCS:
        spec=content.NPCS[key];progression.start_dialogue(p,'adventure_contact')
        text=('The restored intake lets the grain road reopen. This sealed dispatch names Aurelian: a city under attack. Accept the assignment, recover this dispatch, then report it; the road leaves the pumping station to the east.' if key=='city_messenger' else
              'We need practical help. Journal lists our current assignments; each names its fixed evidence and next destination. Named rescues reach safe muster points without long escorts. Defenses seal exits only after your party commits.')
        if key=='veil_scholar' and progress.finished(room,'veil_archmage'):text='Orath commanded the dragon through the old seals. Breaking his bond freed it from orders, not its appetite for destruction. It fled to the Cinder Crown. The roots heal slowly; finish the pursuit before it returns.'
        rows=menu(room,p)
        actions=[action for action,status in [('accept','offered'),('report','ready-to-turn-in')] if any(q['status']==status and q['actionable'] for q in rows)]
        p['dialogue'].update(campaignContact=True,contactId=key,contactTitle=spec['name'],contactPortrait=point.get('portrait','Villager02'),baseReaction=text,reaction=text,settlementChoices=[],serviceChoices=[],runnerActions=actions)
        return True
    if key in content.OBJECTS:progress.retrieve(world,room,p,key);progression.inspect(p,point['name'],content.ARTIFACT_TEXT.get(key,'Recovered for its named settlement request.')+' Recorded outside pouch storage; early discoveries count when the assignment is accepted.');return True
    kind,_,name=key.partition(':')
    if kind=='rescue' and name in content.RESCUES:progress.rescue(world,room,p,name);return True
    if kind=='repair' and name in content.REPAIRS:progress.repair(world,room,p,name);return True
    if kind in ('defense','boss') and (name in content.DEFENSES or name in progress.BOSSES):progress.start_attempt(world,room,p,name);return True
    if kind=='sanctuary' and name in content.CHECKPOINTS:progress.checkpoint(world,room,p,name);return True
    if kind=='mechanism' and name in progress.MECHANISMS:
        if name=='veil_siphon_west' and not {'veil_siphon_records',*content.SIPHON_FEEDS}<=set(s['facts']):raise ValueError('Read the extraction records and close both marked feeds before isolating this siphon.')
        if name=='veil_siphon_east' and not set(content.SIPHON_FOCI)<=set(s['facts']):raise ValueError('Destroy the two visible siphon foci first. Ordinary retreat remains open.')
        if any(math.dist((point['x'],point['y']),(e['x'],e['y']))<180 for e in room['enemies']):raise ValueError('Secure the immediate mechanism before disabling this siphon.')
        progress.atomic(world,room,lambda:progress.fact(room,key));adventure.announce(world,room,'Siphon disabled · a local root stream begins to recover.');return True
    if key in content.SIPHON_FEEDS:
        if any(math.dist((p['x'],p['y']),(e['x'],e['y']))<160 for e in room['enemies']):raise ValueError('Clear or evade nearby threats before closing the feed.')
        progress.atomic(world,room,lambda:progress.fact(room,key));return True
    if key=='cinematic:city_dragon':begin_cinematic(world,room,p);return True
    if key=='cinder_assignment':
        if progress.status(room,'cinder_dragon')=='offered':progress.atomic(world,room,lambda:progress.ensure(room)['accepted'].append('cinder_dragon'))
        return True
    return False

def entered(world,room):
    import adventure
    area=room['adventure']['current']
    if area in content.AREAS:
        adventure.reveal(room,*(other for other,_,_ in adventure.AREAS[area]['exits'] if not closed(room,area,other)))
        if area=='city_approach':adventure.announce(world,room,'Aurelian approach: bandits block the gate. Beyond its ordinary approach, the protected merchant refuge lies south. Speak to Rhea there before challenging the breach captain.')
        if area in ('city_refuge','veil_haven'):
            prefix='city_' if area=='city_refuge' else 'veil_'
            for p in room['players'].values():
                stock=p.setdefault('shopStock',[]);known={i['key'] for i in stock}
                for key in __import__('campaign_equipment').ITEMS:
                    if key=='city_duelist_edge' and 'repair:city_workshop' not in progress.ensure(room)['facts']:continue
                    if key.startswith(prefix) and key not in known and len(stock)<30:stock.append(world._make_item(key))
    if area=='dunmere' and progress.finished(room,'pumping_finale') and not progress.finished(room,'city_call'):adventure.announce(world,room,'Ilyan has a sealed dispatch from Aurelian. The city’s distress continues the repaired trade road.')

def spawn_attempt(world,room):
    import adventure
    s=progress.ensure(room);a=s['attempt'];key=a['id'];wave=a['wave'];runtime=room['_campaignAttempt']
    if key in content.DEFENSES:
        spec=content.DEFENSES[key];kinds=spec['waves'][wave-1];n=max(1,len(world._active_players(room)))
        choices=kinds+([kinds[0]] if n>=2 else [])+([kinds[-1]] if n>=4 else [])
        if not room.get('_campaignWard'):
            x,y=adventure.point(room,*spec['position']);hp=round(spec['health']*(1+.25*(n-1)))
            room['_campaignWard']=dict(id='campaign-objective',campaignObjective=True,name=spec['name'],x=x,y=y,hp=hp,maxHp=hp,status='alive',connected=True)
        positions=[adventure.point(room,x,y+offset) for x,y in spec['spawns'] for offset in (0,50)]
        actors=world._active_players(room)+progress.targets(room)
        import combat_environment as terrain
        for i,kind in enumerate(choices):
            candidates=[p for p in positions if terrain.walkable(room,*p) and all(math.dist(p,(actor['x'],actor['y']))>=120 for actor in actors)]
            if not candidates:raise ValueError('No safe authored defense spawn; encounter remains pending.')
            x,y=max(candidates,key=lambda p:min(math.dist(p,(actor['x'],actor['y'])) for actor in actors))
            positions.remove((x,y));room['enemies'].append(enemy(world,room,kind,'exp-'+key+'-'+str(wave)+'-'+str(i),x,y))
    else:
        kind='breach_captain' if key=='city_breach' else key
        x,y=adventure.point(room,610,210);boss=enemy(world,room,kind,'exp-'+key,x,y,boss=True)
        if key in ('city_mage','veil_archmage'):boss['campaignChanneler']=True
        room['enemies'].append(boss)
        guards=['militia_guard'] if key in ('city_mage','city_archer') else ['siphon_apprentice'] if key=='veil_archmage' else []
        for i,guard in enumerate(guards):
            x,y=adventure.point(room,350+i*250,180);room['enemies'].append(enemy(world,room,guard,'exp-'+key+'-guard'+str(i),x,y))
    runtime['spawned']=True;adventure.announce(world,room,'Wave '+str(wave)+' / '+str(len(content.DEFENSES[key]['waves']) if key in content.DEFENSES else 1)+' · '+key.replace('_',' ')+'.')

def begin_cinematic(world,room,p):
    if 'cinematic:city_dragon' in progress.ensure(room)['facts']:return
    if not progress.finished(room,'city_commanders'):raise ValueError('Report all three commanders before inspecting the upper beacon.')
    progress.gather(world,room,p)
    if room['enemies']:raise ValueError('Secure the terrace before inspecting the beacon.')
    def commit():
        room['_campaignCinematic']=dict(id='city_dragon',endsAt=time.monotonic()+7)
        room.update(projectiles=[],hazards=[])
        for actor in room['players'].values():actor.update(dx=0,dy=0,attacking=False,reviving=None)
    progress.atomic(world,room,commit)

def finish_cinematic(world,room):
    if not room.get('_campaignCinematic'):return
    def commit():
        progress.fact(room,'cinematic:city_dragon');room.pop('_campaignCinematic',None)
        for p in room['players'].values():p.update(dx=0,dy=0,attacking=False,reviving=None)
        __import__('adventure').announce(world,room,'The dragon shatters the upper beacon and leaves. A militia seal flashes on its collar. The refuge is safe for now; report to Rhea, then follow the disturbance into the Verdant Veil.')
    progress.atomic(world,room,commit)

def tick(world,room,now):
    runtime=room.get('_campaignAttempt')
    if runtime and not runtime['spawned'] and now>=runtime['readyAt']:spawn_attempt(world,room)
    c=room.get('_campaignCinematic')
    if c and now>=c['endsAt']:finish_cinematic(world,room)

def art_outcomes(room):
    """Read existing authored/cache anchors; never allocate an NPC slot or save."""
    import adventure
    a=room['adventure'];s=progress.ensure(room);result=[]
    for key,spec in content.REPAIRS.items():
        if spec['area']!=a['current'] or 'repair:'+key not in s['facts']:continue
        pos=a.get('homeNpcs',{}).get(a['current']+':campaign:object:repair:'+key)
        x,y=pos if pos else adventure.point(room,*spec['position'])
        result.append(dict(id='repair:'+key,x=x,y=y))
    return result

def view(room):
    s=progress.ensure(room);a=s['attempt'];ward=room.get('_campaignWard');c=room.get('_campaignCinematic')
    return dict(region=content.AREAS.get(room['adventure']['current'],{}).get('region'),completed='ending:campaign' in s['facts'],
       artStatus='campaign artwork integrated; coverage ledger in art/campaign-v1',facts=s['facts'][:],reported=s['reported'][:],sanctuaries=s['sanctuaries'][:],outcomes=art_outcomes(room),
       settlementAnchors=[list(v) for k,v in room['adventure'].get('homeNpcs',{}).items() if k.startswith(room['adventure']['current']+':')],
       epilogue=('The dragon’s reign is ended. Oakvale’s road, Dunmere’s safe intake, Aurelian’s refuge and Rootsong’s recovering streams endure. '+
         ('The stranded workers helped rebuild the stores. ' if __import__('campaign_quests').done(room,'fire') else '')+
         ('The seed reserve went to '+room['adventure'].get('chapter',{}).get('choices',{}).get('seeds','the settlements')+'. ')+
         'Continue exploring or export this completed save. There is no automatic new-game reset.') if 'ending:campaign' in s['facts'] else None,
       fields=[dict(x=f['x'],y=f['y'],radius=f['radius'],ownerId=f['ownerId'],abilityId=f.get('abilityId'),mechanic=f['mechanic'],
                    pulsesLeft=f['remaining'],nextPulseIn=max(0,f['nextAt']-time.monotonic())) for f in room.get('campaignFields',[])],
       pulses=[dict(**{k:p[k] for k in ('id','ownerId','abilityId','mechanic','x','y','radius')},age=time.monotonic()-p['at'])
               for p in room.get('_campaignVisualPulses',[]) if p['stage']==room['stage'] and p['area']==room['adventure']['current'] and 0<=time.monotonic()-p['at']<.4],
       anchors=[dict(ownerId=p['id'],x=p['campaignAnchor']['x'],y=p['campaignAnchor']['y'],returnIn=max(0,p['campaignAnchor']['returnAt']-time.monotonic()))
                for p in room['players'].values() if p.get('campaignAnchor') and p['status']=='alive' and p.get('connected',True) and not p.get('townInterior')],
       objective=dict(id=a['id'],name=content.DEFENSES[a['id']]['name'] if a['id'] in content.DEFENSES else content.ENEMIES['breach_captain' if a['id']=='city_breach' else a['id']]['name'],type='defense' if a['id'] in content.DEFENSES else 'boss',wave=a['wave'],waves=len(content.DEFENSES[a['id']]['waves']) if a['id'] in content.DEFENSES else 1,
         ward={k:ward[k] for k in ('name','x','y','hp','maxHp')} if ward else None,
         breakLeft=max(0,math.ceil(room.get('_campaignAttempt',{}).get('readyAt',0)-time.monotonic()))) if a else None,
       cinematic=dict(id=c['id'],remaining=max(0,math.ceil(c['endsAt']-time.monotonic())),text='The dragon’s roar pins you in place. It strikes the upper beacon, then leaves. No damage can occur during this scene.') if c else None)

def next_region(room):
    s=progress.ensure(room)
    if 'ending:campaign' in s['facts']:return None
    if progress.finished(room,'veil_archmage'):return dict(name='The Cinder Crown · Ashen Ridge pursuit',description='The bond is broken, but the dragon remains dangerous. Follow the east sanctum trail to Ashen Ridge. Four ascent sanctuaries provide recovery and safe skill management; this is the final region, with no town assignments.')
    if progress.finished(room,'city_terrace'):return dict(name='The Verdant Veil',description='Follow the magical disturbance east from the upper terrace. Help Rootsong’s residents and investigate the failing essence network.')
    if progress.finished(room,'city_call'):return dict(name='Aurelian City · protect the districts',description='Marshal Rhea coordinates the refuge. Secure the breach, rescue named civilians, hold three critical sites and defeat the three militia commanders. The Journal tracks each current assignment.')
    if progress.finished(room,'pumping_finale'):return dict(name='Aurelian City · sealed dispatch',description='Speak to Ilyan in Dunmere; his dispatch opens the eastern pumping-station trade road. Ashen Ridge belongs to the later Cinder Crown pursuit.')
    return dict(name='Dunmere · pumping works',description='Tovin can trace the additive upstream through the farmstead and branching sluice tunnels.') if room['adventure']['bossComplete'] else None
