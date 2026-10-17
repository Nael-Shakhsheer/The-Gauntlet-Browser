"""Adventure Ascension: finite purchased state, eight real signatures and passives.

No second skill-point ledger: the purchased character state owns this kit. Class
changes select the new kit; recharge is still governed by the normal action slot.
"""
import math
import enemy_awareness
import time
import copy

SPECS={
 'Knight':('citadel_oath','Citadel Oath',24,34,150,2.5,'Commit a 0.6s strike around you (2.5× weapon damage, 150px). Nearby allies gain a 30-point barrier and 25% protection for 6s.','guardian_cry',
   [('Bastion','While a barrier is active, incoming hits lose 4 damage.'),('Committed steel','Direct hits against rooted or stunned foes deal 6 extra damage.')]),
 'Wizard':('astral_convergence','Astral Convergence',20,38,360,2.4,'Mark a selected 120px cluster within 360px. After 0.6s it takes 2.4× weapon damage and a 1.6s root; bosses resist control.','arcane_cataclysm',
   [('Elemental fracture','Direct hits against rooted or stunned foes deal 5 extra damage.'),('Arcane economy','Non-basic casts restore 3 mana, at most once per 4s.')]),
 'Archer':('horizon_arrow','Horizon Arrow',18,30,460,3,'Commit a narrow line toward your target: after 0.6s all visible foes within 460px and 38px of that line take 3× weapon damage. Walls block it.','deadeye',
   [('Farshot','Direct hits beyond 240px deal 6 extra damage.'),('Mobile cover','A successful dash grants a 12-point barrier for 4s.')]),
 'Cleric':('dawn_mixture','Dawn Mixture',22,34,300,1.7,'Mark a selected foe, or yourself. After 0.6s a 140px sacred mixture deals 1.7× weapon damage, heals allies 14, cleanses roots and grants an 18-point barrier.','sunburst_flask',
   [('Sacred residue','A direct hit weakens its target’s attacks by 20% for 2s, once per 3s.'),('Prepared mixtures','Healing consumables also grant nearby allies an 18-point barrier.')]),
 'Rogue':('shadow_circuit','Shadow Circuit',18,28,250,2.2,'Lunge up to 120px toward a visible target without crossing walls. After 0.6s strike foes within 140px for 2.2× weapon damage; gain 1.5s concealment.','crosscut',
   [('Escape route','A successful dash grants 0.6s concealment.'),('Relentless hunt','Killing a bleeding foe restores 6 mana, at most once per 3s.')]),
 'Druid':('elder_accord','Elder Accord',22,32,220,1.2,'After 0.6s root visible foes within 220px for 1.6s and deal 1.2× weapon damage. Restore 30 HP to owned summons and empower their damage by 25% for 6s.','call_wild',
   [('Elder companions','All new summons have 35 extra maximum HP; death recharge is unchanged.'),('Kindred return','Summon hits heal you 2 HP, at most once per 2s.')]),
 'Bard':('harmonic_march','Harmonic March',22,32,250,1.6,'After 0.6s interrupt nearby enemies and deal 1.6× weapon damage in 250px. Nearby allies gain 30% movement speed and 25% protection for 6s.','grand_crescendo',
   [('Sheltering rhythm','Non-basic casts grant nearby allies an 8-point barrier, at most once per 4s.'),('Steady tempo','Your direct hits restore 2 mana, at most once per 3s.')]),
 'Healer':('second_dawn','Second Dawn',28,42,220,0,'After 0.6s rescue the nearest visible downed ally within 220px at 35% HP. Otherwise heal the lowest-health nearby ally for 25. The recipient gains a 45-point barrier for 6s.','quick_revival',
   [('Emergency veil','Below 30% HP, reduce an incoming hit by 8, at most once per 10s.'),('Safe return','Starting a rescue grants a 24-point barrier; completed rescues grant both heroes a 25-point barrier.')]),
}


def active(p):return bool(p.get('magicRunes',{}).get('ascended'))

def ability(p):
    aid,name,cd,mana,reach,power,text,icon,_=SPECS[p['class']]
    return dict(id=aid,name=name,cooldown=cd,manaCost=mana,range=reach,power=power,description=text,iconKey=icon,attackType='special',kind='ascend_'+p['class'].lower())

