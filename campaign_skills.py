"""Forty authored Adventure nodes; mechanics first, stable IDs for sprite work."""
import copy
import math
import re
import secrets
import time

# id, name, range, cooldown, mana, power, shape, secondary mechanic, description
ACTIVES={
 'Knight':[
 ('formation_break','Formation Break',235,12,24,1.25,'line','push','Strike a 65px-wide235px lane. Push ordinary foes65px; bosses instead receive a0.35s root.'),
 ('oath_link','Oath Link',240,18,30,0,'allies','link','Allies within240px receive24 barrier for6s. Those within100px also receive25% protection for4s.'),
 ('citadel_fall','Citadel Fall',260,32,55,3.0,'line','ward','Strike a100px-wide260px lane for3× weapon damage; gain30 barrier for6s.')],
 'Wizard':[
 ('ember_seam','Ember Seam',330,12,24,.55,'field','burn','Mark a95px circle at a visible foe within330px. Three1s pulses each deal0.55× weapon damage.'),
 ('prism_fracture','Prism Fracture',300,16,29,1.0,'line','root','Strike a70px-wide300px lane. Root ordinary foes1.5s and weaken their damage30% for3s; bosses resist root.'),
 ('star_corridor','Star Corridor',400,34,58,1.15,'field','arc','At a visible foe within400px, three115px pulses each deal1.15× weapon damage. Pulses stun ordinary foes briefly.')],
 'Archer':[
 ('pinning_line','Pinning Line',370,11,20,1.1,'line','root','Fire through a50px-wide370px lane. Each visible foe takes1.1× weapon damage and a short root.'),
 ('snare_exchange','Snare Exchange',240,14,24,.8,'move','trap','Move90px backwards through clear ground, leaving a90px snare field for3 pulses; each deals0.8× weapon damage and roots.'),
 ('arrow_corridor','Arrow Corridor',410,32,52,1.3,'field','arrows','Commit three110px arrow impacts at a selected visible cluster within410px, each1.3× weapon damage.')],
 'Cleric':[
 ('purging_salve','Purging Salve',300,12,23,1.0,'target','cleanse','A visible target within300px anchors a100px mixture burst. Foes take weapon damage; living allies clear roots and regain8 HP.'),
 ('sealed_vessel','Sealed Vessel',260,17,28,0,'ally','vessel','Give the most wounded visible living ally28 barrier and cleanse roots. Sacred vapour damages nearby foes for0.7× weapon damage.'),
 ('lustral_front','Lustral Front',320,33,54,2.6,'line','mend','A100px-wide320px sacred wave deals2.6× weapon damage and heals visible allies along its lane24 HP.')],
 'Rogue':[
 ('feint_cut','Feint Cut',170,10,18,1.15,'move','conceal','Cut visible foes within100px for1.15× weapon damage, retreat90px through clear ground and conceal for1.2s.'),
 ('shadow_anchor','Shadow Anchor',200,16,24,0,'self','anchor','Place a6s shadow anchor. After3s return through a clear line to it, gaining16 barrier. Blocked returns stay in place safely.'),
 ('nightfall_execution','Nightfall Execution',285,30,50,2.5,'target','execute','Strike the selected visible foe for2.5× weapon damage, doubled below30% health. Conceal for1s after the strike.')],
 'Druid':[
 ('bramble_lane','Bramble Lane',310,13,24,.45,'field','root','A110px bramble field at a visible foe pulses three times:0.45× weapon damage and brief roots.'),
 ('renewal_exchange','Renewal Exchange',240,18,26,0,'self','sacrifice','Consume up to20% current HP from each living summon, without killing it. Heal visible allies within240px by up to24 HP each from that finite pool.'),
 ('pack_reckoning','Pack Reckoning',320,34,56,2.0,'self','pack','Each living summon strikes visible foes within110px for2× your weapon damage. You and nearby allies gain20 barrier. Requires a living summon.')],
 'Bard':[
 ('syncopated_break','Syncopated Break',260,12,22,.9,'line','interrupt','A90px-wide260px sound lane deals0.9× weapon damage and interrupts enemy channels. Allies in the lane gain10 barrier.'),
 ('countermelody','Countermelody',230,18,28,0,'allies','tempo','For6s, nearby allies move20% faster and take20% less damage. Does not reset recharge or stack with a stronger ward.'),
 ('concordant_finale','Concordant Finale',310,34,54,2.2,'circle','concord','A310px resonance deals2.2× weapon damage, interrupts channels, heals allies16 HP and grants16 barrier.')],
 'Healer':[
 ('judgment_ray','Judgment Ray',340,11,21,1.35,'line','judgment','A55px-wide340px ray deals1.35× weapon damage. Each foe struck gives the most wounded nearby living ally4 HP, capped12 total.'),
 ('lifeline_surge','Lifeline Surge',300,17,27,0,'ally','lifeline','Heal the most wounded visible living ally24 HP and give16 barrier; foes within90px of that ally take weapon damage.'),
 ('dawn_deluge','Dawn Deluge',290,32,54,2.0,'circle','dawn','Deal2× weapon damage to visible foes within290px. Heal living allies28 HP; downed allies gain a24-point barrier for their next rescue, not an instant revive.')],
}
PASSIVES={
 'Knight':('knight_muster','Muster', 'Completing a revive grants both hunters24 barrier for6s.'),
 'Wizard':('wizard_alternation','Alternation','Casting a different active skill than your previous one restores3 mana, at most once per4s.'),
 'Archer':('archer_patience','Patient Aim','After standing still for1s, your next direct hit gains8 damage; once per4s.'),
 'Cleric':('cleric_residue','Restorative Residue','Direct damage restores4 HP to the nearest wounded living ally within160px, once per4s.'),
 'Rogue':('rogue_fresh_wound','Fresh Wound','Your first direct hit within3s of a dash applies5s bleed at20% weapon damage, once per dash.'),
 'Druid':('druid_mutual_shelter','Mutual Shelter','While a living owned summon is within100px, reduce incoming damage by3; no extra summon HP or free healing.'),
 'Bard':('bard_relay','Relay','Completing a revive grants nearby living allies25% movement speed for5s.'),
 'Healer':('healer_respite','Respite','Completing a revive heals you and the rescued ally12 HP and clears their roots.')}
