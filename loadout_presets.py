"""Three per-hero safe-hub presets; unlocked state remains authoritative."""
import copy
import time


def state(p):return p.setdefault('loadoutPresets',dict(version=1,revision=0,entries={}))


def validate(p):
    import hero_skills as skills
    record=p.get('loadoutPresets')
    if record is None:return
    if not isinstance(record,dict) or set(record)!={'version','revision','entries'} or record['version']!=1 or type(record['revision']) is not int or not 0<=record['revision']<=10**9 or not isinstance(record['entries'],dict) or len(record['entries'])>24:raise ValueError('Unsupported loadout presets.')
    for key,l in record['entries'].items():
        if key not in {h+':'+str(i) for h in skills.TREES for i in range(1,4)}:raise ValueError('Invalid preset slot.')
        if not isinstance(l,dict) or set(l)!={'basic','active','ultimate'} or not isinstance(l['active'],list) or len(l['active'])!=3:raise ValueError('Invalid stored preset.')
        hero=key.split(':')[0];ids={n['id']:n['ability']['attackType'] for n in skills.TREES[hero] if n['type']=='ability'}
        ids[__import__('ascension').SPECS[hero][0]]='special'
        seen=[]
        for aid,category in [(l['basic'],'light'),*((a,'special') for a in l['active']),(l['ultimate'],'ultimate')]:
            if aid is None:continue
            if not isinstance(aid,str) or ids.get(aid)!=category or aid in seen:raise ValueError('Invalid preset ability.')
            seen.append(aid)
        if l['basic'] is None:raise ValueError('Preset requires a basic attack.')


def apply(world,room,p,payload):
    import hero_skills as skills,adventure
    skills.ensure(room,p)
    if not skills.safe(room,p):raise ValueError('Use presets in a village after closing conversations.')
    index=payload.get('preset')
    if type(index) is not int or index not in (1,2,3):raise ValueError('Choose build1,2 or3.')
    record=state(p)
    if payload.get('revision')!=record['revision']:raise ValueError('Presets changed. Review the current saved builds before retrying.')
    key=p['class']+':'+str(index);kind=payload['action'];before=copy.deepcopy(p)
    if kind=='presetSave':record['entries'][key]=copy.deepcopy(p['adventureLoadout'])
    elif kind=='presetDelete':record['entries'].pop(key,None)
    elif kind=='presetApply':
        l=record['entries'].get(key)
        if l is None:raise ValueError('Save this build before recalling it.')
        if p.get('activeSummons'):raise ValueError('Dismiss live summons through a normal loadout change before recalling a preset. Their recharge is preserved.')
        if any(a and i>=skills.active_slots(room) for i,a in enumerate(l['active'])):raise ValueError('This build uses an active slot not yet available.')
        if any(a and not skills.unlocked(p,a) for a in [l['basic'],*l['active'],l['ultimate']]):raise ValueError('This build contains abilities no longer unlocked. Learn them or save a replacement build.')
        p['adventureLoadout']=copy.deepcopy(l);skills.flatten(p)
        if l['ultimate'] and not p.get('ultimateIntroduced'):
            aid=l['ultimate'];p['abilityCooldowns'][aid]=max(p['abilityCooldowns'].get(aid,0),time.monotonic()+15);p['ultimateIntroduced']=True
    else:raise ValueError('Unknown preset action.')
    record['revision']+=1
    if not adventure.save(world,room) and world.storage:
        p.clear();p.update(before);raise ValueError('Build update was not saved. Previous presets and loadout remain.')
