"""Five-region authored content contract. Stable IDs are also the sprite handoff.

Gameplay owns these identifiers and footprints; the sprite chat owns appearance.
No asset in this contract is implicitly claimed to be finished or integrated.
"""
import copy

VERSION=1
REGIONS={
 'woodland':dict(order=1,name='Woodland',hub='home',status='existing'),
 'dunmere':dict(order=2,name='Dunmere and the pumping works',hub='dunmere',status='existing'),
 'aurelian':dict(order=3,name='Aurelian City',hub='city_refuge',status='playable-mechanics-prototype'),
 'verdant':dict(order=4,name='The Verdant Veil',hub='veil_haven',status='playable-mechanics-prototype'),
 'cinder':dict(order=5,name='The Cinder Crown',hub=None,status='playable-mechanics-prototype'),
}

# id, name, literal atlas x/y, danger, tactical arrangement (compact coordinates).
AREA_ROWS={
 'aurelian':[
 ('city_approach','Aurelian · refugee approach',5,5,9,'road'),
 ('city_gate','Aurelian · breached gate',6,5,9,'gate'),
 ('city_refuge','Aurelian · merchant refuge',6,6,0,'hub'),
 ('city_homes','Aurelian · residential streets',7,6,9,'courtyard'),
 ('city_archive','Aurelian · archive and infirmary',6,7,10,'lanes'),
 ('city_square','Aurelian · barricaded square',7,5,10,'gate'),
 ('city_barracks','Aurelian · militia barracks',8,5,11,'frontage'),
 ('city_observatory','Aurelian · occupied observatory',8,6,11,'pillars'),
 ('city_terrace','Aurelian · upper terrace',8,7,11,'terrace')],
 'verdant':[
 ('veil_threshold','Veil · forest threshold',9,7,11,'road'),
 ('veil_haven','Veil · Rootsong settlement',10,7,0,'hub'),
 ('veil_glades','Veil · disturbed glades',10,8,11,'grove'),
 ('veil_pools','Veil · fading essence pools',11,8,12,'pools'),
 ('veil_grove','Veil · the ancient grove',11,7,12,'grove'),
 ('veil_sanctuary','Veil · abandoned sanctuary',10,9,12,'pillars'),
 ('veil_siphon_west','Veil · western siphon',11,9,13,'lanes'),
 ('veil_siphon_east','Veil · eastern siphon',12,8,13,'frontage'),
 ('veil_sanctum','Veil · siphoning sanctum',12,9,14,'pillars')],
 'cinder':[
 ('cinder_foothills','Ashen Ridge · Cinder foothills',13,9,14,'road'),
 ('cinder_lava_road','Cinder · broken lava road',14,9,14,'lanes'),
 ('cinder_ravine','Cinder · basalt ravine',14,10,15,'pillars'),
 ('cinder_slopes','Cinder · high slopes',15,10,15,'frontage'),
 ('cinder_vent','Cinder · vent passage',15,9,16,'lanes'),
 ('cinder_upper','Cinder · upper approach',16,9,16,'road'),
 ('cinder_antechamber','Cinder · dragon antechamber',16,10,16,'terrace'),
 ('cinder_lair','Cinder Crown · the final lair',17,10,17,'lair')],
}

