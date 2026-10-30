"""Small ability ranks paid with the existing finite Adventure skill points."""
MAX_RANK=3

def ensure(p):
    s=p.setdefault('abilityUpgrades',dict(version=1,hero=p['class'],ranks={}))
    if s['hero']!=p['class']:s.update(hero=p['class'],ranks={})
    return s
def rank(p,aid):return p.get('abilityUpgrades',{}).get('ranks',{}).get(aid,0)
def spent(p):return sum(p.get('abilityUpgrades',{}).get('ranks',{}).values())
def effect(a,r):
    return ('Basic strength +'+str(r*5)+'%') if a['attackType']=='light' else ('Mana cost −'+str(min(r,max(0,a.get('manaCost',0)-1))))
def enhance(p,catalog):
    for aid,a in catalog.items():
        r=rank(p,aid)
        if not r:continue
        if a['attackType']=='light':a['power']=a['power']*(1+.05*r)
        else:a['manaCost']=max(1,a['manaCost']-r)
    return catalog
def validate(p,nodes):
    s=p.get('abilityUpgrades')
    if s is None:return
    if not isinstance(s,dict) or set(s)!={'version','hero','ranks'} or s['version']!=1 or s['hero']!=p['class'] or not isinstance(s['ranks'],dict):raise ValueError('Invalid ability upgrades.')
    import hero_skills
    allowed={n['id'] for n in nodes if n['type']=='ability'}
    if __import__('ascension').active(p):allowed.add(__import__('ascension').ability(p)['id'])
    if any(k not in allowed or type(v) is not int or not 0<=v<=MAX_RANK or not hero_skills.unlocked(p,k) for k,v in s['ranks'].items()):raise ValueError('Invalid ability upgrade ranks.')
