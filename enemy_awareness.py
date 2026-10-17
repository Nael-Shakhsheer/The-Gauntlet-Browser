"""Transient, server-owned perception. Never use hidden actors as live aims."""
import math
import combat_environment as terrain

STATES={'unaware','investigating','alert','searching','returning'}
SEARCH_SECONDS=3.0


def visible(actor,now):
    return actor.get('status')=='alive' and actor.get('connected',True) and not actor.get('townInterior') and actor.get('invisibleUntil',0)<=now


def committed(e,now):
    return bool(e.get('pendingAttack') or e.get('roleAttack') or e.get('chargeUntil',0)>now or e.get('roleChargeUntil',0)>now)


def change(e,state,now):
    if e.get('awareness')==state:return
    old=e.get('awareness','unaware');e.update(awareness=state,awarenessAt=now)
    if state=='alert' and old!='alert':e.update(awarenessCue='!',awarenessCueUntil=now+1.1)
    elif state=='searching':e.update(awarenessCue='?',awarenessCueUntil=now+1.5)


def location(e):
    x,y=e.get('lastKnown',[e['x'],e['y']])
    return dict(id='last-known',x=x,y=y,status='alive',dx=0,dy=0)


def choose(world,room,e,now):
    e['_awarenessTick']=now;e['allowAcquire']=False
    e.setdefault('homeX',e['x']);e.setdefault('homeY',e['y'])
    outdoor=bool(room.get('adventure') and not room['adventure'].get('locked') and not __import__('dungeons').inside(room) and not __import__('opening').active(room))
    radius=e.get('aggroRadius',170) if outdoor else 650
    leash=e.get('leashRadius',245) if outdoor else 2000
    home=dict(x=e['homeX'],y=e['homeY'])
    actors=world._combat_targets(room)
    # Invisibility, disconnection and downing invalidate immediately, including taunts.
    candidates=[p for p in actors if visible(p,now) and math.dist((p['x'],p['y']),(home['x'],home['y']))<=leash and
                math.dist((p['x'],p['y']),(e['x'],e['y']))<=(leash if e.get('awareness')=='alert' else radius) and terrain.line_clear(room,e,p)]
    if math.dist((e['x'],e['y']),(home['x'],home['y']))>leash:candidates=[]
    target=min(candidates,key=lambda p:(p.get('tauntUntil',0)<=now,p['id']!=e.get('targetId'),math.dist((p['x'],p['y']),(e['x'],e['y']))),default=None)
    if target:
        e['lastKnown']=[target['x'],target['y']];e['lastSeenAt']=now
        if e.get('awareness','unaware') in ('unaware','returning'):
            change(e,'investigating',now)
        if now-e.get('awarenessAt',now)>=.25 or e.get('awareness') in ('alert','searching') or e.get('aggro') or not room.get('adventure'):
            change(e,'alert',now);e.update(aggro=True,returning=False,allowAcquire=True)
            for human in room['players'].values():
                if human.get('connected',True) and not human.get('bot') and math.dist((human['x'],human['y']),(e['x'],e['y']))<=450:
                    human['combatParticipationAt']=now
            return target
    elif e.get('awareness') in ('alert','investigating'):
        change(e,'searching',now);e.update(aggro=False,searchUntil=now+SEARCH_SECONDS,moveDecisionAt=0,bossMoveAt=0)
    # An announced attack resolves against recorded coordinates, even after detection loss.
    if committed(e,now):return location(e)
    if max(e.get('recoverUntil',0),e.get('roleRecoverUntil',0))>now:e['moving']=False;return None
    dt=min(.1,max(0,now-e.get('lastAiTick',now-.05)));e['lastAiTick']=now
    state=e.get('awareness','unaware')
    if state=='searching' and now>=e.get('searchUntil',now):change(e,'returning',now);state='returning'
    goal=e.get('lastKnown') if state in ('searching','investigating') else [home['x'],home['y']]
    if state in ('searching','investigating','returning') and goal:
        dx,dy=goal[0]-e['x'],goal[1]-e['y'];distance=math.hypot(dx,dy)
        old=(e['x'],e['y']);step=min(distance,e['speed']*dt)
        if distance:terrain.move(room,e,e['x']+dx/distance*step,e['y']+dy/distance*step,avoid=True)
        e['moving']=math.dist(old,(e['x'],e['y']))>.1
        e['returning']=state=='returning'
        if state=='returning' and distance<12:e['returning']=False;change(e,'unaware',now)
    else:e['moving']=False
    return None


def attacked(e,p,now):
    # Taking a hit creates suspicion of its recorded origin, never secret tracking.
    e['lastKnown']=[p['x'],p['y']]
    if visible(p,now):e['aggro']=True;change(e,'alert',now)
    else:change(e,'searching',now);e['searchUntil']=now+SEARCH_SECONDS


def break_concealment(p,kind):
    # Successful offensive casts break Vanish/smoke. Dash concealment is still
    # granted by its existing modifiers; ongoing bleed/summons do not break it.
    if kind in {'damage','stun','bleed','dash_strike','pierce','area','target_area','rush','root_burst','rift','trap','sunburst','venom','crosscut','ascend_rogue'}:
        p['invisibleUntil']=0