# source, destination, outward edge. Reverse is always the opposite edge.
CONNECTIONS=[
 ('pump_exterior','city_approach','east'),('city_approach','city_gate','east'),
 ('city_gate','city_refuge','south'),('city_gate','city_square','east'),
 ('city_refuge','city_homes','east'),('city_refuge','city_archive','south'),
 ('city_homes','city_square','north'),('city_homes','city_observatory','east'),
 ('city_square','city_barracks','east'),('city_barracks','city_observatory','south'),
 ('city_archive','city_terrace','east'),('city_observatory','city_terrace','south'),
 ('city_terrace','veil_threshold','east'),('veil_threshold','veil_haven','east'),
 ('veil_haven','veil_glades','south'),('veil_haven','veil_grove','east'),
 ('veil_glades','veil_pools','east'),('veil_glades','veil_sanctuary','south'),
 ('veil_pools','veil_grove','north'),('veil_pools','veil_siphon_east','east'),
 ('veil_sanctuary','veil_siphon_west','east'),('veil_siphon_west','veil_sanctum','east'),
 ('veil_siphon_east','veil_sanctum','south'),('veil_sanctum','cinder_foothills','east'),
 ('cinder_foothills','cinder_lava_road','east'),('cinder_lava_road','cinder_ravine','south'),
 ('cinder_ravine','cinder_slopes','east'),('cinder_slopes','cinder_vent','north'),
 ('cinder_vent','cinder_upper','east'),('cinder_upper','cinder_antechamber','south'),
 ('cinder_antechamber','cinder_lair','east'),('cinder_lava_road','cinder_vent','east'),
]
OPPOSITE=dict(north='south',south='north',east='west',west='east')
AREAS={key:dict(id=key,name=name,position=[x,y],danger=danger,region=region,arrangement=layout,
               size=[960,540] if layout=='hub' else [1440,900] if layout in ('road','grove','lair') else [1200,720],
               artFamily=region+'-environment',artStatus='awaiting-sprite-chat',exits=[])
       for region,rows in AREA_ROWS.items() for key,name,x,y,danger,layout in rows}
for source,destination,edge in CONNECTIONS:
    if source in AREAS:AREAS[source]['exits'].append([destination,edge,OPPOSITE[edge]])
    AREAS[destination]['exits'].append([source,OPPOSITE[edge],edge])

NPCS={
 'city_messenger':dict(name='Ilyan · dispatch rider',area='dunmere',role='city assignment'),
 'city_marshal':dict(name='Marshal Rhea',area='city_refuge',role='defense coordinator'),
 'city_physician':dict(name='Sen · infirmary surgeon',area='city_refuge',role='medical supplies'),
 'city_archivist':dict(name='Vela · city archivist',area='city_refuge',role='records and families'),
 'veil_pathfinder':dict(name='Tess · foxfolk pathfinder',area='veil_haven',role='scouting and practical trust'),
 'veil_keeper':dict(name='Arven · stagfolk keeper',area='veil_haven',role='essence channels'),
 'veil_scholar':dict(name='Moru · owlfolk scholar',area='veil_haven',role='wards and bond evidence'),
 'veil_artisan':dict(name='Bren · badgerfolk artisan',area='veil_haven',role='sanctuary repair'),
}
TOWNS={
 'home':dict(name='Oakvale',services=['market','inn','guild','alchemist'],sideQuests=['fire','letters','seeds']),
 'dunmere':dict(name='Dunmere',services=['market','inn','guild','alchemist'],sideQuests=['root_sump','dunmere_medicine','dunmere_carrier','dunmere_reserve']),
 'city_refuge':dict(name='Aurelian refuge',services=['market','inn','guild','alchemist'],sideQuests=['city_family','city_heirloom','city_medicine','city_workshop']),
 'veil_haven':dict(name='Rootsong',services=['market','inn','guild','alchemist'],sideQuests=['veil_scout','veil_sanctuary_repair','veil_ritual','veil_memory']),
}

