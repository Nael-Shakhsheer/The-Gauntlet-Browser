"""Personal finite pouch upgrades; shop Runes remain shared."""
import copy

BASE=10
STEP=5
COSTS=(30,60,90,120)

def level(p):return p.get('pouchLevel',0)
def capacity(p):return BASE+STEP*level(p)
def validate(p):
    if type(level(p)) is not int or not 0<=level(p)<=len(COSTS):raise ValueError('Invalid pouch upgrade level.')
def view(p):
    n=level(p)
    return dict(level=n,capacity=capacity(p),nextCapacity=capacity(p)+STEP if n<len(COSTS) else None,
                cost=COSTS[n] if n<len(COSTS) else None,maxLevel=len(COSTS))
def purchase(world,room,p,payload):
    import adventure
    if room['phase']!='town' or not world._at_merchant(room,p):raise ValueError('Visit the market merchant to expand your pouch.')
    n=level(p)
    if payload.get('expectedLevel')!=n:raise ValueError('Pouch capacity changed. Review the current upgrade before buying again.')
    if n>=len(COSTS):raise ValueError('Your pouch is fully expanded.')
    if room['runes']<COSTS[n]:raise ValueError('The party does not have enough shared Runes.')
    before=copy.deepcopy(p);runes=room['runes']
    room['runes']-=COSTS[n];p['pouchLevel']=n+1
    if adventure.active(room) and not adventure.save(world,room) and world.storage:
        p.clear();p.update(before);room['runes']=runes
        raise ValueError('Pouch upgrade was not saved. Your capacity and shared Runes are unchanged.')
    world._say(room,'system','Market',p['name']+' expanded their pouch to '+str(capacity(p))+' spaces.')

