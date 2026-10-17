"""Adventure-only active skills and small, bounded effect hooks."""
import math
import enemy_awareness
import time
import feedback
import telemetry
import combat_environment as terrain
import hero_skills as skills
import ability_animations
import boss_ai
import tactical_rules as tactical
KINDS={'ascend_'+h.lower() for h in ('Knight','Wizard','Archer','Cleric','Rogue','Druid','Bard','Healer')}|{'rush','banner','parry','barrier','triage','beacon','root_burst','rift','phase','trap','sidestep','mark',
       'sunburst','draft','hallowed','smoke','venom','crosscut','spring','call','refrain','echo','cadence'}


def distance(a,b):return math.hypot(a['x']-b['x'],a['y']-b['y'])
def shield(room,p,amount,seconds=6):
    if p['status']!='alive':return
    p['skillBarrier']=max(amount,p.get('skillBarrier',0) if p.get('barrierUntil',0)>time.monotonic() else 0)
    p['barrierUntil']=time.monotonic()+seconds;feedback.restored(room,p,'ward')
def heal(room,owner,p,amount):
    if p['status']!='alive':return
    actual=min(amount,p['maxHp']-p['hp']);p['hp']+=actual
    telemetry.add(room,owner['id'],'healingGiven',actual)
    if actual:feedback.restored(room,p,'heal',amount=actual,sourceId=owner['id'])
    if skills.rank(owner,'healer_overflow') and amount>actual:shield(room,p,min(12,amount-actual))
def ward(p,now,factor,seconds,owner):
    if p.get('wardUntil',0)<=now or factor<=p.get('wardFactor',1):p.update(wardUntil=now+seconds,wardFactor=factor,wardSource=owner['id'])
def base(p):
    from game import CLASSES
    return round((CLASSES[p['class']]['damage']*(1+.03*p.get('skillRanks',{}).get('power',0))+sum(i.get('damage',0) for i in p['toolSlots'] if i))*(p['damageBoost'] if p['damageBoostUntil']>time.monotonic() else 1)*(.75 if (p.get('curse') or {}).get('effect')=='weakened' else 1)*tactical.direct_factor(p,time.monotonic(),consume=False))
def foes(room,p,reach):return [e for e in room['enemies'] if distance(e,p)<=reach and terrain.line_clear(room,p,e)]
def allies(world,room,p,reach):return [m for m in world._active_players(room) if m['status']=='alive' and distance(m,p)<=reach and terrain.line_clear(room,p,m)]
def zone(room,p,kind,radius,seconds,**fields):
    now=time.monotonic()
    room.setdefault('skillZones',[]).append(dict(id=__import__('secrets').token_hex(5),ownerId=p['id'],kind=kind,x=p['x'],y=p['y'],radius=radius,startedAt=now,duration=seconds,expiresAt=now+seconds,nextHitAt=now,**fields))