# Fixed main quest objects never enter the equipment pouch.
OBJECTS={
 'city_dispatch':('dunmere','Sealed city dispatch'),
 'city_medical_satchel':('city_homes','Marked medical satchel'),
 'city_gate_component':('city_market','Gate winch component'),
 'city_records':('city_archive','Evacuation register'),
 'city_militia_orders':('city_square','Militia command orders'),
 'city_heirloom':('city_homes','Vela’s brass seal'),
 'city_workshop_tools':('city_gate','Workshop tool roll'),
 'dunmere_medicine':('farmstead','Unspoiled medicine case'),
 'dunmere_carrier_note':('irrigation_channels','Carrier’s route note'),
 'dunmere_reserve_tools':('pump_exterior','Reserve ditch tools'),
 'veil_sample_pool':('veil_pools','Fading essence sample'),
 'veil_sample_root':('veil_glades','Damaged root sample'),
 'veil_ward_fragment':('veil_sanctuary','Sanctuary ward fragment'),
 'veil_siphon_records':('veil_siphon_west','Extraction records'),
 'veil_ritual_focus':('veil_siphon_east','Stolen ritual focus'),
 'veil_memory_tablet':('veil_grove','Rootsong memory tablet'),
 'cinder_lair_seal':('cinder_vent','Cracked lair ward'),
}
# The refuge includes the merchant quarter, so no unused tenth city map exists.
OBJECTS['city_gate_component']=('city_refuge',OBJECTS['city_gate_component'][1])
ARTIFACT_TEXT={
 'city_dispatch':'Aurelian controls the grain roads. Its outer gate has fallen. Marshal Rhea asks the hunters who repaired Dunmere’s intake to secure the breach and protect civilian routes.',
 'city_militia_orders':'The raiders are not acting alone. Three militia commanders divide the city. Each order bears Orath’s split-root seal: the same device later seen on the dragon’s collar.',
 'city_records':'Nara, the granary keeper, and Olen, the evacuation clerk, were separated in the homes and archive districts. The protected courtyard is their muster point; securing their rescue does not require a long escort.',
 'city_medical_satchel':'Sen’s marked field dressings were stolen from the infirmary. They can support the main infirmary defense and the surgeon’s optional supply request; both have fixed receipts.',
 'veil_siphon_records':'Orath siphons the old root network to strengthen a command bond. The same split-root seal directs the city militia and the dragon’s collar. The dragon was his weapon, not the source of this extraction.',
 'veil_ward_fragment':'This sanctuary ward uses the old woodland watch geometry. Damaged roots link the spring failures to Orath’s extraction, not a natural drought.',
 'veil_memory_tablet':'Rootsong keeps names through songs and carved memory tablets. Foxfolk pathfinders, stagfolk keepers, owlfolk scholars and badgerfolk artisans share the same settlement; the grafted raiders do not represent its people.',
 'cinder_lair_seal':'The vent ward identifies a safe route through the lair threshold. Keep it with the final pursuit; it takes no pouch space. Activate the four ascent sanctuaries and defeat the two route keepers before entering the dragon’s lair.',
}
OUTCOMES={
 'city_call':'Ilyan’s dispatch opens the eastern road from the pumping station to Aurelian. The repaired intake can supply a city refuge.',
 'city_breach':'The breach is secured. Refuge and square routes open; Rhea can now coordinate named rescues and three critical defenses.',
 'city_rescue':'Nara and Olen reach the refuge muster. Their names replace missing-person notices; the evacuation records are safe.',
 'city_evacuation':'The courtyard evacuation is complete. Civilians shelter at the refuge; this finite assault cannot pay again.',
 'city_gate_repair':'The gate mechanism holds. Defenders can reinforce the breach while hunters use the district loop.',
 'city_infirmary':'Sen’s medical stores survive the attack. The refuge remains a recovery point.',
 'city_commanders':'Varr, Sere and Kes are defeated. Their orders expose Orath’s militia. The upper terrace opens from archive and observatory.',
 'city_terrace':'The dragon destroys the beacon, displays Orath’s collar seal and leaves. A magical disturbance leads through the eastern terrace into the Verdant Veil.',
 'veil_trust':'Siv reaches Rootsong and the threshold path is repaired. Tess and Arven trust you with the failing pools and sanctuary wards.',
 'veil_imbalance':'The pool, root and sanctuary evidence agree: deliberate siphoning is draining the old network.',
 'veil_siphons':'Both siphon sites are disabled. Their records name Archmage Orath and identify the dragon’s command bond; his sanctum is open.',
 'veil_archmage':'Orath is defeated. He owned and commanded the dragon through the split-root bond. Breaking it ends his control, but the still-destructive dragon flees to the Cinder Crown. Limited streams recover; pursue it before it returns.',
 'cinder_dragon':'The dragon is dead, Orath’s threat is resolved and the main campaign is finished. Settlements and unfinished optional stories remain available in this completed save.',
}

