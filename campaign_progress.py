"""Additive campaign facts, fixed retrieval/rescue receipts and finite attempts.

No monotonic clock, partial wave body or temporary player session is portable.
All protected operations still execute under GameWorld's authoritative lock.
"""
import copy
import math
import time
import campaign_content as content

VERSION=1
SCHEMA={'version','facts','accepted','reported','objectives','attempt','sanctuaries'}
BOSSES={'city_breach':'city_gate','city_knight':'city_barracks','city_mage':'city_observatory',
        'city_archer':'city_square','veil_archmage':'veil_sanctum',
        'ravine_keeper':'cinder_ravine','summit_warden':'cinder_upper','cinder_dragon':'cinder_lair'}
MECHANISMS={'veil_siphon_west','veil_siphon_east'}
FACTS={f for q in content.QUESTS.values() for f in q['requires']}|{'boss:'+k for k in BOSSES}|{'mechanism:'+k for k in MECHANISMS}|set(content.SIPHON_FEEDS)|set(content.SIPHON_FOCI)

def ensure(room):
    a=room['adventure'];s=a.setdefault('campaign',dict(version=VERSION,facts=[],accepted=[],reported=[],objectives={},attempt=None,sanctuaries=[]))
    if s.get('version')!=VERSION:raise ValueError('Unsupported campaign extension; original preserved.')
    return s

def finished(room,key):
    return key in ensure(room)['reported'] or key in room['adventure'].get('chapter',{}).get('turnedIn',[])

def status(room,key):
    s=ensure(room);q=content.QUESTS[key]
    if key in s['reported']:return 'complete'
    if key in s['accepted']:return 'ready-to-turn-in' if set(q['requires'])<=set(s['facts']) else 'accepted'
    return 'offered' if all(finished(room,p) for p in q['prerequisites']) else 'unavailable'

def fact(room,key):
    if key not in FACTS:raise ValueError('Unknown campaign fact; original preserved.')
    s=ensure(room)
    if key in s['facts']:return False
    s['facts'].append(key);return True

def atomic(world,room,operation):
    """Interaction transaction; never called per render, input or ordinary tick."""
    import adventure,adventure_transactions
    before=copy.deepcopy({k:v for k,v in room.items() if k not in ('_killBatch','_chapterProbe')})
    try:
        result=operation()
        if not adventure.save(world,room) and world.storage:raise OSError('Campaign update was not saved. No progress or reward committed.')
        return result
    except Exception as error:
        adventure_transactions.rollback(room,dict(before=before),str(error));raise

def eligible_player(room,p):
    import progression
    if p.get('bot') or not p.get('connected',True) or p['status']!='alive' or p.get('townInterior') or progression.locked(room,p):
        raise ValueError('A connected living hunter must finish the current conversation before acting.')

def gather(world,room,p):
    humans=world._voting_players(room)
    if not humans or any(q['status']!='alive' or q.get('townInterior') or q.get('dialogue') or math.dist((p['x'],p['y']),(q['x'],q['y']))>145 for q in humans):
        raise ValueError('Gather connected living hunters here. Offline hunters and companions do not block this encounter.')

def quest_action(world,room,p,payload):
    import adventure
    eligible_player(room,p);key=payload.get('quest');q=content.QUESTS[key]
    if room['adventure']['current']!=q['hub']:raise ValueError('Report this assignment at '+q['hub'].replace('_',' ')+'.')
    contact=next((f for f in __import__('campaign_expansion').features(room) if f['id']==q['contact'] and math.dist((p['x'],p['y']),(f['x'],f['y']))<=78),None)
    if not contact:raise ValueError('Approach '+content.NPCS.get(q['contact'],{}).get('name','the foothill pursuit marker')+' to accept or report this assignment.')
    state=status(room,key)
    if payload['action']=='chapterAccept' and state in ('accepted','ready-to-turn-in','complete'):return
    if payload['action']=='chapterReport' and state=='complete':return
    if state!=('offered' if payload['action']=='chapterAccept' else 'ready-to-turn-in'):raise ValueError('The assignment is not ready. Inspect its Journal evidence and prerequisites.')
    def commit():
        s=ensure(room)
        if payload['action']=='chapterAccept':s['accepted'].append(key)
        else:
            s['reported'].append(key);reward=q['reward']
            adventure.reward(world,room,reward['receipt'],reward['sharedRunes'],__import__('campaign_equipment').reward_key(key))
            lead={'city_call':'city_approach','city_commanders':'city_terrace','city_terrace':'veil_threshold','veil_archmage':'cinder_foothills'}.get(key)
            if lead:adventure.reveal(room,lead)
        adventure.announce(world,room,('Accepted: '+q['title']+'.') if payload['action']=='chapterAccept' else content.OUTCOMES.get(key,'Completed: '+q['title']+'. The recovered supplies and people remain safe.'))
    atomic(world,room,commit)