def nodes(p):
    a=ability(p);owned=active(p)
    result=[dict(id=a['id'],name=a['name'],branch='Ascension',type='ability',cost=0,maxRank=1,requires=[],effects=[a['description']],starter=True,
      rank=int(owned),unlocked=owned,equipped=a['id'] in p['abilities'],current=a)]
    for i,(name,text) in enumerate(SPECS[p['class']][-1]):result.append(dict(id='ascended_passive_'+str(i+1),name=name,branch='Ascension',type='passive',cost=0,maxRank=1,requires=[],effects=[text],starter=True,rank=int(owned),unlocked=owned,equipped=False,current=None))
    return result


def cast(world,room,p,a):
    import combat_environment as terrain,skill_casts as s,hero_skills,feedback
    if not active(p):raise ValueError('Ascend with 15 unspent Magic Runes before using this signature.')
    now=time.monotonic();targets=s.foes(room,p,a['range']);enemy=min(targets,key=lambda e:(e['id']!=p.get('preferredTarget'),s.distance(p,e)),default=None)
    if p['class'] in ('Wizard','Archer','Rogue') and not enemy:raise ValueError('No visible enemy is in range.')
    if p['mana']<a['manaCost']:raise ValueError(a['name']+' requires '+str(a['manaCost'])+' mana.')
    enemy_awareness.break_concealment(p,a['kind'])
    p['mana']-=a['manaCost'];p['abilityCooldowns'][a['id']]=now+a['cooldown'];hero_skills.commit_cooldown(p,a['id'],now+a['cooldown'])
    if p['class']=='Rogue':
        dx,dy=enemy['x']-p['x'],enemy['y']-p['y'];length=max(1,math.hypot(dx,dy));reach=min(120,max(0,length-30))
        terrain.move(room,p,p['x']+dx/length*reach,p['y']+dy/length*reach)
    center=enemy if p['class'] in ('Wizard','Cleric') and enemy else p
    radius=120 if p['class']=='Wizard' else 140 if p['class'] in ('Rogue','Cleric') else a['range']
    direction=None
    if p['class']=='Archer':
        length=max(1,s.distance(p,enemy));direction=[(enemy['x']-p['x'])/length,(enemy['y']-p['y'])/length]
    room.setdefault('ascensionCasts',[]).append(dict(ownerId=p['id'],hero=p['class'],x=center['x'],y=center['y'],origin=[p['x'],p['y']],radius=radius,direction=direction,releaseAt=now+.6,ability=copy.deepcopy(a)))
    p.update(animation='special',animationUntil=time.time()+.6)
    feedback.emit(room,'ability',actor=p,abilityId=a['id'],attackType='special',abilityKind=a['kind'])
    motion=__import__('ability_animations').record(room,p,a,(p['x'],p['y']),(center['x'],center['y']),[],
        release_after=.6,visual=dict(shape='line' if direction else 'rescue' if p['class']=='Healer' else 'circle',
            family=__import__('ability_visuals').ASCENDED[p['class']],center=[center['x'],center['y']],radius=radius,direction=direction,width=38 if direction else None,origin=[p['x'],p['y']],los=True),
        facing=(enemy['x']-p['x'],enemy['y']-p['y']) if enemy else None)
    room['ascensionCasts'][-1]['presentationId']=motion['id']
    s.after_cast(room,p,a,now)