def quest(key,title,hub,requires,prerequisites=(),optional=False,contact=None,shared=12,magic=1,skill=0):
    return dict(id=key,title=title,hub=hub,requires=list(requires),prerequisites=list(prerequisites),
                optional=optional,contact=contact or ('city_marshal' if hub=='city_refuge' else 'veil_keeper' if hub=='veil_haven' else 'city_messenger'),
                reward=dict(receipt='campaign:'+key,sharedRunes=shared,magicRunes=magic,skillPoints=skill,
                            ownership='world shared Runes; personal item/Magic/SP; once, late join reconciliation',
                            fullPouch='new item converts to sell value; existing items untouched'))
QUESTS={q['id']:q for q in [
 quest('city_call','The City’s Distress','dunmere',['city_dispatch'],['pumping_finale'],shared=0,magic=0),
 quest('city_breach','Break the Outer Assault','city_refuge',['city_breach'],['city_call'],skill=2),
 quest('city_rescue','Names in the Smoke','city_refuge',['rescue:nara','rescue:olen','city_records'],['city_breach'],skill=1),
 quest('city_evacuation','Hold the Courtyard','city_refuge',['defense:city_evacuation'],['city_breach'],skill=1),
 quest('city_gate_repair','The Gate Must Hold','city_refuge',['city_gate_component','defense:city_gate_repair'],['city_breach'],skill=1),
 quest('city_infirmary','A Shelter Under Fire','city_refuge',['city_medical_satchel','defense:city_infirmary'],['city_breach'],skill=1),
 quest('city_commanders','The Hidden Militia','city_refuge',['city_militia_orders','boss:city_knight','boss:city_mage','boss:city_archer'],['city_rescue','city_evacuation','city_gate_repair','city_infirmary'],shared=36,magic=2,skill=2),
 quest('city_terrace','Above the Broken Banners','city_refuge',['cinematic:city_dragon'],['city_commanders'],shared=20,magic=1),
 quest('veil_trust','Useful Hands','veil_haven',['rescue:veil_forager','repair:veil_path'],['city_terrace'],skill=1),
 quest('veil_imbalance','What the Roots Remember','veil_haven',['veil_sample_pool','veil_sample_root','veil_ward_fragment'],['veil_trust'],skill=2),
 quest('veil_siphons','The Stolen Current','veil_haven',['mechanism:veil_siphon_west','mechanism:veil_siphon_east','veil_siphon_records'],['veil_imbalance'],skill=2),
 quest('veil_archmage','The Hand on the Chain','veil_haven',['boss:veil_archmage','bond_broken'],['veil_siphons'],shared=40,magic=2,skill=2),
 quest('cinder_dragon','End the Dragon’s Reign','cinder_foothills',['cinder_lair_seal','boss:cinder_dragon','ending:campaign'],['veil_archmage'],contact='cinder_assignment',shared=80,magic=2),
 quest('dunmere_medicine','Clean Hands, Clean Water','dunmere',['dunmere_medicine'],['chapter_outcome'],True,shared=8),
 quest('dunmere_carrier','The Last Carrier','dunmere',['dunmere_carrier_note','rescue:dunmere_carrier'],['chapter_outcome'],True,shared=8),
 quest('dunmere_reserve','A Reserve for Tomorrow','dunmere',['dunmere_reserve_tools','repair:dunmere_reserve'],['pumping_finale'],True,shared=10),
 quest('city_family','The Name on the Door','city_refuge',['rescue:city_brother'],['city_breach'],True,'city_archivist'),
 quest('city_heirloom','The Brass Seal','city_refuge',['city_heirloom'],['city_breach'],True,'city_archivist'),
 quest('city_medicine','A Surgeon’s Satchel','city_refuge',['city_medical_satchel'],['city_breach'],True,'city_physician'),
 quest('city_workshop','Tools for the Living','city_refuge',['city_workshop_tools','repair:city_workshop'],['city_breach'],True,'city_physician'),
 quest('veil_scout','A Missing Pathfinder','veil_haven',['rescue:veil_scout'],['veil_trust'],True,'veil_pathfinder'),
 quest('veil_sanctuary_repair','A Roof for the Roots','veil_haven',['veil_ward_fragment','repair:veil_sanctuary'],['veil_trust'],True,'veil_artisan'),
 quest('veil_ritual','The Interrupted Song','veil_haven',['veil_ritual_focus','defense:veil_ritual'],['veil_trust'],True,'veil_keeper'),
 quest('veil_memory','A People’s Memory','veil_haven',['veil_memory_tablet'],['veil_trust'],True,'veil_scholar'),
]}