def reconcile_personal(room):
    import magic_runes
    s=ensure(room)
    for p in room['players'].values():
        for key in s['reported']:
            if content.QUESTS[key]['reward']['magicRunes']:magic_runes.claim(p,'campaign:'+key)

def retrieve(world,room,p,key):
    if key not in content.OBJECTS:raise ValueError('Unknown fixed quest object.')
    if room['adventure']['current']!=content.OBJECTS[key][0]:raise ValueError('This object belongs to another location.')
    atomic(world,room,lambda:fact(room,key))

def rescue(world,room,p,key):
    import adventure
    spec=content.RESCUES[key]
    if room['adventure']['current']!=spec['area']:raise ValueError('This person is in another location.')
    if any(e.get('group','').startswith(spec['guards']) for e in room['enemies']):raise ValueError('Clear the marked nearby threat first. The rescue cannot be lost to an offscreen death.')
    def commit():
        if fact(room,'rescue:'+key):adventure.announce(world,room,spec['name']+' reached the protected muster point. No long escort is required.')
    atomic(world,room,commit)

def repair(world,room,p,key):
    spec=content.REPAIRS[key]
    if room['adventure']['current']!=spec['area']:raise ValueError('This repair belongs to another location.')
    if not set(spec['requires'])<=set(ensure(room)['facts']):raise ValueError('Recover the marked repair supplies first; quest objects do not use pouch space.')
    if any(math.dist((p['x'],p['y']),(e['x'],e['y']))<250 for e in room['enemies']):raise ValueError('Secure the immediate repair site first.')
    def commit():
        fact(room,'repair:'+key)
        if key=='city_workshop':
            for actor in room['players'].values():
                stock=actor.setdefault('shopStock',[])
                if not any(i['key']=='city_duelist_edge' for i in stock) and len(stock)<30:stock.append(world._make_item('city_duelist_edge'))
    atomic(world,room,commit)

def start_attempt(world,room,p,key):
    import adventure
    eligible_player(room,p);gather(world,room,p);s=ensure(room)
    area=content.DEFENSES[key]['area'] if key in content.DEFENSES else BOSSES[key]
    if room['adventure']['current']!=area:raise ValueError('This encounter belongs to another location.')
    if s['attempt']:raise ValueError('Finish the current sealed encounter first.')
    completion=('defense:' if key in content.DEFENSES else 'boss:')+key
    if completion in s['facts']:return
    if room['enemies']:raise ValueError('Clear the marked approach before committing. Ordinary retreat stays open until then.')
    if key=='city_gate_repair' and 'city_gate_component' not in s['facts']:raise ValueError('Recover the fixed gate winch component first.')
    if key=='city_infirmary' and 'city_medical_satchel' not in s['facts']:raise ValueError('Recover the marked medical satchel first.')
    if key=='veil_ritual' and 'veil_ritual_focus' not in s['facts']:raise ValueError('Return the stolen ritual focus first.')
    if key=='cinder_dragon' and 'cinder_dragon' not in s['accepted']:raise ValueError('Accept the final pursuit at the foothill marker before challenging the dragon.')
    def commit():
        progress=s['objectives'].setdefault(key,dict(completedWaves=[]))
        wave=len(progress['completedWaves'])+1;s['attempt']=dict(id=key,wave=wave)
        room['adventure']['locked']=True;room['_campaignAttempt']=dict(readyAt=time.monotonic()+1.5,spawned=False)
        room.update(projectiles=[],hazards=[])
        adventure.announce(world,room,'Encounter seals the exits: '+key.replace('_',' ')+'. Complete the finite assault or recover at your checkpoint. Failed defenses may be retried without losing rescued people.')
    atomic(world,room,commit)

