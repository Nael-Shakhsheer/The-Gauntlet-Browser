"""Distinct commander commitments and finite archmage/dragon phases."""
import math
import time

PATTERNS={
 'city_breach':('charge','slam'),'breach_captain':('slam','charge'),
 'city_knight':('charge','rocks','charge','slam'),
 'city_mage':('arcane_cross','pool','volley'),
 'city_archer':('volley','pool','volley'),
 'veil_archmage':('arcane_cross','pool','volley'),
 'ravine_keeper':('charge','rocks','slam'),
 'summit_warden':('raise_cover','rocks','shatter','slam'),
}
def identity(e):return e.get('archetype') or e['id'].removeprefix('exp-')
def pattern(e):
    key=identity(e)
    if key=='cinder_dragon':return ('breath','slam','volley','charge') if e.get('bossPhase',1)==1 else ('fire_trail','breath','meteor','charge') if e.get('bossPhase')==2 else ('meteor','breath','fire_trail','volley','slam')
    return PATTERNS.get(key)

def interrupt(world,room,e,now,damage=0):
    if identity(e) not in ('city_mage','veil_archmage'):return False
    pending=e.get('pendingAttack')
    if not pending or e.get('campaignChannelResist',0)>now:return False
    pending['concentrationDamage']=pending.get('concentrationDamage',0)+max(0,damage)
    if e.get('stunUntil',0)<=now and pending['concentrationDamage']<e['maxHp']*.08:return False
    e.pop('pendingAttack',None);e.update(recoverUntil=now+2,nextBossAttack=now+3,campaignChannelResist=now+6,interruptedUntil=now+1.2)
    room['hazards']=[h for h in room['hazards'] if h['ownerId']!=e['id'] or h['activatesAt']<=now]
    __import__('feedback').emit(room,'interrupt',x=e['x'],y=e['y']);return True

def tick(world,room,e,now):
    import adventure,combat_environment as terrain
    key=identity(e)
    dt=min(.1,max(0,now-e.get('campaignLastTick',now-.05)));e['campaignLastTick']=now
    if key=='city_archer' and not e.get('pendingAttack'):
        index=e.get('attackIndex',0)
        if index and e.get('campaignShotIndex')!=index:
            e['campaignShotIndex']=index;e['campaignRepositionUntil']=now+1.3
            candidates=[adventure.point(room,*p) for p in ((260,190),(730,210),(480,410))]
            clear=[p for p in candidates if terrain.walkable(room,*p) and terrain.line_clear(room,e,dict(x=p[0],y=p[1]))]
            if clear:e['campaignRepositionGoal']=max(clear,key=lambda p:math.dist(p,(e['x'],e['y'])))
        goal=e.get('campaignRepositionGoal')
        if goal and now<e.get('campaignRepositionUntil',0):
            dx,dy=goal[0]-e['x'],goal[1]-e['y'];d=max(1,math.hypot(dx,dy));step=min(d,100*dt)
            terrain.move(room,e,e['x']+dx/d*step,e['y']+dy/d*step,avoid=True);e['moving']=True;return True
    if key=='veil_archmage':
        phase=e.get('bossPhase',1)
        if phase<3 and e['hp']<=e['maxHp']*(.66 if phase==1 else .33):
            e['bossPhase']=phase+1;e.update(nextBossAttack=now+3,recoverUntil=now+2)
            for i,(cx,cy) in enumerate(((400,330),(560,330))):
                x,y=adventure.point(room,cx,cy);hp=round(55*(1+.25*(len(world._active_players(room))-1)))
                room['enemies'].append(dict(id='exp-veil-device-'+str(phase)+'-'+str(i),name='Siphon focus · shields Orath',kind='troll',structure=True,
                    affinity='Arcane',color='#b3a1d5',baseColor='#b3a1d5',x=x,y=y,hp=hp,maxHp=hp,damage=0,speed=0,attackRate=1,boss=False,group='archmage-devices'))
            adventure.announce(world,room,'Orath draws on the siphon foci. Break the two visible devices to remove his protection; his channels can be interrupted.')
    if key=='cinder_dragon':
        if e.get('bossPhase')==2 and e['hp']<=e['maxHp']*.4:
            e.update(bossPhase=3,damage=round(e['damage']*1.15),attackRate=e['attackRate']*1.1,nextBossAttack=now+2.5,recoverUntil=now+2)
            adventure.announce(world,room,'The Crownfire Dragon enters its final fury. Familiar breath lanes and marked impacts return faster, with recovery after each commitment.')
        index=e.get('attackIndex',0)
        if index and index%4==0 and e.get('campaignFlightIndex')!=index and not e.get('pendingAttack'):
            e['campaignFlightIndex']=index;e['flyingUntil']=now+1.5;e['nextBossAttack']=max(e.get('nextBossAttack',0),now+1.8)
            w,h=terrain.dimensions(room);candidates=[(w*.35,h*.32),(w*.7,h*.35),(w*.65,h*.68)]
            clear=[p for p in candidates if terrain.walkable(room,*p) and terrain.line_clear(room,e,dict(x=p[0],y=p[1]))]
            if clear:e['campaignFlightGoal']=max(clear,key=lambda p:math.dist(p,(e['x'],e['y'])))
            adventure.announce(world,room,'Dragon flyover · it remains vulnerable. Watch the next landing and breath warning.')
        goal=e.get('campaignFlightGoal')
        if goal and e.get('flyingUntil',0)>now:
            dx,dy=goal[0]-e['x'],goal[1]-e['y'];length=max(1,math.hypot(dx,dy));step=min(length,220*dt)
            terrain.move(room,e,e['x']+dx/length*step,e['y']+dy/length*step,avoid=True)
            e['moving']=True;return True

def damage_factor(room,e):
    return .55 if identity(e)=='veil_archmage' and any(a['id'].startswith('exp-veil-device-') for a in room['enemies']) else 1

def tactic(e):
    return {'city_knight':'Bait a committed charge into cover; attack during recovery.',
        'city_mage':'Break concentration during the marked channel. Use pillars against projectiles.',
        'city_archer':'Cross its marked shot lane, use cover and punish the reposition.',
        'veil_archmage':'Break siphon foci at66%/33%, interrupt channels and attack during recovery.',
        'cinder_dragon':'Dodge committed ground strikes and directional breath. Flyovers remain damageable; final fury remixes those attacks.'}.get(identity(e))