ENEMIES={key:dict(id=key,name=name,region=region,kind=kind,role=role,affinity=element,
                   unique=unique,artStatus='awaiting-sprite-chat',artFamily=key)
 for region,rows in {
 'aurelian':[
 ('breach_captain','Breach Captain','troll','defender','Stone',True),
 ('knife_raider','Knife Raider','wolf','flanker','Shadow',False),('shield_bruiser','Shield Bruiser','troll','defender','Stone',False),
 ('bow_poacher','Bow Poacher','serpent','ranged','Nature',False),('fire_saboteur','Fire Saboteur','spider','channeler','Fire',False),
 ('militia_guard','Militia Guard','troll','defender','Stone',False),('militia_archer','Militia Archer','serpent','ranged','Nature',False),
 ('militia_mage','Militia Battlemage','serpent','channeler','Arcane',False),('militia_officer','Militia Signal Officer','troll','support','Arcane',False),
 ('city_knight','Commander Varr','minotaur','charger','Stone',True),('city_mage','Magister Sere','serpent','channeler','Arcane',True),
 ('city_archer','Captain Kes','serpent','ranged','Nature',True)],
 'verdant':[
 ('veil_scout_hostile','Grafted Scout','wolf','flanker','Nature',False),('thorn_guardian','Thorn Guardian','troll','defender','Nature',False),
 ('siphon_construct','Siphon Construct','behemoth','bruiser','Arcane',False),('siphon_apprentice','Siphon Apprentice','serpent','channeler','Arcane',False),
 ('essence_stalker','Essence Stalker','spider','ambusher','Shadow',False),('veil_archmage','Archmage Orath','serpent','channeler','Arcane',True)],
 'cinder':[
 ('ash_draco','Ash Draco','draco','draco','Fire',False),('basalt_guardian','Basalt Guardian','behemoth','bruiser','Stone',False),
 ('cinder_serpent','Cinder Serpent','serpent','ranged','Fire',False),('vent_stalker','Vent Stalker','spider','ambusher','Fire',False),
 ('ravine_keeper','Ravine Keeper','minotaur','charger','Stone',True),('summit_warden','Summit Warden','behemoth','bruiser','Fire',True),
 ('cinder_dragon','The Crownfire Dragon','dragon','charger','Fire',True)]}.items()
 for key,name,kind,role,element,unique in rows}