MODIFIERS={
 'Knight':('formation_breach','Open the Formation',dict(width=100),'Formation Break widens to100px; committed positioning still matters.'),
 'Wizard':('ember_retention','Retained Embers',dict(pulses=4),'Ember Seam gains a fourth pulse; no shorter cooldown.'),
 'Archer':('pinning_breadth','Split Pins',dict(width=85),'Pinning Line widens to85px; its damage and range stay.'),
 'Cleric':('salve_reserve','Shared Salve',dict(salveHeal=14),'Purging Salve heals14 instead of8 per affected living ally.'),
 'Rogue':('feint_veil','Lingering Feint',dict(concealSeconds=2),'Feint Cut conceals for2s after its retreat; attacking still reveals you.'),
 'Druid':('bramble_reach','Living Boundary',dict(radius=145),'Bramble Lane grows to145px; line-of-sight and root resistance remain.'),
 'Bard':('break_resonance','Shared Break',dict(barrier=18),'Syncopated Break grants18 instead of10 barrier to allies in its lane.'),
 'Healer':('judgment_mercy','Merciful Judgment',dict(healCap=20),'Judgment Ray can distribute up to20 healing from enemies struck, without raising damage.')}
BRANCHES={'Knight':(1,2,1,0),'Wizard':(1,0,1,1),'Archer':(0,1,2,0),'Cleric':(2,1,0,2),
          'Rogue':(1,1,0,2),'Druid':(1,2,0,0),'Bard':(2,1,0,1),'Healer':(0,1,0,2)}