def cast(world,room,p,a):
    if a['kind'].startswith('ascend_'):return __import__('ascension').cast(world,room,p,a)
    now=time.monotonic();kind=a['kind'];targets=foes(room,p,a['range']);team=allies(world,room,p,a['range'] or 320)
    target=min(team,key=lambda m:m['hp']/m['maxHp'],default=p)
    enemy=min(targets,key=lambda e:(e['id']!=p.get('preferredTarget'),distance(e,p)),default=None)
    if kind in ('root_burst','rift','sidestep','mark','sunburst','crosscut','echo') and not enemy:raise ValueError('No visible enemy is in range.')
    if kind in ('smoke','refrain') and not targets:raise ValueError('No visible enemy is close enough.')
    summons=[s for s in room.get('summons',[]) if s['ownerId']==p['id']]
    if kind=='call' and not summons:raise ValueError('Summon a companion before calling it back.')
    if kind=='triage' and target['hp']>=target['maxHp']:raise ValueError('No injured ally is within 320px.')
    if p['mana']<a['manaCost']:raise ValueError(f"{a['name']} needs {a['manaCost']} mana.")
    enemy_awareness.break_concealment(p,a['kind'])
    p['mana']-=a['manaCost'];p['abilityCooldowns'][a['id']]=now+a['cooldown'];skills.commit_cooldown(p,a['id'],now+a['cooldown'])
    p.update(animation='special',animationUntil=time.time()+.45)
    feedback.emit(room,'ability',actor=p,abilityId=a['id'],attackType='special',abilityKind=kind)
    origin=(p['x'],p['y'])
    if kind=='rush':
        length=max(.001,math.hypot(p['facingX'],p['facingY']));terrain.move(room,p,p['x']+100*p['facingX']/length,p['y']+100*p['facingY']/length)
        for e in list(foes(room,p,90)):world._stun(e,now);world._damage_enemy(room,p,e,round(base(p)*a['power']))
        shield(room,p,10,4)
    elif kind=='banner':zone(room,p,'banner',150,6)
    elif kind=='parry':p['parryUntil']=now+5
    elif kind=='barrier':shield(room,target,a['power'])
    elif kind=='triage':
        heal(room,p,target,18);room.setdefault('skillHeals',[]).append(dict(ownerId=p['id'],targetId=target['id'],ticks=6,nextHitAt=now+1))
    elif kind=='beacon':zone(room,p,'beacon',160,6)
    elif kind in ('root_burst','sunburst','smoke','refrain'):
        center=enemy if kind in ('root_burst','sunburst') else p
        for e in list(foes(room,center,95 if kind=='root_burst' else 100 if kind=='sunburst' else a['range'])):
            if not terrain.line_clear(room,p,e):continue
            if kind in ('root_burst','smoke'):root(e,now,1.6 if kind=='root_burst' else 1)
            elif kind=='sunburst':e['weakenUntil']=now+4
            elif kind=='refrain':world._stun(e,now);boss_ai.interrupt(world,room,e,now)
            world._damage_enemy(room,p,e,max(1,round(base(p)*a['power'])))
        if kind=='smoke':p['invisibleUntil']=now+2
    elif kind=='rift':zone(room,p,'rift',95,3,xTarget=enemy['x'],yTarget=enemy['y'],damage=round(base(p)*a['power']),pulses=3)
    elif kind in ('phase','sidestep','crosscut'):
        if kind=='crosscut':dx,dy=enemy['x']-p['x'],enemy['y']-p['y'];reach=min(160,max(0,math.hypot(dx,dy)-30))
        else:
            dx,dy=p['facingX'],p['facingY'];reach=120 if kind=='phase' else 80
            if kind=='sidestep':dx,dy=-dy,dx
        length=max(.001,math.hypot(dx,dy));terrain.move(room,p,p['x']+dx/length*reach,p['y']+dy/length*reach)
        if kind=='phase':shield(room,p,12,4)
        elif kind=='sidestep':world._launch_projectile(room,side='hero',owner_id=p['id'],target_id=enemy['id'],x=p['x'],y=p['y'],damage=round(base(p)*a['power']),color='#bfd99b',attack_class=p['class'],ability_id=a['id'],speed=360)
        else:
            for e in list(foes(room,p,95)):world._damage_enemy(room,p,e,round(base(p)*a['power']))
    elif kind=='trap':
        length=max(.001,math.hypot(p['facingX'],p['facingY']));x=p['x']+65*p['facingX']/length;y=p['y']+65*p['facingY']/length
        if not terrain.walkable(room,x,y) or not terrain.line_clear(room,p,dict(x=x,y=y)):x,y=p['x'],p['y']
        zone(room,p,'trap',55,8,xTarget=x,yTarget=y,damage=round(base(p)*a['power']))
    elif kind=='mark':p['skillMark']=dict(target=enemy['id'],hits=3);p['markUntil']=now+6
    elif kind=='draft':
        for m in team:m['mana']=min(m['maxMana'],m['mana']+12);m.update(speedBoost=1.25,speedBoostUntil=now+5)
    elif kind=='hallowed':zone(room,p,'hallowed',130,6)
    elif kind=='venom':p['venomHits']=3;p['venomUntil']=now+8
    elif kind=='spring':zone(room,p,'spring',130,6)
    elif kind=='call':
        for i,s in enumerate(summons):
            x,y=p['x']+(-28 if i%2 else 28),p['y']+28
            s['x'],s['y']=(x,y) if terrain.walkable(room,x,y) and terrain.line_clear(room,p,dict(x=x,y=y)) else (p['x'],p['y'])
            s['hp']=min(s['maxHp'],s['hp']+round(s['maxHp']*.2))
    elif kind=='echo':room.setdefault('skillEchoes',[]).append(dict(ownerId=p['id'],targetId=enemy['id'],releaseAt=now+.6,damage=round(base(p)*.9)))
    elif kind=='cadence':
        for m in team:m['cadenceUntil']=now+8
    else:raise ValueError('Unsupported active skill.')
    after_cast(room,p,a,now)
    recipients=team if kind in ('draft','cadence') else [target] if kind in ('barrier','triage') else []
    ability_animations.record(room,p,a,origin,(enemy['x'],enemy['y']) if enemy else (target['x'],target['y']),[m['id'] for m in recipients],facing=(enemy['x']-p['x'],enemy['y']-p['y']) if enemy else None)