# Every defense has finite, distinct authored pressure; no random spawn schedule.
DEFENSES={
 'city_evacuation':dict(area='city_homes',name='Evacuation courtyard',health=280,position=[480,330],breakSeconds=4,
    waves=[['knife_raider','bow_poacher'],['shield_bruiser','knife_raider','bow_poacher']],
    spawns=[[130,140],[820,140],[760,440],[140,440]],description='Hold two approaches while Nara and Olen reach the protected muster point.'),
 'city_gate_repair':dict(area='city_gate',name='Gate repair winch',health=320,position=[620,280],breakSeconds=5,
    waves=[['shield_bruiser','fire_saboteur'],['militia_guard','militia_archer','fire_saboteur']],
    spawns=[[140,160],[820,150],[180,430],[820,430]],description='Protect the winch. Saboteurs approach from side lanes; cover blocks archers.'),
 'city_infirmary':dict(area='city_archive',name='Infirmary supplies',health=240,position=[480,370],breakSeconds=6,
    waves=[['militia_archer','knife_raider'],['militia_officer','militia_guard','militia_archer']],
    spawns=[[160,130],[800,130],[150,420],[810,420]],description='Intercept ranged threats and their officer before they reach the medical stores.'),
 'veil_ritual':dict(area='veil_grove',name='Rootsong ritual',health=300,position=[480,320],breakSeconds=5,
    waves=[['essence_stalker','siphon_apprentice'],['thorn_guardian','essence_stalker','siphon_apprentice']],
    spawns=[[160,140],[800,140],[160,430],[800,430]],description='Protect the returned focus while residents reconnect one damaged root.')}
RESCUES={
 'nara':dict(area='city_homes',position=[330,190],name='Nara · granary keeper',guards='homes-raiders'),
 'olen':dict(area='city_archive',position=[700,330],name='Olen · evacuation clerk',guards='archive-patrol'),
 'city_brother':dict(area='city_square',position=[270,400],name='Jori · Vela’s brother',guards='square-patrol'),
 'veil_forager':dict(area='veil_glades',position=[320,390],name='Siv · foxfolk forager',guards='glade-thorns'),
 'veil_scout':dict(area='veil_siphon_east',position=[740,450],name='Ren · Rootsong scout',guards='east-apprentices'),
 'dunmere_carrier':dict(area='farmstead',position=[280,400],name='Eris · grain carrier',guards='barn-guards')}
REPAIRS={
 'dunmere_reserve':dict(area='fields',requires=['dunmere_reserve_tools'],position=[300,390]),
 'city_workshop':dict(area='city_refuge',requires=['city_workshop_tools'],position=[360,390]),
 'veil_path':dict(area='veil_threshold',requires=[],position=[610,340]),
 'veil_sanctuary':dict(area='veil_sanctuary',requires=['veil_ward_fragment'],position=[470,350])}
SIPHON_FEEDS={
 'veil_feed_north':dict(area='veil_siphon_west',position=[450,190],name='Close the northern essence feed'),
 'veil_feed_south':dict(area='veil_siphon_west',position=[470,460],name='Close the southern essence feed')}
SIPHON_FOCI={'veil_focus_west':dict(area='veil_siphon_east',position=[400,280]),'veil_focus_east':dict(area='veil_siphon_east',position=[740,210])}
CHECKPOINTS={key:dict(area=area,position=pos,skillPoints=sp,restores='only first activation outside combat; repeats only choose recovery',safeSkills=True)
 for key,area,pos,sp in [('cinder_entry','cinder_foothills',[220,300],1),('cinder_shelter','cinder_ravine',[220,400],1),
 ('cinder_upper','cinder_upper',[220,320],2),('cinder_last','cinder_antechamber',[480,380],1)]}
ENCOUNTER_REWARDS={
 'ravine_keeper':dict(receipt='encounter:ravine_keeper',sharedRunes=15,items=['cinder_heatward','phoenix_flask'],repeatable=False),
 'summit_warden':dict(receipt='encounter:summit_warden',sharedRunes=20,items=['cinder_pursuit_blade','cinder_shelter_plate','cinder_pack_focus'],repeatable=False)}

