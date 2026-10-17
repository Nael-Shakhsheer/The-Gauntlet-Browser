"""Personal finite progression; never reads or spends the shared Rune pool."""
import math
import re
import copy

SOURCES={'shrine:brook':1,'shrine:deepwood':1,'shrine:watch':1,
 'report:hunter':1,'report:bridge':1,'report:shrine':1,'report:woodland_boss':2,
 'cache:dry_spring':1,'report:failed_harvest':1,'report:irrigation':2,
 'report:mill_cellar':2,'report:chapter_outcome':2}


def ensure(p):
    from game import CLASSES
    if 'magicRunes' not in p:
        ordinary=math.ceil(CLASSES[p['class']]['hp']*(1+.04*p.get('skillRanks',{}).get('vitality',0)))
        p['magicRunes']=dict(version=1,claims=[],balance=0,healthRanks=0,manaRanks=0,ascended=False,transactions={},
            legacyHp=max(0,p['maxHp']-ordinary),legacyMana=max(0,p['maxMana']-100))
    return p['magicRunes']


def claim(p,key):
    m=ensure(p)
    if key not in SOURCES:raise ValueError('Unknown personal Magic Rune source.')
    if key in m['claims']:return False
    m['claims'].append(key);m['balance']+=SOURCES[key];return True


def reconcile_reports(room):
    from chapter_flow import available_rewards
    sources=available_rewards(room)
    for p in room['players'].values():
        for source in sources:claim(p,source)