def targets(room):
    ward=room.get('_campaignWard')
    return [ward] if ward and ward['status']=='alive' else []

def hurt_objective(world,room,target,amount):
    if target.get('status')!='alive':return
    target['hp']=max(0,target['hp']-max(1,round(amount)))
    if not target['hp']:
        target['status']='fallen';fail_attempt(world,room)

def clear_attempt(room):
    room.pop('_campaignAttempt',None);room.pop('_campaignWard',None)
    room['enemies']=[e for e in room.get('enemies',[]) if not e['id'].startswith('exp-')]
    room.update(projectiles=[],hazards=[]);room['adventure']['locked']=False

def fail_attempt(world,room):
    import adventure
    def commit():
        ensure(room)['attempt']=None;clear_attempt(room)
        adventure.announce(world,room,'Defense interrupted. Civilians are safe; completed waves and unique rewards remain. Regroup at the marker to retry the unfinished wave.')
    atomic(world,room,commit)

def recover(room):
    s=room['adventure'].get('campaign')
    if not s:return
    interrupted=bool(s['attempt'] or room.get('_campaignCinematic'))
    s['attempt']=None
    if interrupted:clear_attempt(room)
    room.pop('_campaignCinematic',None)
    for state in room['adventure']['areas'].values():state['enemies']=[e for e in state['enemies'] if not e['id'].startswith('exp-')]

def on_kill(world,room,e):
    """True prevents the legacy woodland boss handler claiming a new boss."""
    if e['id'].startswith('focus-'):
        fact(room,e['id'].removeprefix('focus-'));__import__('adventure').save(world,room);return True
    if not e['id'].startswith('exp-'):return False
    s=ensure(room);attempt=s['attempt']
    if not attempt:return True
    key=attempt['id'];wave=attempt['wave']
    if any(enemy['id'].startswith('exp-') for enemy in room['enemies']):return True
    if key in content.DEFENSES:
        progress=s['objectives'][key]
        if wave not in progress['completedWaves']:progress['completedWaves'].append(wave)
        if wave<len(content.DEFENSES[key]['waves']):
            attempt['wave']=wave+1;room['_campaignAttempt']=dict(readyAt=time.monotonic()+content.DEFENSES[key]['breakSeconds'],spawned=False)
            __import__('adventure').announce(world,room,'Wave '+str(wave)+' secured. Short break before wave '+str(wave+1)+'.')
        else:fact(room,'defense:'+key);s['attempt']=None;clear_attempt(room)
    else:
        fact(room,'boss:'+key)
        if key in content.ENCOUNTER_REWARDS:
            reward=content.ENCOUNTER_REWARDS[key]
            __import__('adventure').reward(world,room,reward['receipt'],reward['sharedRunes'],reward['items'][0])
        if key=='city_breach':fact(room,'city_breach')
        if key=='veil_archmage':
            fact(room,'bond_broken');__import__('adventure').announce(world,room,content.OUTCOMES['veil_archmage'])
        if key=='cinder_dragon':
            fact(room,'ending:campaign')
            if 'cinder_dragon' not in s['reported']:
                s['reported'].append('cinder_dragon');q=content.QUESTS['cinder_dragon']['reward']
                __import__('adventure').reward(world,room,q['receipt'],q['sharedRunes'],'cinder_shelter_plate')
                __import__('adventure').announce(world,room,'CAMPAIGN COMPLETE · The Crownfire Dragon is defeated and Orath’s control is broken. Oakvale keeps its road, Dunmere its safe intake, Aurelian its refuge and Rootsong its recovering streams. Your completed save remains open for visits and unfinished optional stories. Export a backup before leaving.')
        s['attempt']=None;clear_attempt(room)
    __import__('adventure').save(world,room);return True