def manifest():
    """Secret-free contract. Development content is never called finished art."""
    return copy.deepcopy(dict(version=VERSION,regionCount=5,regions=REGIONS,areas=AREAS,connections=CONNECTIONS,
       towns=TOWNS,npcs=NPCS,quests=QUESTS,questObjects={k:dict(id=k,area=v[0],name=v[1],pouch=False) for k,v in OBJECTS.items()},
       enemies=ENEMIES,defenses=DEFENSES,rescues=RESCUES,repairs=REPAIRS,checkpoints=CHECKPOINTS,
       encounterRewards=ENCOUNTER_REWARDS,
       siphonFeeds=SIPHON_FEEDS,siphonFoci=SIPHON_FOCI,
       items=__import__('campaign_equipment').manifest(),heroNodes=__import__('campaign_skills').manifest(),
       rewardLedger={key:dict(**q['reward'],repeatable=False,personalItemPriority={hero:__import__('campaign_equipment').reward_options(key,hero) for hero in __import__('campaign_skills').ACTIVES}) for key,q in QUESTS.items()},
       authoredCollision=dict(coordinateSpace=[960,540],scaleToAreaSize=True,arrangements=__import__('campaign_expansion').LAYOUTS,rule='Finished scenery must match these authoritative footprints; props remain static by default.'),
       artifactText=ARTIFACT_TEXT,questOutcomes=OUTCOMES,
       encounters={area:[dict(id=area+'-'+group,group=group,center=[x,y],enemies=kinds) for group,x,y,kinds in rows] for area,rows in __import__('campaign_expansion').PACKS.items()},
       bossEncounters={key:dict(id='exp-'+key,area=area,unique=True,retry='full encounter, stable kill receipts') for key,area in __import__('campaign_progress').BOSSES.items()},
       ownership=dict(gameplay='this chat: IDs, rules, AI, collision, saves, progression',art='sprite chat: finished images, cosmetic rendering; preserve IDs/footprints'),
       cinematics={'city_dragon':dict(area='city_terrace',seconds=7,skippable=True,targetable=False,damage=False,restart='restart finite scene; same resolved receipt')},
       audio=dict(policy='reuse existing event/Bfxr families; no new bank required',families=['interact','warning','release','complete','travel','skill-learn','boss-phase']),
       recovery=dict(progress='completed facts/claims persist',attempts='unfinished full encounter restarts, stable kill receipts',wipe='existing 15% once',storage='local disk; Render free disk temporary')))

def validate_contract(document=None):
    d=manifest() if document is None else document
    if d['version']!=VERSION or d['regionCount']!=5 or len(d['regions'])!=5:raise ValueError('Campaign must contain exactly five regions.')
    existing={'pump_exterior','home','dunmere','fields','farmstead','irrigation_channels'}
    for a in d['areas'].values():
        if a['region'] not in d['regions']:raise ValueError('Unknown gameplay region.')
        for other,edge,reverse in a['exits']:
            if other not in d['areas'] and other not in existing:raise ValueError('Disconnected area ID: '+other)
            if OPPOSITE[edge]!=reverse:raise ValueError('Mismatched reverse exit.')
            if other in d['areas'] and [a['id'],reverse,edge] not in d['areas'][other]['exits']:raise ValueError('Missing reverse route.')
    for key,q in d['quests'].items():
        if key!=q['id'] or len(q['requires'])!=len(set(q['requires'])):raise ValueError('Invalid quest contract.')
        if any(p not in d['quests'] and p not in ('pumping_finale','chapter_outcome') for p in q['prerequisites']):raise ValueError('Unknown prerequisite.')
    visited=set();active=set()
    def check(k):
        if k in active:raise ValueError('Cyclic quest prerequisites.')
        if k in visited or k not in d['quests']:return
        active.add(k)
        for pre in d['quests'][k]['prerequisites']:check(pre)
        active.remove(k);visited.add(k)
    for k in d['quests']:check(k)
    for t in d['towns'].values():
        if not 3<=len(t['sideQuests'])<=4:raise ValueError('Every town needs three or four optional stories.')
    if sum(q['reward']['skillPoints'] for q in d['quests'].values())+sum(c['skillPoints'] for c in d['checkpoints'].values())!=20:raise ValueError('Skill reward ledger mismatch.')
    return True