def tick(world,room,now):
    import skill_casts as s,combat_environment as terrain,boss_ai
    for c in list(room.get('ascensionCasts',[])):
        if now<c['releaseAt']:continue
        room['ascensionCasts'].remove(c);p=room['players'].get(c['ownerId'])
        if not p:continue
        if not active(p) or p['class']!=c['hero'] or p['status']!='alive' or not p.get('connected',True):
            __import__('ability_animations').resolve(room,p,c.get('presentationId'),now,cancelled=True)
            continue
        a=c['ability'];hero=p['class'];center=dict(x=c['x'],y=c['y'])
        origin=dict(x=c['origin'][0],y=c['origin'][1])
        if not terrain.line_clear(room,p,center):
            __import__('ability_animations').resolve(room,p,c.get('presentationId'),now,cancelled=True)
            continue
        targets=s.foes(room,center,c['radius'])
        if hero=='Archer':
            dx,dy=c['direction'];targets=[]
            for e in room['enemies']:
                ex,ey=e['x']-origin['x'],e['y']-origin['y'];along=ex*dx+ey*dy
                if 0<=along<=a['range'] and abs(ex*dy-ey*dx)<=38 and terrain.line_clear(room,origin,e):targets.append(e)
        for e in list(targets):
            if not terrain.line_clear(room,p,e):continue
            if hero in ('Wizard','Druid'):s.root(e,now,1.6)
            if hero in ('Knight','Bard'):world._stun(e,now);boss_ai.interrupt(world,room,e,now)
            if a['power']:world._damage_enemy(room,p,e,round(s.base(p)*a['power']))
        team=[m for m in world._active_players(room) if m['status']=='alive' and s.distance(m,center)<=(140 if hero=='Cleric' else max(140,a['range'])) and terrain.line_clear(room,center,m)]
        if hero=='Knight':
            for m in team:s.shield(room,m,30);s.ward(m,now,.75,6,p)
        elif hero=='Cleric':
            for m in team:s.heal(room,p,m,14);s.shield(room,m,18);m['rootUntil']=0
        elif hero=='Rogue':p['invisibleUntil']=max(p.get('invisibleUntil',0),now+1.5)
        elif hero=='Druid':
            p['elderAccordUntil']=now+6
            for summon in room.get('summons',[]):
                if summon['ownerId']==p['id']:summon['hp']=min(summon['maxHp'],summon['hp']+30)
        elif hero=='Bard':
            for m in team:m.update(speedBoost=1.3,speedBoostUntil=now+6);s.ward(m,now,.75,6,p)
        elif hero=='Healer':
            down=[m for m in world._active_players(room) if m['status'] in ('downed','fallen') and s.distance(m,center)<=220 and terrain.line_clear(room,center,m)]
            target=min(down,key=lambda m:s.distance(m,center),default=None)
            if target:world._restore_ally(room,p,target,.35)
            else:target=min(team,key=lambda m:m['hp']/m['maxHp'],default=p);s.heal(room,p,target,25)
            s.shield(room,target,45)
        recipients=[target['id']] if hero=='Healer' else [m['id'] for m in team] if hero in ('Knight','Cleric','Bard') else []
        __import__('ability_animations').resolve(room,p,c.get('presentationId'),now,recipients=recipients)
        __import__('feedback').emit(room,'ascended_release',actor=p,abilityId=a['id'],castId=c.get('presentationId'),
            targetX=center['x'],targetY=center['y'],origin=c['origin'],radius=c['radius'],direction=c['direction'],recipientIds=recipients)


def outgoing(room,p,e,damage,summon,now):
    if not active(p):return damage
    damage=round(damage*1.08)
    import skill_casts as s
    hero=p['class'];controlled=max(e.get('rootUntil',0),e.get('stunUntil',0))>now
    if hero=='Druid' and summon:
        if p.get('elderAccordUntil',0)>now:damage=round(damage*1.25)
        if p.get('kindredReturnAt',0)<=now:s.heal(room,p,p,2);p['kindredReturnAt']=now+2
    if summon:return damage
    if controlled and hero in ('Knight','Wizard'):damage+=6 if hero=='Knight' else 5
    if hero=='Archer' and s.distance(p,e)>240:damage+=6
    if hero=='Cleric' and p.get('sacredResidueAt',0)<=now:e['ascWeakenUntil']=now+2;p['sacredResidueAt']=now+3
    if hero=='Bard' and p.get('steadyTempoAt',0)<=now:p['mana']=min(p['maxMana'],p['mana']+2);p['steadyTempoAt']=now+3
    return damage


def incoming(p,amount,now):
    if not active(p):return amount
    if p['class']=='Knight' and p.get('barrierUntil',0)>now:amount=max(0,amount-4)
    if p['class']=='Healer' and p['hp']<=p['maxHp']*.3 and p.get('emergencyVeilAt',0)<=now:amount=max(0,amount-8);p['emergencyVeilAt']=now+10
    return amount


def after_cast(room,p,a,now):
    if not active(p) or a['attackType']=='light':return
    import skill_casts as s
    if p['class']=='Wizard' and p.get('arcaneEconomyAt',0)<=now:p['mana']=min(p['maxMana'],p['mana']+3);p['arcaneEconomyAt']=now+4
    if p['class']=='Bard' and p.get('shelteringRhythmAt',0)<=now:
        for m in room['players'].values():
            if m['status']=='alive' and s.distance(m,p)<=240 and __import__('combat_environment').line_clear(room,p,m):s.shield(room,m,8)
        p['shelteringRhythmAt']=now+4
