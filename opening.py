"""The Last Caravan: durable story receipts, disposable combat attempts.

Only new worlds opt in. No enemy/treasure/currency payouts occur here. Restart
rebuilds the unfinished authored encounter; finished threats never respawn.
Animation clocks and defender support budgets are intentionally not saved.
"""
import math
import time
import feedback

AREA='caravan'
FACTS=('encounter_started','initial_threat_cleared','watch_event_observed',
       'withdrawal_unlocked','oakvale_reached','opening_complete')
MUSTER=(1040,150)
MANIFEST='The manifest lists missing grain deliveries from Dunmere, dated before the dragon attack. A note says: "Brook cloudy. Ask the hunter about the old watch." The grain road beyond the woodland leads to Dunmere.'


def active(room):
    s=room.get('adventure',{}).get('opening')
    return bool(s and 'opening_complete' not in s['facts'])


def validate(s,current):
    if s is None:
        if current==AREA:raise ValueError('Missing caravan progress; original preserved.')
        return
    if not isinstance(s,dict) or set(s)-{'version','facts','attempt','skipped','manifestRead'} or s.get('version')!=1:raise ValueError('Unsupported opening record; original preserved.')
    facts=s.get('facts')
    if not isinstance(facts,list) or not facts or facts!=list(FACTS[:len(facts)]):raise ValueError('Invalid opening stage receipts.')
    if type(s.get('attempt')) is not int or not 0<=s['attempt']<=100000:raise ValueError('Invalid opening attempt.')
    if any(type(s.get(k)) is not bool for k in ('skipped','manifestRead')):raise ValueError('Invalid opening flag.')
    if ('opening_complete' not in facts)!=(current==AREA):raise ValueError('Opening location/stage disagree.')


def begin(world,room,skip=False):
    import adventure
    s=room['adventure']['opening']=dict(version=1,facts=list(FACTS) if skip else [FACTS[0]],attempt=0,skipped=skip,manifestRead=False)
    if not skip:
        adventure.enter(world,room,AREA,'south',initial=True)
        prepare(world,room)
        adventure.announce(world,room,'Hold the road! Get the wounded through the gate! Move now; hold attack. Defend while the crew loads the wagon.')
    return s


def environment():
    # Collision matches the drawn wagon bed and stone gateposts. No sealed
    # invisible boundary: the story exit is an explicit safe-muster trigger.
    return dict(stage=1,region='woodland',obstacles=[],zones=[],barriers=[
        dict(id='wagon-bed',x=440,y=380,width=95,height=48,material='wood',blocksShots=True),
        dict(id='gate-left',x=910,y=38,width=40,height=95,material='stone',blocksShots=True),
        dict(id='gate-right',x=1135,y=38,width=40,height=95,material='stone',blocksShots=True)])


def prepare(world,room):
    s=room['adventure']['opening'];room['adventure']['locked']=False
    room.update(phase='combat',enemies=[],projectiles=[],hazards=[],effects=[],environment=environment(),skillZones=[],skillHeals=[],skillEchoes=[])
    phase='withdrawal' if FACTS[3] in s['facts'] else 'second' if FACTS[1] in s['facts'] else 'arrival'
    room['_opening']=dict(phase=phase,startedAt=time.monotonic(),spawned=False,supportAt=0,support=0,eventAt=None,retry=False,creaked=False)
    for i,p in enumerate(room['players'].values()):
        p.update(x=1030+i*25 if phase=='withdrawal' else 620+i*32,y=170 if phase=='withdrawal' else 470,
                 dx=0,dy=0,attacking=False,reviving=None,lastMove=time.monotonic(),dialogue=None,townInterior=None,adventureTravel=None)


def spawn(world,room,second=False):
    from game import AFFINITIES,DIFFICULTIES
    import enemy_roles
    n=max(1,len(world._active_players(room)));scale=DIFFICULTIES[room['difficulty']]['multiplier']/1.25
    count=(3 if second else 2)+(n-1)
    sites=[(110,330),(240,600),(800,635),(150,540),(760,80),(180,180)] if not second else [(820,80),(1160,430),(140,480),(800,635),(180,180),(240,600)]
    for i in range(count):
        kind='serpent' if second and i==0 else 'wolf';x,y=sites[i]
        hp=round((48 if kind=='wolf' else 55)*(1+.16*(n-1))*scale)
        room['enemies'].append(dict(id='caravan-'+('flank' if second else 'road')+'-'+str(i),name='Displaced '+('Serpent' if kind=='serpent' else 'Wolf'),kind=kind,
            affinity='Nature',color=AFFINITIES['Nature'],baseColor='#85977a',x=x,y=y,hp=hp,maxHp=hp,
            damage=max(2,round(4*scale)),speed=68,attackRate=1,lastAttack=0,stunUntil=0,bleedUntil=0,bleedDamage=0,lastBleedTick=0,
            homeX=x,homeY=y,leashRadius=2000,aggroRadius=2000))
    enemy_roles.assign(room)
    room['_opening']['spawned']=True


def commit(world,room,fact):
    import adventure
    s=room['adventure']['opening']
    if fact not in s['facts']:
        if FACTS[len(s['facts'])]!=fact:raise ValueError('Opening transition out of order.')
        s['facts'].append(fact);adventure.save(world,room)