def tick(world,room,now):
    __import__('ascension').tick(world,room,now)
    for z in list(room.get('skillZones',[])):
        owner=room['players'].get(z['ownerId'])
        if z['expiresAt']<=now or not owner or not owner.get('connected',True):room['skillZones'].remove(z);continue
        center=dict(x=z.get('xTarget',z['x']),y=z.get('yTarget',z['y']))
        if z['kind'] in ('trap','rift') and z['nextHitAt']<=now:
            targets=foes(room,center,z['radius'])
            if z['kind']=='trap' and targets:
                for e in list(foes(room,center,70)):root(e,now,1.2);world._damage_enemy(room,owner,e,z['damage'])
                z['expiresAt']=now
            elif z['kind']=='rift' and z['pulses']>0:
                for e in list(targets):world._damage_enemy(room,owner,e,z['damage'])
                z['pulses']-=1;z['nextHitAt']=now+1
        for p in world._active_players(room):
            if p['status']!='alive' or distance(z,p)>z['radius'] or not terrain.line_clear(room,z,p):continue
            if z['kind']=='banner':ward(p,now,.7,.15,owner)
            elif z['kind']=='beacon':
                p['beaconUntil']=now+.15
                if p.get('reviving'):ward(p,now,.65,.15,owner)
            elif z['kind']=='hallowed':ward(p,now,.7,.15,owner);p['rootUntil']=0
            elif z['kind']=='spring' and z['nextHitAt']<=now:heal(room,owner,p,3)
        if z['kind']=='spring' and z['nextHitAt']<=now:z['nextHitAt']=now+1
    for h in list(room.get('skillHeals',[])):
        p=room['players'].get(h['targetId']);owner=room['players'].get(h['ownerId'])
        if not p or not owner or p['status']!='alive' or not h['ticks']:room['skillHeals'].remove(h);continue
        if now>=h['nextHitAt']:heal(room,owner,p,4);h['ticks']-=1;h['nextHitAt']=now+1
    for echo in list(room.get('skillEchoes',[])):
        if now<echo['releaseAt']:continue
        room['skillEchoes'].remove(echo);p=room['players'].get(echo['ownerId']);e=next((e for e in room['enemies'] if e['id']==echo['targetId']),None)
        if p and e and p.get('connected',True) and p['status']=='alive' and distance(p,e)<=350 and terrain.line_clear(room,p,e):
            world._launch_projectile(room,side='hero',owner_id=p['id'],target_id=e['id'],x=p['x'],y=p['y'],damage=echo['damage'],color='#f095bf',attack_class='Bard',speed=300)


def incoming(world,room,p,enemy,amount,now):
    original=amount
    amount=__import__('ascension').incoming(p,amount,now)
    if enemy.get('ascWeakenUntil',0)>now:amount=round(amount*.8)
    if enemy.get('weakenUntil',0)>now:amount=round(amount*.7)
    if skills.rank(p,'knight_brace') and math.hypot(p.get('dx',0),p.get('dy',0))<.05 and p.get('braceReadyAt',0)<=now:
        amount=max(0,amount-6);p['braceReadyAt']=now+3
    if p.get('parryUntil',0)>now:
        p['parryUntil']=0;amount=max(0,amount-12)
        if enemy in room['enemies'] and distance(p,enemy)<=160 and terrain.line_clear(room,p,enemy):world._damage_enemy(room,p,enemy,base(p))
    if p.get('barrierUntil',0)>now:
        absorbed=min(amount,p.get('skillBarrier',0));p['skillBarrier']-=absorbed;amount-=absorbed
    telemetry.add(room,p['id'],'protectionGiven',original-amount)
    return amount


def dashed(room,p,now):
    if __import__('ascension').active(p):
        if p['class']=='Archer':shield(room,p,12,4)
        if p['class']=='Rogue':p['invisibleUntil']=max(p.get('invisibleUntil',0),now+.6)
    if skills.rank(p,'knight_pursuit') or skills.rank(p,'archer_escape'):p['steelUntil']=now+3
    if skills.rank(p,'wizard_phase'):shield(room,p,10,4)
    if skills.rank(p,'rogue_escape'):p['invisibleUntil']=max(p.get('invisibleUntil',0),now+1)
