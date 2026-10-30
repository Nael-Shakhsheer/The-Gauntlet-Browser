"""Server-side acquisition differences published only after confirmed storage.

This compares committed mutation snapshots, never browser polls. Baselines are
transient and initialize on restoration, so reconnect never replays old rewards.
"""
import copy
import feedback


def snapshot(room,p):
    items={i['id']:(copy.deepcopy(i),where) for where,rows in [('pouch',p.get('inventory',[])),('equipment',p.get('toolSlots',[])+p.get('utilitySlots',[]))] for i in rows if i}
    return dict(items=items,magic=p.get('magicRunes',{}).get('balance',0),claims=list(p.get('magicRunes',{}).get('claims',[])),pending=copy.deepcopy(p.get('pendingRewards',{})),resolved=copy.deepcopy(p.get('resolvedRewards',{})),history=[r['id'] for r in room['adventure'].get('rewardHistory',[])])


def prime(room):
    if not room.get('adventure'):return
    base=room.setdefault('_acquisitionBase',{})
    for p in room['players'].values():
        if p['id'] not in base:base[p['id']]=snapshot(room,p)


def confirmed(room):
    if not room.get('adventure'):return
    prime(room);base=room['_acquisitionBase']
    from game import ITEMS
    for p in room['players'].values():
        now=snapshot(room,p);old=base[p['id']];base[p['id']]=now
        if p.get('bot'):continue
        def emit(**data):feedback.emit(room,'acquisition',actor=p,privateTo=p['id'],personal=True,**data)
        for identity,(item,where) in now['items'].items():
            if identity not in old['items']:emit(itemKey=item['key'],name=item['name'],rarity=item.get('rarity','common'),quantity=1,destination=where)
        for key,row in now['pending'].items():
            if key not in old['pending']:emit(name=row['title'],rarity='choice',quantity=1,destination='pending reward · choose in Journal')
        for key,row in now['resolved'].items():
            if key not in old['resolved'] and row['delivery']=='sell':
                item=ITEMS[row['item']];emit(itemKey=row['item'],name=item['name'],rarity=item.get('rarity','common'),quantity=1,destination='converted to '+str(row['soldRunes'])+' shared Runes')
        for row in room['adventure'].get('rewardHistory',[]):
            if row['id'] in old['history']:continue
            for who in row['recipients']:
                if row['id'] in now['resolved'] and row['id'] not in old['resolved']:continue
                if who.get('id')==p['id'] and who.get('convertedRunes'):emit(name=who['item'],rarity='reward',quantity=1,destination='pouch full · converted to '+str(who['convertedRunes'])+' shared Runes')
        gained=set(now['claims'])-set(old['claims'])
        if gained:
            import magic_runes
            feedback.emit(room,'magic_acquired',actor=p,privateTo=p['id'],personal=True,quantity=sum(magic_runes.SOURCES[k] for k in gained),balance=now['magic'])
