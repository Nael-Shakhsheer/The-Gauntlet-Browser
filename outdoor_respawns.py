"""Ten-minute outdoor generations. Unoccupied areas only; no active-body resets."""
import copy
import time

INTERVAL_SECONDS=600
CHECK_SECONDS=2
EXCLUDED={'hunter_wolves','camp_guards','mill-approach','mill-approach-flank'}


def ordinary(area,e):
    import adventure,dungeons,region_content
    return (area in adventure.GROUPS and area not in dungeons.AREAS and area not in region_content.HUBS and
            area not in ('caravan','shrine','ruins','cellar') and e.get('group') and e['group'] not in EXCLUDED and
            'shrine' not in e['group'] and not any(e.get(k) for k in ('boss','miniBoss','structure','uniqueQuest')))


def prepare(area,state,world=None,room=None):
    if 'respawns' in state:return
    import adventure
    if area not in adventure.GROUPS:return
    groups={}
    templates=copy.deepcopy(state['enemies'])
    if world and room:
        # Reconstruct only authored origins with existing defeat receipts. Do not
        # spawn missing enemies now or reinterpret a partial fight as completed.
        known={e['id'] for e in templates};defeated=set(state.get('defeated',[]))
        defeated.update(k.removeprefix('enemy:') for k in room['adventure']['claimed'] if k.startswith('enemy:'))
        if defeated-known:templates += [e for e in __import__('adventure').build_area(world,room,area)['enemies'] if e['id'] in defeated-known]
    for e in templates:
        if not ordinary(area,e):continue
        origin=e.setdefault('lifeOrigin',e['id']);e.setdefault('lifeGeneration',0)
        g=groups.setdefault(e['group'],dict(generation=0,templates=[],deaths={},eligibleAt=None,paid=0))
        g['templates'].append(copy.deepcopy(e))
    if groups:
        live={e.get('lifeOrigin',e['id']) for e in state['enemies']};stamp=time.time()
        for g in groups.values():
            g['deaths']={e.get('lifeOrigin',e['id']):stamp for e in g['templates'] if e.get('lifeOrigin',e['id']) not in live}
            if len(g['deaths'])==len(g['templates']):g['eligibleAt']=stamp+INTERVAL_SECONDS
        state['respawns']=dict(version=1,groups=groups)


def killed(room,e,stamp=None):
    a=room['adventure'];state=a['areas'][a['current']];prepare(a['current'],state)
    g=state.get('respawns',{}).get('groups',{}).get(e.get('group'))
    if not g:return False
    origin=e.get('lifeOrigin',e['id']);generation=e.get('lifeGeneration',0)
    if generation!=g['generation'] or origin in g['deaths']:return True
    stamp=time.time() if stamp is None else stamp;g['deaths'][origin]=stamp
    if generation and g['paid']<6:room['runes']+=1;g['paid']+=1
    if len(g['deaths'])==len(g['templates']):g['eligibleAt']=stamp+INTERVAL_SECONDS
    return generation>0


def tick(world,room,now):
    if now<room.get('_respawnCheckAt',0):return
    room['_respawnCheckAt']=now+CHECK_SECONDS
    a=room['adventure'];wall=time.time();changed=False
    for area,state in a['areas'].items():
        if area==a['current']:continue # Never materialize enemies in an occupied area.
        for group,g in state.get('respawns',{}).get('groups',{}).items():
            if g['eligibleAt'] is None or wall<g['eligibleAt']:continue
            if any(e.get('group')==group for e in state['enemies']):continue
            g.update(generation=g['generation']+1,deaths={},eligibleAt=None,paid=0)
            for template in g['templates']:
                e=copy.deepcopy(template);origin=e.get('lifeOrigin',e['id'])
                e.update(id=origin+'~'+str(g['generation']),lifeOrigin=origin,lifeGeneration=g['generation'],hp=e['maxHp'],x=e['homeX'],y=e['homeY'])
                state['enemies'].append(e)
            changed=True
    if changed:__import__('adventure').save(world,room)


def validate(area,state):
    s=state.get('respawns')
    if s is None:return
    if not isinstance(s,dict) or set(s)!={'version','groups'} or s['version']!=1 or not isinstance(s['groups'],dict) or len(s['groups'])>12:raise ValueError('Unsupported outdoor generation record.')
    for key,g in s['groups'].items():
        if not isinstance(g,dict) or set(g)!={'generation','templates','deaths','eligibleAt','paid'}:raise ValueError('Invalid outdoor group.')
        if type(g['generation']) is not int or not 0<=g['generation']<=10**9 or type(g['paid']) is not int or not 0<=g['paid']<=6:raise ValueError('Invalid outdoor generation.')
        if not isinstance(g['templates'],list) or not 1<=len(g['templates'])<=12:raise ValueError('Invalid respawn templates.')
        origins=[]
        for e in g['templates']:
            if not isinstance(e,dict) or not isinstance(e.get('group'),str) or not isinstance(e.get('lifeOrigin',e.get('id')),str):raise ValueError('Invalid respawn origin.')
            if not ordinary(area,e) or e['group']!=key or e.get('lifeGeneration',0)!=0:raise ValueError('Unique encounter cannot respawn.')
            origins.append(e.get('lifeOrigin',e['id']))
        if len(set(origins))!=len(origins) or not isinstance(g['deaths'],dict) or any(k not in origins or type(v) not in (int,float) or not 0<=v<=10**12 for k,v in g['deaths'].items()):raise ValueError('Invalid outdoor death receipts.')
        due=g['eligibleAt']
        if due is not None and (type(due) not in (int,float) or not 0<=due<=10**12 or len(g['deaths'])!=len(origins)):raise ValueError('Invalid respawn time.')