def maxima(p,health=None,mana=None,ascended=None):
    from game import CLASSES
    m=ensure(p);health=m['healthRanks'] if health is None else health;mana=m['manaRanks'] if mana is None else mana
    ascended=m['ascended'] if ascended is None else ascended
    return (((CLASSES[p['class']]['hp']*(100+4*p.get('skillRanks',{}).get('vitality',0)+5*health+(10 if ascended else 0))+99)//100)+m['legacyHp'],
            100+5*mana+(10 if ascended else 0)+m['legacyMana'])


def refresh(p):
    hp,mana=maxima(p)
    if hp!=p['maxHp']:
        ratio=p['hp']/p['maxHp'];p['maxHp']=hp;p['hp']=max(1,math.floor(hp*ratio)) if p['status']=='alive' and ratio>0 else 0
    if mana!=p['maxMana']:
        ratio=p['mana']/p['maxMana'];p['maxMana']=mana;p['mana']=min(mana,mana*ratio)


def safe(room,p):
    import progression,region_content
    return p['status']=='alive' and not progression.locked(room,p) and room['adventure']['current'] in region_content.HUBS


def transact(world,room,p,payload):
    import adventure
    if not safe(room,p):raise ValueError('Spend Magic Runes safely in Oakvale or Dunmere, after finishing the conversation.')
    m=ensure(p);key=payload.get('requestId');kind=payload.get('purchase')
    if not isinstance(key,str) or not re.fullmatch('[A-Za-z0-9_-]{16,80}',key):raise ValueError('A private purchase retry ID is required.')
    if kind not in ('health','mana','ascend'):raise ValueError('Choose Health, Mana or Ascension.')
    if key in m['transactions']:
        if m['transactions'][key]['kind']!=kind:raise ValueError('This retry belongs to another purchase.')
        return
    before={k:copy.deepcopy(p[k]) for k in ('magicRunes','hp','mana','maxHp','maxMana')}
    if kind=='ascend':
        if m['ascended']:return
        if m['balance']<15:raise ValueError('Ascension requires 15 currently unspent Magic Runes. Prior purchases do not count.')
        if 'chapter_outcome' not in room['adventure'].get('chapter',{}).get('turnedIn',[]):raise ValueError('Finish and report Dunmere’s harvest and water investigation before Ascension.')
        m['balance']-=15;m['ascended']=True
    else:
        field=kind+'Ranks';rank=m[field]
        if payload.get('expectedRank')!=rank:raise ValueError('This rank changed; review the current purchase preview before retrying.')
        if rank>=5:raise ValueError('This permanent purchase is capped at five ranks.')
        if m['balance']<1:raise ValueError('You need one unspent personal Magic Rune.')
        m['balance']-=1;m[field]+=1
    m['transactions'][key]=dict(kind=kind);refresh(p)
    if not adventure.save(world,room) and world.storage:
        p.update(before)
        raise ValueError('Purchase was not committed: storage did not confirm the save. Your Magic Runes and stats are unchanged; retry after exporting/checking storage.')
    if kind=='ascend':__import__('feedback').emit(room,'ascension_transform',actor=p)
    adventure.announce(world,room,p['name']+(' has Ascended.' if kind=='ascend' else ' purchased a permanent '+kind+' improvement.'))


def view(room,p):
    m=ensure(p);hp,mana=maxima(p)
    return dict(ascensionEligible='chapter_outcome' in room['adventure'].get('chapter',{}).get('turnedIn',[]),balance=m['balance'],collected=sum(SOURCES[k] for k in m['claims']),healthRanks=m['healthRanks'],manaRanks=m['manaRanks'],
        ascended=m['ascended'],safe=safe(room,p),healthBefore=hp,healthAfter=maxima(p,health=min(5,m['healthRanks']+1))[0],
        manaBefore=mana,manaAfter=maxima(p,mana=min(5,m['manaRanks']+1))[1],ascendHealth=maxima(p,ascended=True)[0],ascendMana=maxima(p,ascended=True)[1],
        claims=m['claims'],chapterBudget=16,description='Personal Magic Runes. Health/Mana cost 1; Ascension requires the completed Dunmere investigation and spends 15 currently unspent. There are 15 guaranteed + 1 optional in the playable chapters. Spending more than one makes Ascension unavailable until later content adds sources. Purchases are permanent; resource proportions and recharge are kept.')


def validate(p):
    m=p.get('magicRunes')
    if m is None:return
    keys={'version','claims','balance','healthRanks','manaRanks','ascended','transactions','legacyHp','legacyMana'}
    if not isinstance(m,dict) or set(m)!=keys or m['version']!=1 or type(m['ascended']) is not bool:raise ValueError('Unsupported personal Magic Rune record.')
    if not isinstance(m['claims'],list) or any(not isinstance(k,str) or k not in SOURCES for k in m['claims']) or len(m['claims'])!=len(set(m['claims'])):raise ValueError('Invalid Magic Rune claims.')
    for key,maximum in [('balance',16),('healthRanks',5),('manaRanks',5),('legacyHp',2500),('legacyMana',2500)]:
        if type(m[key]) is not int or not 0<=m[key]<=maximum:raise ValueError('Invalid permanent Magic Rune value.')
    if m['balance']!=sum(SOURCES[k] for k in m['claims'])-m['healthRanks']-m['manaRanks']-(15 if m['ascended'] else 0):raise ValueError('Magic Rune balance does not match its source/purchase receipts.')
    if not isinstance(m['transactions'],dict) or len(m['transactions'])>11 or any(not re.fullmatch('[A-Za-z0-9_-]{16,80}',k) or not isinstance(v,dict) or set(v)!={'kind'} or v['kind'] not in ('health','mana','ascend') for k,v in m['transactions'].items()):raise ValueError('Invalid Magic Rune transaction receipts.')


def validate_world(a,p):
    m=p.get('magicRunes')
    if not m:return
    import chapter_flow
    allowed={source for key,(source,_) in chapter_flow.MAGIC_SOURCES.items() if key in a.get('chapter',{}).get('turnedIn',[])}
    allowed.update('shrine:'+key for key in a.get('travelShrines',{}).get('active',[]))
    if 'dry_spring_found' in a['claimed']:allowed.add('cache:dry_spring')
    if any(key not in allowed for key in m['claims']):raise ValueError('Personal Magic Rune claim lacks its world activation or report receipt.')