def readable(text):return re.sub(r'(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])',' ',text).replace('px-wide','px wide, ')

def install(trees):
    for hero,rows in ACTIVES.items():
        tree=trees[hero]
        if any(n['id']==rows[0][0] for n in tree):continue
        branches=list(dict.fromkeys(n['branch'] for n in tree));starter=next(n['id'] for n in tree if n['starter'] and n['ability']['attackType']=='special')
        for i,row in enumerate(rows):
            aid,name,reach,cd,mana,power,shape,mechanic,description=row
            description=readable(description)
            a=dict(id=aid,name=name,kind='campaign_skill',power=power,range=reach,cooldown=cd,manaCost=mana,
                   attackType='ultimate' if i==2 else 'special',description=description,iconKey=tree[0]['id'],shape=shape,mechanic=mechanic)
            tree.append(dict(id=aid,name=name,branch=branches[BRANCHES[hero][i]],type='ability',cost=3 if i==2 else 2,maxRank=1,requires=[starter if i==0 else rows[i-1][0]],effects=[description],ability=a,starter=False,
                             campaignGate='cinder' if i==2 else 'verdant' if i==1 else 'aurelian'))
        pid,name,text=PASSIVES[hero]
        tree.append(dict(id=pid,name=name,branch=branches[BRANCHES[hero][3]],type='passive',cost=2,maxRank=1,requires=[rows[0][0]],effects=[readable(text)],starter=False,campaignGate='aurelian'))
        mid,name,changes,text=MODIFIERS[hero]
        tree.append(dict(id=mid,name=name,branch=branches[BRANCHES[hero][0]],type='modifier',cost=2,maxRank=1,requires=[rows[0][0]],changes=[changes],effects=[readable(text)],starter=False,campaignGate='verdant'))

def gate(room,node):
    visits=room['adventure']['visited'];g=node.get('campaignGate')
    return not g or ('city_refuge' in visits if g=='aurelian' else 'veil_haven' in visits if g=='verdant' else 'cinder_foothills' in visits)

GATE_NAMES={'aurelian':'Aurelian’s refuge','verdant':'Rootsong in the Verdant Veil','cinder':'the first Cinder Crown sanctuary'}

def manifest():
    return {hero:dict(abilities=[dict(id=r[0],name=r[1],range=r[2],cooldown=r[3],mana=r[4],power=r[5],shape=r[6],mechanic=r[7],description=readable(r[8]),artStatus='awaiting-sprite-chat') for r in rows],
                      passive=dict(id=PASSIVES[hero][0],name=PASSIVES[hero][1],effect=readable(PASSIVES[hero][2])),
                      modifier=dict(id=MODIFIERS[hero][0],name=MODIFIERS[hero][1],changes=MODIFIERS[hero][2],effect=readable(MODIFIERS[hero][3]))) for hero,rows in ACTIVES.items()}

