"""Authored Adventure roles; existing species, committed tells and bounded pursuit."""
import math
import combat_environment as terrain

HINTS={
 'defender':'Rootguard · front guard; flank it or separate it from nearby allies.',
 'channeler':'Channeler · break concentration with direct hits or a stun during the marked cast.',
 'flanker':'Flanker · commits to a side approach; move away from its marked pounce.',
}
LAYOUTS={
 'camp':{'camp_guards':('defender',)},
 'mill_trail':{'wheel-road':('channeler',)},
 'hollow':{'hollow-shrine-flank':('flanker',)},
 'watch':{'watch-shrine':('defender',)},
 'fields':{'ditch-stalkers':('flanker',),'granary-guards':('channeler',)},
 'mill':{'mill-approach-flank':('defender',)},
 'sluice_gallery':{'*':('defender','channeler','flanker')},
}


def enemy(world,room,key,kind,role,x,y):
    import adventure
    from game import DIFFICULTIES,AFFINITIES
    danger=adventure.AREAS[room['adventure']['current']]['danger'];n=max(1,len(world._active_players(room)))
    scale=DIFFICULTIES[room['difficulty']]['multiplier']/1.25;hp=round((36+danger*7)*(1+.16*(n-1))*scale)
    return dict(id=key,name={'troll':'Rootguard','serpent':'Root Channeler','wolf':'Woodland Flanker'}[kind],kind=kind,combatRole=role,
        **{'class':{'defender':'Knight','channeler':'Wizard','flanker':'Rogue'}[role]},affinity='Nature',color=AFFINITIES['Nature'],baseColor='#85977a',
        x=x,y=y,homeX=x,homeY=y,hp=hp,maxHp=hp,damage=max(2,round((4+danger)*scale)),speed=68+danger*2,attackRate=1,
        boss=False,bossPhase=1,group='oath-trial',aggroRadius=190,leashRadius=260,lastAttack=0,stunUntil=0,bleedUntil=0,bleedDamage=0,lastBleedTick=0)


def assign(room,area):
    choices=LAYOUTS.get(area,{})
    for group,roles in choices.items():
        members=sorted((e for e in room['enemies'] if (group=='*' or e.get('group')==group) and not any(e.get(k) for k in ('boss','miniBoss','structure'))),key=lambda e:e['id'])
        for e,role in zip(members,roles):
            e.update(combatRole=role,**{'class':{'defender':'Knight','channeler':'Wizard','flanker':'Rogue'}[role]})


def damage_factor(room,enemy,source,now):
    if enemy.get('boss') or enemy.get('structure'):return 1
    def frontal(guard):
        dx,dy=source['x']-guard['x'],source['y']-guard['y'];fx,fy=guard.get('guardFacing',[0,1])
        return (dx*fx+dy*fy)/max(.001,math.hypot(dx,dy))>.45
    if enemy.get('combatRole')=='defender' and enemy.get('roleRecoverUntil',0)<=now and frontal(enemy):return .6
    for guard in room['enemies']:
        if guard is enemy or guard.get('combatRole')!='defender' or guard.get('roleRecoverUntil',0)>now:continue
        if math.dist((enemy['x'],enemy['y']),(guard['x'],guard['y']))<100 and frontal(guard) and terrain.line_clear(room,guard,enemy):return .8
    return 1


def interrupt(enemy,now,damage=0,stun=False):
    attack=enemy.get('roleAttack')
    if not attack or not attack.get('interruptible') or enemy.get('channelResistUntil',0)>now:return False
    attack['concentrationDamage']=attack.get('concentrationDamage',0)+max(0,damage)
    if not stun and attack['concentrationDamage']<max(8,enemy['maxHp']*.12):return False
    enemy.pop('roleAttack',None);enemy.update(roleRecoverUntil=now+1.8,roleReadyAt=now+4,channelResistUntil=now+6,moving=False)
    enemy['interruptedUntil']=now+1.2
    return True


def tick(world,room,e,target,now,dt):
    import enemy_roles,boss_ai
    role=e['combatRole'];e['moving']=False
    if e.get('roleRecoverUntil',0)>now:return
    pending=e.get('roleAttack')
    if pending:
        if now<pending['releaseAt']:return
        e.pop('roleAttack');e['animationUntil']=__import__('time').time()+.35
        if role=='channeler':
            fire=e.get('archetype')=='fire_saboteur'
            boss_ai.area(room,e,pending['x'],pending['y'],now,radius=72,delay=0,duration=3 if fire else .25,power=.65 if fire else 1.1,kind='fire pot' if fire else 'root pulse')
        elif role=='defender':
            for actor in world._combat_targets(room):
                if actor['status']=='alive' and math.dist((actor['x'],actor['y']),(pending['x'],pending['y']))<45 and terrain.line_clear(room,e,actor):world._damage_player(room,e,actor,e['damage'])
        else:
            # A committed pounce cannot follow a last-second sidestep or cross a wall.
            terrain.move(room,e,pending['x'],pending['y'])
            for actor in world._combat_targets(room):
                if actor['status']=='alive' and math.dist((actor['x'],actor['y']),(e['x'],e['y']))<45 and terrain.line_clear(room,e,actor):world._damage_player(room,e,actor,e['damage'])
        e['roleRecoverUntil']=now+(1.2 if role!='channeler' else .8);e['moveDecisionAt']=0
        return
    if not e.get('allowAcquire',True):return
    distance=math.dist((e['x'],e['y']),(target['x'],target['y']))
    if role=='defender' and now>=e.get('guardFaceAt',0):
        length=max(.001,distance);e['guardFacing']=[(target['x']-e['x'])/length,(target['y']-e['y'])/length];e['guardFaceAt']=now+.9
    e['facingX'],e['facingY']=target['x']-e['x'],target['y']-e['y']
    reach={'defender':80,'channeler':250,'flanker':135}[role]
    if distance>reach or not terrain.line_clear(room,e,target):
        if role=='flanker' and now>=e.get('moveDecisionAt',0):
            dx,dy=target['x']-e['x'],target['y']-e['y'];length=max(.001,distance);side=1 if sum(map(ord,e['id']))%2 else -1
            e.update(moveGoal=[target['x']-dy/length*90*side,target['y']+dx/length*90*side],moveDecisionAt=now+.9)
        before=e['x'],e['y'];enemy_roles.approach(room,e,target,now,dt,165 if role=='channeler' else 40);e['moving']=math.dist(before,(e['x'],e['y']))>.1
        return
    if now<e.get('roleReadyAt',0):return
    delay={'defender':.85,'channeler':1.4,'flanker':.8}[role]
    x,y=target['x'],target['y']
    if role=='flanker':
        length=max(1,distance);scale=min(1,120/length);x=e['x']+(x-e['x'])*scale;y=e['y']+(y-e['y'])*scale
    e['roleAttack']=dict(kind=role,x=x,y=y,targetId=target['id'],startedAt=now,releaseAt=now+delay,
        interruptible=role=='channeler' and e.get('channelResistUntil',0)<=now,radius=72 if role=='channeler' else 45)
    e['roleReadyAt']=now+{'defender':3.3,'channeler':6,'flanker':3.7}[role]