def checkpoint(world,room,p,key):
    import adventure
    spec=content.CHECKPOINTS[key];s=ensure(room)
    if room['adventure']['current']!=spec['area'] or math.dist((p['x'],p['y']),adventure.point(room,*spec['position']))>78:raise ValueError('Approach the sanctuary to choose it as recovery.')
    if s['attempt'] or room['adventure'].get('locked') or any(math.dist((p['x'],p['y']),(e['x'],e['y']))<300 for e in room['enemies']):raise ValueError('Secure the sanctuary before resting or managing skills.')
    gather(world,room,p)
    def commit():
        first=key not in s['sanctuaries']
        if first:s['sanctuaries'].append(key)
        room['adventure']['checkpoint']=dict(area=spec['area'],bed=None,sanctuary=key)
        if first:
            for actor in world._active_players(room):
                if actor['status']=='alive':actor.update(hp=actor['maxHp'],mana=actor['maxMana'])
        adventure.announce(world,room,'Recovery set: '+key.replace('_',' ')+('. First-visit supplies restore living hunters; recharge is kept.' if first else '. Supplies already used; resources and recharge are kept.'))
    atomic(world,room,commit)

def safe_skills(room,p):
    if p['status']!='alive' or ensure(room)['attempt'] or room['adventure'].get('locked') or any(math.dist((p['x'],p['y']),(e['x'],e['y']))<300 for e in room['enemies']):return False
    import adventure
    return any(key in ensure(room)['sanctuaries'] and spec['area']==room['adventure']['current'] and math.dist((p['x'],p['y']),adventure.point(room,*spec['position']))<=100
               for key,spec in content.CHECKPOINTS.items())

def validate(s):
    if s is None:return
    if not isinstance(s,dict) or set(s)!=SCHEMA or s.get('version')!=VERSION:raise ValueError('Unsupported campaign progress; original preserved.')
    allowed={'facts':FACTS,'accepted':set(content.QUESTS),'reported':set(content.QUESTS),'sanctuaries':set(content.CHECKPOINTS)}
    for field,known in allowed.items():
        values=s[field]
        if not isinstance(values,list) or any(not isinstance(k,str) or k not in known for k in values) or len(values)!=len(set(values)):raise ValueError('Unsupported campaign '+field+'; original preserved.')
    if not set(s['reported'])<=set(s['accepted']):raise ValueError('Campaign report without acceptance.')
    for key in s['accepted']:
        if any(pre in content.QUESTS and pre not in s['reported'] for pre in content.QUESTS[key]['prerequisites']):raise ValueError('Campaign acceptance precedes its reported prerequisites.')
    for key in s['reported']:
        if not set(content.QUESTS[key]['requires'])<=set(s['facts']):raise ValueError('Campaign report without objective facts.')
    if not isinstance(s['objectives'],dict) or set(s['objectives'])-set(content.DEFENSES)-set(BOSSES):raise ValueError('Unknown campaign encounter.')
    for key,progress in s['objectives'].items():
        if not isinstance(progress,dict) or set(progress)!={'completedWaves'}:raise ValueError('Invalid completed wave record.')
        waves=progress['completedWaves'];limit=len(content.DEFENSES[key]['waves']) if key in content.DEFENSES else 1
        if not isinstance(waves,list) or any(type(w) is not int for w in waves) or waves!=list(range(1,len(waves)+1)) or len(waves)>limit:raise ValueError('Invalid finite wave sequence.')
    a=s['attempt']
    if a is not None:
        if not isinstance(a,dict) or set(a)!={'id','wave'} or a['id'] not in s['objectives'] or type(a['wave']) is not int:raise ValueError('Invalid campaign attempt.')
        key=a['id'];limit=len(content.DEFENSES[key]['waves']) if key in content.DEFENSES else 1
        if a['wave']!=len(s['objectives'][key]['completedWaves'])+1 or not 1<=a['wave']<=limit:raise ValueError('Campaign attempt overlaps a completed wave.')