def cast(world,room,p,a):
    import combat_environment as terrain,skill_casts as sc,hero_skills,enemy_awareness,ability_animations,feedback,boss_ai
    now=time.monotonic();origin=(p['x'],p['y']);shape=a['shape'];mechanic=a['mechanic'];reach=a['range']
    choices=sc.foes(room,p,reach);enemy=min(choices,key=lambda e:(e['id']!=p.get('preferredTarget'),sc.distance(p,e)),default=None)
    living=sc.allies(world,room,p,reach or 300);ally=min(living,key=lambda q:q['hp']/q['maxHp'],default=p)
    summons=[s for s in room.get('summons',[]) if s['ownerId']==p['id'] and s['hp']>0]
    if shape in ('line','target','field') and not enemy:raise ValueError('Select or approach a visible enemy in range.')
    if mechanic in ('pack','sacrifice') and not summons:raise ValueError('This skill requires a living owned summon.')
    if p['mana']<a['manaCost']:raise ValueError('Not enough mana.')
    p['mana']-=a['manaCost'];hero_skills.commit_cooldown(p,a['id'],now+a['cooldown']);p['abilityCooldowns'][a['id']]=now+a['cooldown']
    enemy_awareness.break_concealment(p,a['id']);p.update(animation='special',animationUntil=time.time()+.45)
    feedback.emit(room,'ability',actor=p,abilityId=a['id'],attackType=a['attackType'],abilityKind='campaign_skill')
    def hit(e,factor=a['power']):
        if e in room['enemies']:world._damage_enemy(room,p,e,max(1,round(sc.base(p)*factor)))
    def in_line(actor,width):
        dx,dy=enemy['x']-origin[0],enemy['y']-origin[1];length=max(.001,math.hypot(dx,dy));ux,uy=dx/length,dy/length
        ax,ay=actor['x']-origin[0],actor['y']-origin[1];along=ax*ux+ay*uy
        return 0<=along<=reach and abs(ax*uy-ay*ux)<=width/2 and terrain.line_clear(room,p,actor)
    width=a.get('width',100 if mechanic in ('ward','mend') else 90 if mechanic=='interrupt' else 55 if mechanic=='judgment' else 65 if mechanic=='push' else 70 if hero_skills.rank(p,'prism_fracture') else 50)
    affected=[e for e in choices if in_line(e,width)] if shape=='line' else [enemy] if mechanic=='execute' else list(sc.foes(room,enemy if shape=='target' else p,100 if shape=='target' else reach)) if shape in ('target','circle') else []
    if shape=='field':
        room.setdefault('campaignFields',[]).append(dict(ownerId=p['id'],abilityId=a['id'],x=enemy['x'],y=enemy['y'],radius=a.get('radius',110 if mechanic=='root' else 115 if mechanic=='arc' else 110 if mechanic=='arrows' else 95),
            remaining=a.get('pulses',3),nextAt=now+.7,power=a['power'],mechanic=mechanic))
    for e in list(affected):
        if mechanic in ('root','push'):sc.root(e,now,1.5 if mechanic=='root' else .35)
        if mechanic=='root':e['weakenUntil']=now+3
        if mechanic in ('interrupt','concord'):world._stun(e,now);boss_ai.interrupt(world,room,e,now);__import__('encounter_roles').interrupt(e,now,999)
        hit(e, a['power']*(2 if mechanic=='execute' and e['hp']/e['maxHp']<.3 else 1))
        if mechanic=='push' and not any(e.get(k) for k in ('boss','miniBoss','structure')):
            dx,dy=e['x']-p['x'],e['y']-p['y'];d=max(1,math.hypot(dx,dy));terrain.move(room,e,e['x']+dx/d*65,e['y']+dy/d*65)
    if shape=='line':
        for q in living:
            if in_line(q,width):
                if mechanic=='interrupt':sc.shield(room,q,a.get('barrier',10))
                if mechanic=='mend':sc.heal(room,p,q,24)
        if mechanic=='ward':sc.shield(room,p,30)
        if mechanic=='judgment':sc.heal(room,p,ally,min(a.get('healCap',12),4*len(affected)))
    if mechanic=='cleanse':
        for q in sc.allies(world,room,enemy,100):q['rootUntil']=0;sc.heal(room,p,q,a.get('salveHeal',8))
    elif mechanic in ('vessel','lifeline'):
        sc.shield(room,ally,28 if mechanic=='vessel' else 16);ally['rootUntil']=0
        if mechanic=='lifeline':sc.heal(room,p,ally,24)
        for e in list(sc.foes(room,ally,90)):hit(e,.7 if mechanic=='vessel' else 1)
    elif mechanic in ('link','tempo'):
        for q in living:
            if mechanic=='link':sc.shield(room,q,24)
            if mechanic=='tempo' or sc.distance(q,p)<=100:sc.ward(q,now,.8 if mechanic=='tempo' else .75,6 if mechanic=='tempo' else 4,p)
            if mechanic=='tempo':q.update(speedBoost=1.2,speedBoostUntil=now+6)
    elif mechanic in ('trap','conceal'):
        if mechanic=='conceal':
            for e in list(sc.foes(room,p,100)):hit(e)
        fx,fy=p.get('facingX',1),p.get('facingY',0);d=max(.001,math.hypot(fx,fy));terrain.move(room,p,p['x']-90*fx/d,p['y']-90*fy/d)
        p['positionRevision']=p.get('positionRevision',0)+1
        if mechanic=='trap':room.setdefault('campaignFields',[]).append(dict(ownerId=p['id'],abilityId=a['id'],x=origin[0],y=origin[1],radius=90,remaining=3,nextAt=now+.7,power=a['power'],mechanic='root'))
        else:p['invisibleUntil']=now+a.get('concealSeconds',1.2)
    elif mechanic=='anchor':p['campaignAnchor']=dict(x=p['x'],y=p['y'],returnAt=now+3)
    elif mechanic=='execute':p['invisibleUntil']=now+1
    elif mechanic=='sacrifice':
        pool=0
        for s in summons:
            amount=min(max(0,s['hp']-1),round(s['hp']*.2));s['hp']-=amount;pool+=amount
        for q in sorted(living,key=lambda q:q['hp']/q['maxHp']):
            amount=min(24,pool,q['maxHp']-q['hp']);sc.heal(room,p,q,amount);pool-=amount
    elif mechanic=='pack':
        for s in summons:
            for e in list(sc.foes(room,s,110)):world._damage_enemy(room,p,e,max(1,round(sc.base(p)*a['power'])),summon_id=s['id'])
        for q in living:sc.shield(room,q,20)
    elif mechanic in ('concord','dawn'):
        for q in living:sc.heal(room,p,q,16 if mechanic=='concord' else 28);sc.shield(room,q,16 if mechanic=='concord' else 0)
        if mechanic=='dawn':
            for q in world._active_players(room):
                if q['status']=='downed' and sc.distance(p,q)<=reach and terrain.line_clear(room,p,q):q['pendingRescueBarrier']=24
    sc.after_cast(room,p,a,now)
    target=(enemy['x'],enemy['y']) if enemy else (ally['x'],ally['y'])
    visual=__import__('ability_visuals').describe(a,p,origin,target)
    if mechanic in ('pack','sacrifice'):
        visual['sources']=[dict(id=s['id'],x=s['x'],y=s['y']) for s in summons]
    if shape=='ally':visual['recipientIds']=[ally['id']]
    ability_animations.record(room,p,a,origin,target,[q['id'] for q in living] if shape in ('allies','ally') else [],visual=visual,
                              facing=visual['direction'] if shape in ('line','target','field') else None)