def outgoing(room,p,e,damage,summon,now):
    if not summon and p.get('steelUntil',0)>now:p['steelUntil']=0;damage+=10
    controlled=max(e.get('rootUntil',0),e.get('stunUntil',0))>now
    if not summon:
        if skills.rank(p,'archer_sight') and distance(p,e)>240:damage+=6
        if skills.rank(p,'rogue_opportunity') and controlled:damage+=6
        mark=p.get('skillMark',{})
        if p.get('markUntil',0)>now and mark.get('target')==e['id'] and mark.get('hits',0)>0:mark['hits']-=1;damage+=8
        if p.get('venomUntil',0)>now and p.get('venomHits',0)>0:
            p['venomHits']-=1;e.update(bleedOwner=p['id'],bleedUntil=now+5,bleedDamage=max(1,round(base(p)*.25)),lastBleedTick=now)
        gain=0
        if skills.rank(p,'wizard_control') and controlled and p.get('insightReadyAt',0)<=now:gain+=3;p['insightReadyAt']=now+2
        if skills.rank(p,'cleric_consecrate') and p.get('shardsReadyAt',0)<=now:gain+=2;p['shardsReadyAt']=now+3
        if skills.rank(p,'druid_roots') and e.get('rootUntil',0)>now and p.get('rootsReadyAt',0)<=now:gain+=3;p['rootsReadyAt']=now+3
        if p.get('cadenceUntil',0)>now and p.get('cadenceReadyAt',0)<=now:gain+=2;p['cadenceReadyAt']=now+1
        if p.get('backbeatUntil',0)>now:p['backbeatUntil']=0;gain+=6
        p['mana']=min(p['maxMana'],p['mana']+gain)
    return __import__('ascension').outgoing(room,p,e,damage,summon,now)
def killed(room,p,e,now):
    if __import__('ascension').active(p) and p['class']=='Rogue' and e.get('bleedUntil',0)>now and p.get('relentlessAt',0)<=now:p['mana']=min(p['maxMana'],p['mana']+6);p['relentlessAt']=now+3
    if skills.rank(p,'rogue_blood') and e.get('bleedUntil',0)>now and p.get('bloodReadyAt',0)<=now:heal(room,p,p,6);p['bloodReadyAt']=now+3
def revive_start(room,p,now):
    if __import__('ascension').active(p) and p['class']=='Healer' and p.get('safeReturnAt',0)<=now:shield(room,p,24);p['safeReturnAt']=now+8
    if (skills.rank(p,'healer_ward') or skills.rank(p,'cleric_rescue')) and p.get('watchReadyAt',0)<=now:shield(room,p,16);p['watchReadyAt']=now+8
def projectile(p,shot):
    a=skills.catalog(p).get(shot.get('abilityId'),{})
    for key in ('splashRadius','chainTargets','chainDecay','rootDuration'):
        if key in a:shot[{'splashRadius':'splash'}.get(key,key)]=a[key]
def revived(room,p,target):
    if __import__('ascension').active(p) and p['class']=='Healer':
        for m in (p,target):shield(room,m,25)
    if skills.rank(p,'knight_captain') or skills.rank(p,'bard_rescue'):
        for member in (p,target):shield(room,member,18)
    if skills.rank(p,'healer_rescue'):
        for member in (p,target):member['mana']=min(member['maxMana'],member['mana']+15)
    if skills.rank(p,'archer_rescue'):
        for m in room['players'].values():
            if m['status']=='alive' and distance(m,p)<=240:m.update(speedBoost=1.3,speedBoostUntil=time.monotonic()+4)


def root(e,now,seconds):
    if e.get('rootResistUntil',0)>now:return
    duration=min(.35,seconds) if e.get('boss') else seconds
    e.update(rootUntil=now+duration,rootResistUntil=now+max(1.8,duration))
def after_cast(room,p,a,now):
    __import__('ascension').after_cast(room,p,a,now)
    if a['attackType']=='light':return
    if a['kind'] in ('rush','root_burst','rift','sidestep','sunburst','smoke','crosscut','refrain','echo'):tactical.direct_factor(p,now,consume=True)
    if skills.rank(p,'wizard_reserve') and now-p.get('lastActiveCast',-100)>=4:p['mana']=min(p['maxMana'],p['mana']+6)
    if skills.rank(p,'bard_backbeat'):p['backbeatUntil']=now+4
    p['lastActiveCast']=now
def potion(world,room,p,kind):
    if kind=='heal' and __import__('ascension').active(p) and p['class']=='Cleric':
        for m in allies(world,room,p,240):shield(room,m,18)
    if kind=='heal':
        if skills.rank(p,'cleric_potion'):
            for m in allies(world,room,p,240):shield(room,m,12)
        if skills.rank(p,'druid_nourish'):
            for s in room.get('summons',[]):
                if s['ownerId']==p['id']:s['hp']=min(s['maxHp'],s['hp']+20)
    if kind=='mana' and skills.rank(p,'bard_encore'):
        for m in allies(world,room,p,240):
            if m['id']!=p['id']:m['mana']=min(m['maxMana'],m['mana']+8)
