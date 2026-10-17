"""Personal one-time choices. Shared Rune awards remain Adventure facts."""
import copy

ACTIVITIES={'dungeon:cave_survey','dungeon:cave','dungeon:tower','shrine','region'}


def options(key,hero):
    from game import CLASS_WEAPONS
    if key=='dungeon:cave_survey':return ['warding_tonic','mana_draught']
    if key=='dungeon:cave':return ['phoenix_flask','stormguard_charm']
    if key=='shrine':return ['rescuers_cuirass','stormguard_charm']
    if key=='region':return ['aegis_of_dawn','starfall_blade']
    build={'Knight':'pursuit_blade','Wizard':'arcane_conductor','Archer':'arcane_conductor',
           'Cleric':'rescuers_cuirass','Rogue':'pursuit_blade','Druid':'summoners_staff',
           'Bard':'rescuers_cuirass','Healer':'rescuers_cuirass'}[hero]
    return [CLASS_WEAPONS[hero],build]


def offer(player,key,title):
    if key in player.setdefault('resolvedRewards',{}):return
    player.setdefault('pendingRewards',{}).setdefault(key,dict(title=title,options=options(key,player['class'])))


def validate(p):
    from game import ITEMS
    for field in ('pendingRewards','resolvedRewards'):
        rows=p.get(field,{})
        if not isinstance(rows,dict) or any(k not in ACTIVITIES for k in rows):raise ValueError('Unsupported reward choice.')
    for key,row in p.get('pendingRewards',{}).items():
        if not isinstance(row,dict) or not isinstance(row.get('title'),str) or not 1<=len(row.get('options',[]))<=2 or any(k not in ITEMS for k in row['options']):raise ValueError('Invalid pending reward.')
        # A prior class change may leave an earned choice for the original hero.
        allowed=set().union(*(options(key,h) for h in __import__('game').CLASSES))
        if not set(row['options'])<=allowed:raise ValueError('Unsupported reward options.')
    if set(p.get('pendingRewards',{})) & set(p.get('resolvedRewards',{})):raise ValueError('Reward cannot be pending and claimed.')


def claim(world,room,p,payload):
    from game import ITEMS
    import adventure
    key=str(payload.get('reward',''));item=str(payload.get('item',''))
    if key in p.setdefault('resolvedRewards',{}):return  # Retry does not pay again.
    pending=p.setdefault('pendingRewards',{}).get(key)
    if not pending or item not in pending['options']:raise ValueError('That reward is unavailable.')
    delivery=payload.get('delivery','pouch');sold=0;replaced=None
    if delivery=='sell':sold=ITEMS[item]['sell'];room['runes']+=sold
    elif delivery=='pouch':
        if len(p['inventory'])>=10:
            replaced=next((i for i in p['inventory'] if i['id']==payload.get('replace')),None)
            if not replaced:raise ValueError('Pouch full. Choose an item to sell and replace, or sell this reward for shared Runes.')
            p['inventory'].remove(replaced);room['runes']+=replaced['sell']
        p['inventory'].append(world._make_item(item))
    else:raise ValueError('Unknown reward delivery.')
    result=dict(item=item,delivery=delivery,soldRunes=sold,replaced=replaced['key'] if replaced else None)
    p['resolvedRewards'][key]=result;del p['pendingRewards'][key]
    for receipt in room['adventure'].get('rewardHistory',[]):
        if receipt['id']==key:
            receipt['recipients'].append(dict(name=p['name'],item=ITEMS[item]['name'],convertedRunes=sold,replaced=ITEMS[replaced['key']]['name'] if replaced else None))
    message=p['name']+' chose '+ITEMS[item]['name']+ (f' · sold for {sold} shared Runes.' if sold else ' · added to pouch.')
    if replaced:message+=' Sold '+replaced['name']+f' for {replaced["sell"]} shared Runes to make room.'
    adventure.announce(world,room,message)


def view(world,p):
    result=[]
    for key,row in p.get('pendingRewards',{}).items():
        choices=[]
        for item in row['options']:
            candidate=world._make_item(item);candidate.pop('id',None)
            candidate['alreadyOwned']=any(i and i['key']==item for i in p['inventory']+p['toolSlots'])
            choices.append(candidate)
        result.append(dict(id=key,title=row['title'],options=choices))
    return result