def tick(world,room,now):
    import skill_casts as sc,combat_environment as terrain
    for p in world._active_players(room):
        if p.get('dx',0) or p.get('dy',0):p['campaignStillSince']=now
        else:p.setdefault('campaignStillSince',now)
        anchor=p.get('campaignAnchor')
        if anchor and now>=anchor['returnAt']:
            p.pop('campaignAnchor',None)
            if p['status']=='alive' and terrain.line_clear(room,p,anchor) and terrain.walkable(room,anchor['x'],anchor['y']):
                terrain.move(room,p,anchor['x'],anchor['y']);p['positionRevision']=p.get('positionRevision',0)+1;sc.shield(room,p,16)
    for field in list(room.get('campaignFields',[])):
        owner=room['players'].get(field['ownerId'])
        if not owner or not owner.get('connected',True) or owner['status']!='alive':room['campaignFields'].remove(field);continue
        if now<field['nextAt']:continue
        field['nextAt']=now+1;field['remaining']-=1
        # Transient presentation history includes the final acknowledged pulse,
        # after its field is removed. It never schedules or applies damage.
        room.setdefault('_campaignVisualPulses',[]).append(dict(id=secrets.token_hex(6),at=now,stage=room['stage'],area=room['adventure']['current'],
            ownerId=field['ownerId'],abilityId=field.get('abilityId'),mechanic=field['mechanic'],x=field['x'],y=field['y'],radius=field['radius']))
        room['_campaignVisualPulses']=room['_campaignVisualPulses'][-32:]
        for e in list(sc.foes(room,field,field['radius'])):
            if field['mechanic']=='root':sc.root(e,now,.8)
            if field['mechanic']=='arc':world._stun(e,now)
            world._damage_enemy(room,owner,e,max(1,round(sc.base(owner)*field['power'])))
        if not field['remaining'] and field in room['campaignFields']:room['campaignFields'].remove(field)