def complete(world,room):
    import adventure,progression
    s=room['adventure']['opening']
    if not active(room):return
    if FACTS[3] not in s['facts']:raise ValueError('The caravan has not reached safety.')
    # The location and all completion receipts commit together in one save.
    s['facts']=list(FACTS);room.pop('_opening',None)
    adventure.enter(world,room,'home','south');adventure.place_checkpoint(room)
    for p in world._voting_players(room):progression.start_dialogue(p,'caravan_aftermath')
    adventure.announce(world,room,'Caravan survivors reached Oakvale. Follow the missing hunter’s tracks on the Southern road; the manifest is an optional clue.')
    feedback.emit(room,'caravan_arrival',x=480,y=460)
    adventure.save(world,room)


def tick(world,room,now):
    if not active(room):return
    s=room['adventure']['opening'];r=room.get('_opening')
    if r is None:prepare(world,room);r=room['_opening']
    if r.get('retry'):return
    age=max(0,now-r['startedAt']);phase=r['phase']
    if phase=='arrival' and age>=3 and not r['creaked']:
        r['creaked']=True;feedback.emit(room,'caravan_creak',x=487,y=440)
    if phase=='arrival' and age>=8:
        r.update(phase='first',startedAt=now,spawned=False);phase='first';age=0
    if phase in ('first','second') and not r['spawned'] and age>=1.5:spawn(world,room,phase=='second')
    if phase=='first' and r['spawned'] and not room['enemies'] and age>=30:
        commit(world,room,FACTS[1]);r.update(phase='second',startedAt=now,spawned=False,support=0);phase='second';age=0
    if phase=='second' and age>=9 and FACTS[2] not in s['facts']:
        r['eventAt']=now;commit(world,room,FACTS[2]);feedback.emit(room,'caravan_impact',x=985,y=90)
        __import__('adventure').announce(world,room,'A dragon struck the distant watch! Keep the road clear while the wounded move.')
    if phase=='second' and r['spawned'] and not room['enemies'] and age>=35:
        commit(world,room,FACTS[3]);r.update(phase='withdrawal',startedAt=now,spawned=True);phase='withdrawal';age=0
        feedback.emit(room,'caravan_gate',x=MUSTER[0],y=MUSTER[1])
        __import__('adventure').announce(world,room,'Gate open! Gather at the gold muster circle. The exhausted defenders are withdrawing; keep everyone together.')
    # Exhausted guards fire only nearby, line-of-sight shots with a bounded total
    # budget. They support weaker starter kits; they cannot win either pack alone.
    if phase in ('first','second') and now>=r['supportAt'] and r['support']<28:
        import combat_environment as terrain
        guard=dict(x=650,y=340);target=next((e for e in room['enemies'] if math.dist((e['x'],e['y']),(guard['x'],guard['y']))<330 and terrain.line_clear(room,guard,e)),None)
        owner=next(iter(world._voting_players(room)),None)
        if owner and target:
            r.update(supportAt=now+2,support=r['support']+4)
            world._add_effect(room,'arrow',650,340,'#e8d8ad',target['x'],target['y'],duration=.2)
            world._damage_enemy(room,owner,target,4,direct=False)
    if phase=='withdrawal' and age>=20:
        humans=world._voting_players(room)
        if humans and all(p['status']=='alive' and math.dist((p['x'],p['y']),MUSTER)<=100 for p in humans):complete(world,room)


def wipe(world,room):
    import adventure
    r=room['_opening']
    if r.get('retry'):return
    world._dismiss_summons(room)
    for p in world._active_players(room):world._record_death(room,p)
    room.update(phase='defeat',enemies=[],projectiles=[],hazards=[],skillZones=[],skillHeals=[],skillEchoes=[])
    r['retry']=True;adventure.announce(world,room,'The road was overrun. Retry the unfinished caravan encounter. No Runes are lost; completed opening steps remain.')
    adventure.save(world,room)


def retry(world,room):
    import adventure
    if not active(room) or not room.get('_opening',{}).get('retry'):raise ValueError('No caravan retry is pending.')
    room['adventure']['opening']['attempt']+=1
    for p in room['players'].values():p.update(status='alive',hp=p['maxHp'],mana=p['maxMana'],deathRecorded=False)
    prepare(world,room);adventure.save(world,room)


def view(room):
    s=room.get('adventure',{}).get('opening')
    if not active(room):return None
    r=room.get('_opening',{});phase=r.get('phase','arrival');age=max(0,time.monotonic()-r.get('startedAt',time.monotonic()))
    texts={'arrival':'Hold the road! Move with WASD / arrows; hold attack. Wounded are being loaded.',
           'first':'Protect the wagon while the crew loads the wounded. Defeat the road attackers.',
           'second':'Cover the wounded. Stop the flanking creatures; the distant watch is under attack.',
           'withdrawal':'Reach the gold muster circle by the gate. All connected hunters must gather.'}
    delay=8-age if phase=='arrival' else 30-age if phase=='first' else 35-age if phase=='second' else 20-age
    return dict(phase=phase,objective=texts[phase],remaining=max(0,math.ceil(delay)),retry=r.get('retry',False),
        warning=phase in ('first','second') and not r.get('spawned'),watch=FACTS[2] in s['facts'],
        eventAge=max(0,time.monotonic()-r['eventAt']) if r.get('eventAt') is not None else None,
        muster=list(MUSTER),facts=s['facts'],manifestRead=s['manifestRead'],attempt=s['attempt'])