def incoming(room,p,amount):
    import hero_skills
    if hero_skills.rank(p,'druid_mutual_shelter') and any(s['ownerId']==p['id'] and s['hp']>0 and math.dist((s['x'],s['y']),(p['x'],p['y']))<=100 for s in room.get('summons',[])):return max(0,amount-3)
    return amount

def outgoing(room,p,e,damage,summon,now):
    import hero_skills,skill_casts as sc,combat_environment as terrain
    if summon:return damage
    if hero_skills.rank(p,'archer_patience') and now-p.get('campaignStillSince',now)>=1 and p.get('campaignAimReady',0)<=now:damage+=8;p['campaignAimReady']=now+4
    if hero_skills.rank(p,'cleric_residue') and p.get('campaignResidueAt',0)<=now:
        allies=[q for q in room['players'].values() if q['status']=='alive' and q['hp']<q['maxHp'] and sc.distance(p,q)<=160 and terrain.line_clear(room,p,q)]
        if allies:sc.heal(room,p,min(allies,key=lambda q:sc.distance(p,q)),4);p['campaignResidueAt']=now+4
    if hero_skills.rank(p,'rogue_fresh_wound') and p.get('campaignDashUntil',0)>now:p['campaignDashUntil']=0;e.update(bleedOwner=p['id'],bleedUntil=now+5,bleedDamage=max(1,round(sc.base(p)*.2)),lastBleedTick=now)
    return damage

def after_cast(p,a,now):
    import hero_skills
    if hero_skills.rank(p,'wizard_alternation') and a['attackType']!='light' and a.get('id'):
        if p.get('campaignLastSpell') and p['campaignLastSpell']!=a['id'] and p.get('campaignAlternateAt',0)<=now:p['mana']=min(p['maxMana'],p['mana']+3);p['campaignAlternateAt']=now+4
        p['campaignLastSpell']=a['id']

def revived(room,p,target):
    import hero_skills,skill_casts as sc
    now=time.monotonic()
    if hero_skills.rank(p,'knight_muster'):
        for q in (p,target):sc.shield(room,q,24)
    if hero_skills.rank(p,'bard_relay'):
        for q in room['players'].values():
            if q['status']=='alive' and sc.distance(p,q)<=240:q.update(speedBoost=1.25,speedBoostUntil=now+5)
    if hero_skills.rank(p,'healer_respite'):
        for q in (p,target):sc.heal(room,p,q,12);q['rootUntil']=0

def wants(world,room,p,a):
    """Companions use ordinary costs/targets, retaining resources when healthy."""
    import skill_casts as sc
    allies=sc.allies(world,room,p,a['range'] or 300)
    if a['mechanic'] in ('sacrifice','lifeline','vessel') and not any(q['hp']<q['maxHp']*.8 for q in allies):return False
    if a['shape'] in ('circle','line','field','target') and not sc.foes(room,p,a['range']):return False
    if a['mechanic']=='pack' and not any(s['ownerId']==p['id'] for s in room.get('summons',[])):return False
    return True
