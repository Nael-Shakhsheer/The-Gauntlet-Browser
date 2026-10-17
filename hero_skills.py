"""Finite Adventure training. Gauntlet's pre-run loadouts are untouched.

Progress is character-bound; earned milestone receipts and legacy training are
never refunded into a second currency. Ability and action-slot recharge survive
loadout changes, respecs, travel, recovery and portable backups.
"""
import copy
import math
import time

TREES = {}
MILESTONES = dict(arrival=2,road=1,inn=1,hunter=2,bridge=2,shrine=2,
                  alcove=1,cave=2,floor1=1,floor2=1,tower=2,region=3)


def define(hero, branches, assignments, new, modifiers, passives):
    from game import ABILITY_SETS, ability_record
    nodes=[]
    for i,entry in enumerate(ABILITY_SETS[hero]):
        a=ability_record(entry);starter=i in (0,2)
        nodes.append(dict(id=a['id'],name=a['name'],branch=branches[assignments[i]],type='ability',
            cost=0 if starter else 3 if i>=4 else 1,maxRank=1,requires=[] if starter or i<4 else [ABILITY_SETS[hero][2][0]],
            effects=[a['description']],ability=a,starter=starter))
    for spec in new:
        aid,name,branch,kind,power,reach,cd,mana,description,icon=spec
        a=dict(id=aid,name=name,kind=kind,power=power,range=reach,cooldown=cd,manaCost=mana,
               attackType='special',description=description,iconKey=icon)
        nodes.append(dict(id=aid,name=name,branch=branches[branch],type='ability',cost=2,maxRank=1,
            requires=[ABILITY_SETS[hero][2][0]],effects=[description],ability=a,starter=False))
    for aid,name,branch,requires,effects,changes in modifiers:
        nodes.append(dict(id=aid,name=name,branch=branches[branch],type='modifier',cost=1,maxRank=len(effects),
            requires=[requires],effects=effects,changes=changes,starter=False))
    for aid,name,branch,requires,text in passives:
        nodes.append(dict(id=aid,name=name,branch=branches[branch],type='passive',cost=2,maxRank=1,
            requires=[requires],effects=[text],starter=False))
    TREES[hero]=nodes


def setup():
    if TREES:return
    define('Knight',('Defense','Weapon mastery','Leadership'),(0,1,0,2,2,1),[
      ('shield_rush','Shield Rush',1,'rush',1.2,110,8,16,'Rush 100px along your facing; strike and briefly stun foes within 90px of arrival. Gain a 10-point barrier for 4s.','shadowstep'),
      ('rally_banner','Rallying Banner',2,'banner',0,0,12,22,'Place a banner for 6s. Allies within 150px take 30% less damage while inside.','guardian_cry'),
      ('riposte','Riposte',0,'parry',0,0,10,16,'For 5s, the next hit loses 12 damage and counters its attacker for your base weapon damage if within 160px.','iron_wall')],[
      ('bash_training','Shield discipline',0,'shield_bash',['Bash reaches 195px.','Bash reaches 195px; recharges in 0.38s.'],[dict(range=195),dict(range=195,cooldown=.38)]),
      ('cleave_training','Wide arc',1,'cleaving_arc',['Cleave reaches 165px.','Cleave reaches 165px and deals 1.1× weapon damage.'],[dict(range=165),dict(range=165,power=1.1)]),
      ('cry_training','Enduring command',2,'guardian_cry',['Last Stand lasts 11s.','Last Stand lasts 11s and also clears roots.'],[dict(duration=11),dict(duration=11,cleanse=True)])],[
      ('knight_brace','Brace',0,'iron_wall','While standing still, block 6 damage from a hit, once per 3s.'),
      ('knight_pursuit','Steel tempo',1,'shield_rush','A successful dash primes your next direct hit within 3s to deal 10 extra damage.'),
      ('knight_captain','Captain’s rescue',2,'rally_banner','Completing a revive grants both hunters an 18-point barrier for 6s.')])
    define('Healer',('Direct healing','Prevention','Rescue'),(0,1,0,2,1,2),[
      ('life_barrier','Life Barrier',1,'barrier',32,320,10,20,'Give the lowest-health standing ally within 320px a 32-point barrier for 6s. Can target yourself.','team_aegis'),
      ('triage','Triage',0,'triage',18,320,12,22,'Heal the most injured ally within 320px for 18, then 4 each second for 6s.','major_mend'),
      ('rescue_beacon','Rescue Beacon',2,'beacon',0,0,14,24,'Place a beacon for 6s. Within 160px, holding a revive is 40% faster and rescuers take 35% less damage.','quick_revival')],[
      ('spark_training','Long reach',0,'life_spark',['Life Spark reaches 260px.','Life Spark reaches 260px and recharges in 0.4s.'],[dict(range=260),dict(range=260,cooldown=.4)]),
      ('mend_training','Deep mend',0,'major_mend',['Major Mend restores 58 HP.','Major Mend restores 58 HP and clears roots.'],[dict(power=58),dict(power=58,cleanse=True)]),
      ('revival_training','Safe return',2,'quick_revival',['Quick Revival restores 60% HP.','Quick Revival restores 60% HP and gives an 18-point barrier.'],[dict(reviveFraction=.6),dict(reviveFraction=.6,barrier=18)])],[
      ('healer_overflow','Gentle overflow',0,'triage','Your healing converts excess healing into a barrier, capped at 12 points for 6s.'),
      ('healer_ward','Watchful hands',1,'life_barrier','Starting a held revive gives you a 16-point barrier, once per 8s.'),
      ('healer_rescue','Shared relief',2,'rescue_beacon','Completing a revive restores 15 mana to both hunters.')])
    define('Wizard',('Elemental control','Arcane power','Mobility'),(1,0,1,2,2,1),[
      ('glacial_prison','Glacial Prison',0,'root_burst',.65,320,10,22,'Root a selected cluster within 320px for 1.6s and deal 65% weapon damage in a 95px circle. Boss roots are shorter.','frost_lance'),
      ('mana_rift','Mana Rift',1,'rift',.45,320,12,24,'Open a fixed 95px rift at your target for three pulses, each dealing 45% weapon damage.','arcane_cataclysm'),
      ('phase_step','Phase Step',2,'phase',0,120,9,18,'Step 120px along your facing, respecting walls and roots; gain a 12-point barrier for 4s.','blink')],[
      ('arc_training','Conductive arc',1,'arc_burst',['Arc Bolt chains to three additional enemies.','Arc Bolt chains to three enemies with 80% damage retained per jump.'],[dict(chainTargets=3),dict(chainTargets=3,chainDecay=.8)]),
      ('frost_training','Distant frost',0,'frost_lance',['Frost Lance reaches 380px.','Frost Lance reaches 380px and deals 85% weapon damage.'],[dict(range=380),dict(range=380,power=.85)]),
      ('aegis_training','Astral shelter',2,'team_aegis',['Astral Aegis lasts 11s.','Astral Aegis lasts 11s and clears roots.'],[dict(duration=11),dict(duration=11,cleanse=True)])],[
      ('wizard_phase','Phase armor',2,'phase_step','A successful dash grants a 10-point barrier for 4s.'),
      ('wizard_reserve','Arcane reserve',1,'mana_rift','Casting an active after at least 4s without another active refunds 6 mana.'),
      ('wizard_control','Cold insight',0,'glacial_prison','Hitting an already rooted or stunned enemy restores 3 mana, once per 2s.')])
    define('Archer',('Precision','Traps','Volleys'),(0,1,0,1,2,0),[
      ('barbed_trap','Barbed Trap',1,'trap',1.4,0,10,18,'Place a trap 65px ahead for 8s. The first foe within 55px triggers damage and a 1.2s root in a 70px circle.','snare_shot'),
      ('sidestep_shot','Sidestep Shot',0,'sidestep',1.4,350,9,20,'Step 80px sideways and fire a powerful arrow at your selected foe within 350px.','piercing_volley'),
      ('marked_quarry','Marked Quarry',0,'mark',8,380,12,16,'Mark a selected foe within 380px for 6s. Your next three direct hits each deal 8 extra damage.','deadeye')],[
      ('volley_training','Longbow',0,'piercing_volley',['Quick Shot reaches 400px.','Quick Shot reaches 400px; its impact splash grows to 75px.'],[dict(range=400),dict(range=400,splashRadius=75)]),
      ('snare_training','Patient aim',1,'snare_shot',['Snare Shot reaches 380px.','Snare Shot reaches 380px and costs no extra time: 0.42s recharge.'],[dict(range=380),dict(range=380,cooldown=.42)]),
      ('rain_training','Broad volleys',2,'rain_of_arrows',['Rain of Arrows has a 145px blast radius.','Rain of Arrows has a 145px radius and 450px casting range.'],[dict(blastRadius=145),dict(blastRadius=145,range=450)])],[
      ('archer_sight','Long sight',0,'marked_quarry','Direct hits beyond 240px deal 6 extra damage.'),
      ('archer_escape','Escape shot',1,'sidestep_shot','A successful dash primes your next direct hit within 3s for 10 extra damage.'),
      ('archer_rescue','Covering fire',2,'rain_of_arrows','Completing a revive gives nearby allies 30% movement speed for 4s.')])
    define('Cleric',('Sacred projectiles','Protection','Restorative mixtures'),(0,0,2,1,2,1),[
      ('sunburst_flask','Sunburst Flask',0,'sunburst',1.3,300,10,22,'Throw a sacred burst at your selected foe. Enemies in its 100px circle take damage and deal 30% less damage for 4s.','radiant_flask'),
      ('pilgrim_draft','Pilgrim’s Draft',2,'draft',0,240,12,24,'Nearby allies recover 12 mana and move 25% faster for 5s. Costs 24 mana, so it cannot generate free caster mana.','splash_mend'),
      ('hallowed_circle','Hallowed Circle',1,'hallowed',0,0,14,24,'Place a 130px circle for 6s. Allies inside take 30% less damage and have roots cleared.','blessed_vial')],[
      ('flask_training','Scattering light',0,'radiant_flask',['Radiant Flask splashes within 105px.','Radiant Flask splashes within 105px and reaches 320px.'],[dict(splashRadius=105),dict(splashRadius=105,range=320)]),
      ('splash_training','Cleansing mixture',2,'splash_mend',['Splash Mend also clears roots.','Splash Mend clears roots and reaches 320px.'],[dict(cleanse=True),dict(cleanse=True,range=320)]),
      ('vial_training','Pilgrim shelter',1,'blessed_vial',['Blessed Vial reaches 320px.','Blessed Vial reaches 320px and lasts 11s.'],[dict(range=320),dict(range=320,duration=11)])],[
      ('cleric_consecrate','Consecrated shards',0,'sunburst_flask','Direct hits restore 2 mana, once per 3s.'),
      ('cleric_potion','Shared remedy',2,'pilgrim_draft','Using a healing consumable gives nearby allies a 12-point barrier for 6s.'),
      ('cleric_rescue','Pilgrim’s guard',1,'hallowed_circle','Starting a held revive grants a 16-point barrier, once per 8s.')])
    define('Rogue',('Ambush','Movement','Sustained pressure'),(2,0,0,1,2,0),[
      ('smoke_snare','Smoke Snare',0,'smoke',.4,150,11,20,'Root nearby foes for 1s and deal 40% weapon damage. Become untargetable for 2s.','vanish'),
      ('venom_edge','Venom Edge',2,'venom',0,0,12,18,'Your next three direct hits within 8s apply a five-second bleed for 25% weapon damage per tick.','backstab'),
      ('crosscut','Crosscut',1,'crosscut',1.8,240,10,22,'Rush toward your selected foe up to 160px, then strike enemies within 95px of arrival. Walls block the rush and strikes.','shadowstep')],[
      ('cut_training','Extended blade',2,'backstab',['Quick Cut reaches 195px.','Quick Cut reaches 195px and deals 120% weapon damage.'],[dict(range=195),dict(range=195,power=1.2)]),
      ('shadow_training','Long pursuit',1,'shadowstep',['Shadowstep reaches 380px.','Shadowstep reaches 380px and recharges in 6s.'],[dict(range=380),dict(range=380,cooldown=6)]),
      ('bloom_training','Wide bloom',0,'death_bloom',['Death Bloom reaches 340px.','Death Bloom reaches 340px and deals 2.7× weapon damage.'],[dict(range=340),dict(range=340,power=2.7)])],[
      ('rogue_opportunity','Opportunist',0,'smoke_snare','Direct hits against rooted or stunned foes deal 6 extra damage.'),
      ('rogue_escape','Vanish step',1,'crosscut','A successful dash makes you untargetable for 1s.'),
      ('rogue_blood','Blood price',2,'venom_edge','Killing a bleeding foe restores 6 HP, once per 3s.')])
    define('Druid',('Summons','Nature control','Restoration'),(1,1,0,0,0,2),[
      ('root_grasp','Root Grasp',1,'root_burst',.65,310,10,20,'Root a selected cluster within 310px for 1.6s and strike a 95px circle for 65% weapon damage. Bosses resist roots.','briar_burst'),
      ('verdant_spring','Verdant Spring',2,'spring',3,0,14,24,'Place a 130px healing spring for 6s. Standing allies recover 3 HP each second while inside.','splash_mend'),
      ('call_wild','Call of the Wild',0,'call',0,0,12,22,'Recall your living summons beside you, healing each for 20% maximum HP. Requires a living summon and respects solid ground.','fire_wolf')],[
      ('briar_training','Spreading roots',1,'briar_burst',['Briar Bolt spreads through a 95px circle.','Briar Bolt spreads through 95px and roots for 1.2s.'],[dict(splashRadius=95),dict(splashRadius=95,rootDuration=1.2)]),
      ('bird_training','Storm keeper',0,'lightning_bird',['Lightning Bird has 30 additional maximum HP.','Lightning Bird has 30 additional HP and costs 16 mana.'],[dict(summonBonus=30),dict(summonBonus=30,manaCost=16)]),
      ('bear_training','Ancient guardian',2,'ice_bear',['Ice Bear has 50 additional maximum HP.','Ice Bear has 50 additional HP and grants you a 16-point barrier on summoning.'],[dict(summonBonus=50),dict(summonBonus=50,barrier=16)])],[
      ('druid_kindred','Kindred shelter',0,'call_wild','All your summons gain 25 maximum HP. This does not change their attack damage or death recharge.'),
      ('druid_roots','Root communion',1,'root_grasp','Hitting a rooted foe restores 3 mana, once per 3s.'),
      ('druid_nourish','Wild nourishment',2,'verdant_spring','Using a healing consumable heals your living summons for 20 HP each.')])
    define('Bard',('Offensive rhythm','Support','Disruption'),(0,2,1,1,0,1),[
      ('dissonant_refrain','Dissonant Refrain',2,'refrain',1,210,10,20,'Interrupt nearby enemies and deal weapon damage. Bosses resist repeated control.','discord_note'),
      ('echo_verse','Echo Verse',0,'echo',.9,300,10,18,'Fire an echo bolt at your selected foe after 0.6s, dealing 90% weapon damage.','grand_crescendo'),
      ('restful_cadence','Restful Cadence',1,'cadence',0,240,14,24,'For 8s, nearby allies’ direct hits restore 2 mana, at most once per second each.','rallying_chord')],[
      ('discord_training','Resonant circle',0,'discord_note',['Discord Note reaches 250px.','Discord Note reaches 250px and deals 115% weapon damage.'],[dict(range=250),dict(range=250,power=1.15)]),
      ('rhythm_training','Travel rhythm',1,'fleet_rhythm',['Fleet Rhythm lasts 9s.','Fleet Rhythm lasts 9s and grants 40% movement speed.'],[dict(duration=9),dict(duration=9,power=1.4)]),
      ('crescendo_training','Grand hall',2,'grand_crescendo',['Grand Crescendo reaches 360px.','Grand Crescendo reaches 360px and deals 3× weapon damage.'],[dict(range=360),dict(range=360,power=3)])],[
      ('bard_backbeat','Backbeat',0,'echo_verse','Casting an active primes your next direct hit within 4s to recover 6 mana.'),
      ('bard_encore','Generous encore',1,'restful_cadence','Using a mana consumable restores 8 mana to nearby allies other than you.'),
      ('bard_rescue','Steady chorus',2,'dissonant_refrain','Completing a revive grants both hunters an 18-point barrier for 6s.')])


def facts(room):
    a=room['adventure'];q=a['quests'];ds=a.get('dungeons',{});c=ds.get('cave',{});t=ds.get('tower',{})
    return dict(arrival=True,road='road' in a['visited'],inn=any(p.get('trainingKnown') for p in room['players'].values()),
        hunter=q['hunter']=='complete',bridge=a['bridge'],shrine=q['shrine']=='complete',
        alcove='cave_survey' in c.get('claimedTreasure',[]),cave=c.get('bossComplete',False),
        floor1=1 in t.get('completedFloors',[]),floor2=2 in t.get('completedFloors',[]),
        tower=t.get('bossComplete',False),region=a['bossComplete'])


def ensure(room,p):
    __import__('soul_crystal').ensure(p)
    setup();hero=p['class']
    if hero not in TREES:raise ValueError('Unsupported Adventure hero tree: '+str(hero))
    tree=TREES[hero];old=p.get('heroProgress');fresh=p.pop('_freshHero',False)
    if old is None:
        legacy=[] if fresh else [aid for aid in p['abilities'] if any(n['id']==aid for n in tree)]
        old=p['heroProgress']=dict(version=1,hero=hero,ranks={},awards=[],legacy=legacy,
            legacyPoints=min(99,max(0,p.get('skillPoints',0)-(1 if 'first_inn' in p.get('skillRewards',[]) and p.get('trainingKnown') else 0))))
        p['skillPoints']=0
    if old.get('version')!=1:raise ValueError('Unsupported hero progression; original save preserved.')
    if old['hero']!=hero:
        old.update(hero=hero,ranks={},legacy=[]);p.pop('adventureLoadout',None)
        p['abilities']=[n['id'] for n in tree if n['starter']]
        p['abilityCooldowns']={k:v for k,v in p['abilityCooldowns'].items() if k in catalog(p)}
    for key,complete in facts(room).items():
        if complete and key not in old['awards']:old['awards'].append(key)
    if 'adventureLoadout' not in p:
        catalogue=catalog(p);basic=next((a for a in p['abilities'] if catalogue.get(a,{}).get('attackType')=='light'),tree[0]['id'])
        active=[a for a in p['abilities'] if catalogue.get(a,{}).get('attackType')=='special'][:3]
        ultimate=next((a for a in p['abilities'] if catalogue.get(a,{}).get('attackType')=='ultimate'),None)
        p['adventureLoadout']=dict(basic=basic,active=(active+[None]*3)[:3],ultimate=ultimate)
    flatten(p)
    for aid in p['abilities']:commit_cooldown(p,aid,p['abilityCooldowns'].get(aid,0))
    return old


def catalog(p):
    setup();out={n['id']:copy.deepcopy(n['ability']) for n in TREES[p['class']] if n['type']=='ability'}
    for n in TREES[p['class']]:
        r=rank(p,n['id'])
        if n['type']=='modifier' and r:
            for aid in n['requires']:
                if aid in out:
                    changes=n['changes'][r-1];a=out[aid]
                    for field in ('range','splashRadius','blastRadius'):
                        if field in changes and field in a:a['description']=a['description'].replace(str(a[field])+'px',str(changes[field])+'px')
                    if 'rootDuration' in changes:a['description']=a['description'].replace(str(a.get('rootDuration',.8))+'s',str(changes['rootDuration'])+'s')
                    if 'duration' in changes:
                        old=6 if a['kind']=='team_speed' else 8
                        a['description']=a['description'].replace(str(old)+' seconds',str(changes['duration'])+' seconds')
                    a.update(changes)
                    if aid=='arc_burst':a['description']=f"A bolt chains to {a['chainTargets']} more foes within 110px of each hit, retaining {round(a['chainDecay']*100)}% damage per jump."
                    if a.get('cleanse'):a['description']+=' Clears roots on affected allies.'
                    if a.get('barrier'):a['description']+=f" Grants a {a['barrier']}-point barrier."
    if __import__('ascension').active(p):
        a=__import__('ascension').ability(p);out[a['id']]=a
    return out


def rank(p,node):return p.get('heroProgress',{}).get('ranks',{}).get(node,0)
def unlocked(p,node):
    if __import__('ascension').active(p) and node==__import__('ascension').ability(p)['id']:return True
    return rank(p,node)>0 or node in p.get('heroProgress',{}).get('legacy',[]) or any(n['id']==node and n['starter'] for n in TREES[p['class']])
def points(p):
    h=p['heroProgress'];return h.get('legacyPoints',0)+sum(MILESTONES[k] for k in h['awards'])-sum(n['cost']*rank(p,n['id']) for n in TREES[p['class']])
def active_slots(room):
    return 3 if any(v=='complete' for v in room['adventure']['quests'].values()) else 2 if 'road' in room['adventure']['visited'] else 1
def flatten(p):
    l=p['adventureLoadout'];p['abilities']=[a for a in [l['basic'],*l['active'],l['ultimate']] if a]
def slot(p,aid):
    l=p.get('adventureLoadout')
    if not l:return None
    if aid==l['basic']:return 'basic'
    if aid==l['ultimate']:return 'ultimate'
    return next(('active'+str(i+1) for i,a in enumerate(l['active']) if a==aid),None)
def ready_at(p,aid):return max(p['abilityCooldowns'].get(aid,0),p.get('skillSlotCooldowns',{}).get(slot(p,aid),0))
def commit_cooldown(p,aid,until):
    if p.get('adventureLoadout'):
        s=slot(p,aid)
        if s:p.setdefault('skillSlotCooldowns',{})[s]=max(until,p.get('skillSlotCooldowns',{}).get(s,0))
def safe(room,p):return room['adventure']['current'] in __import__('region_content').HUBS and p['status']=='alive' and not __import__('progression').locked(room,p)


def action(world,room,p,payload):
    ensure(room,p)
    if not safe(room,p):raise ValueError('Change skills in Oakvale or Dunmere after closing the conversation. Inspect your tree anywhere.')
    kind=payload['action'];nodes={n['id']:n for n in TREES[p['class']]}
    if kind=='skillUnlock':
        n=nodes.get(payload.get('node'))
        if not n:raise ValueError('Unknown skill.')
        r=rank(p,n['id'])
        if 'expectedRank' in payload and payload['expectedRank']!=r:raise ValueError('This skill changed or the previous request already succeeded. Review its current rank.')
        if n['starter'] or n['id'] in p['heroProgress']['legacy'] or r>=n['maxRank']:raise ValueError('This skill is already fully unlocked.')
        if any(not unlocked(p,k) for k in n['requires']):raise ValueError('Unlock the prerequisite first.')
        if points(p)<n['cost']:raise ValueError('Not enough milestone points.')
        p['heroProgress']['ranks'][n['id']]=r+1
    elif kind=='skillEquip':
        s=payload.get('slot');aid=payload.get('ability');l=p['adventureLoadout'];cat=catalog(p)
        valid=s in ('basic','ultimate','active1','active2','active3')
        if not valid:raise ValueError('Unknown action slot.')
        if s.startswith('active') and int(s[-1])>active_slots(room):raise ValueError('Explore the road and complete a woodland quest to open this slot.')
        category='light' if s=='basic' else 'ultimate' if s=='ultimate' else 'special'
        if aid is not None and (aid not in cat or not unlocked(p,aid) or cat[aid]['attackType']!=category):raise ValueError('Unlock a matching ability first.')
        if s=='basic' and aid is None:raise ValueError('Keep a basic attack equipped.')
        if aid and slot(p,aid)==s:return
        if aid and aid in p['abilities']:raise ValueError('That ability is already equipped.')
        world._dismiss_summons(room,p['id'])
        if s.startswith('active'):l['active'][int(s[-1])-1]=aid
        else:l[s]=aid
        if aid and s=='ultimate' and not p.get('ultimateIntroduced'):
            p['abilityCooldowns'][aid]=max(p['abilityCooldowns'].get(aid,0),time.monotonic()+15);p['ultimateIntroduced']=True
        flatten(p)
    elif kind=='skillRespec':
        world._dismiss_summons(room,p['id']);p['heroProgress']['ranks']={}
        starters=[n['id'] for n in TREES[p['class']] if n['starter']]
        p['adventureLoadout']=dict(basic=starters[0],active=[starters[1],None,None],ultimate=None);flatten(p)
        # Respec is free at home. It neither restores resources nor clears clocks.
    else:raise ValueError('Unknown skill action.')


def revision(room,p):
    """Public UI content token, not authorization or durable progression.

    Includes every tree-view input, especially safety/slots and class changes.
    Cooldown clocks remain in the live ability slots, never in this cache.
    """
    import hashlib,json
    ensure(room,p)
    fields=(__import__('build_info').SERVER,p['class'],p['heroProgress'],p['adventureLoadout'],p.get('skillRanks',{}),
            bool(p.get('magicRunes',{}).get('ascended')),safe(room,p),active_slots(room))
    return hashlib.sha256(json.dumps(fields,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16]


def view(room,p):
    ensure(room,p);h=p['heroProgress'];cat=catalog(p)
    return dict(hero=p['class'],points=points(p),earned=sum(MILESTONES[k] for k in h['awards'])+h.get('legacyPoints',0),
        safe=safe(room,p),activeSlots=active_slots(room),loadout=copy.deepcopy(p['adventureLoadout']),
        legacyTraining=copy.deepcopy(p.get('skillRanks',{})),milestones=[dict(id=k,points=v,earned=k in h['awards']) for k,v in MILESTONES.items()],
        nodes=[{k:copy.deepcopy(v) for k,v in n.items() if k not in ('changes','ability')}|dict(rank=rank(p,n['id']),
            unlocked=unlocked(p,n['id']),equipped=n['id'] in p['abilities'],current=cat.get(n['id'])) for n in TREES[p['class']]]+__import__('ascension').nodes(p))


def train_companions(world,room):
    for p in room['players'].values():
        if not p.get('bot') or not safe(room,p):continue
        abilities=[n for n in TREES[p['class']] if n['type']=='ability' and not n['starter'] and n['ability']['attackType']!='light']
        # A deterministic utility/ultimate build uses the same finite budget and
        # safe-location checks as human characters. No bonus points or stats.
        order=sorted(abilities,key=lambda n:(n['ability']['attackType']!='ultimate',n['cost'],n['id']))
        for n in order:
            if not unlocked(p,n['id']) and points(p)>=n['cost'] and all(unlocked(p,k) for k in n['requires']):
                action(world,room,p,dict(action='skillUnlock',node=n['id']))
        l=p['adventureLoadout']
        if not l['ultimate']:
            aid=next((n['id'] for n in order if n['ability']['attackType']=='ultimate' and unlocked(p,n['id'])),None)
            if aid:action(world,room,p,dict(action='skillEquip',slot='ultimate',ability=aid))
        for i in range(active_slots(room)):
            if l['active'][i]:continue
            aid=next((n['id'] for n in order if n['ability']['attackType']=='special' and unlocked(p,n['id']) and n['id'] not in p['abilities']),None)
            if aid:action(world,room,p,dict(action='skillEquip',slot='active'+str(i+1),ability=aid))


def validate(p):
    setup();h=p.get('heroProgress')
    if h is None:return
    if not isinstance(h,dict) or h.get('version')!=1 or h.get('hero')!=p['class']:raise ValueError('Unsupported hero progression; original save preserved.')
    nodes={n['id']:n for n in TREES[p['class']]}
    if set(h)-{'version','hero','ranks','awards','legacy','legacyPoints'}:raise ValueError('Unsupported hero progression fields.')
    if not isinstance(h.get('legacyPoints'),int) or not 0<=h['legacyPoints']<=99:raise ValueError('Invalid legacy training credit.')
    if not isinstance(h.get('awards'),list) or any(not isinstance(k,str) for k in h['awards']) or len(set(h['awards']))!=len(h['awards']) or any(k not in MILESTONES for k in h['awards']):raise ValueError('Invalid skill milestone receipts.')
    if not isinstance(h.get('legacy'),list) or any(not isinstance(k,str) for k in h['legacy']) or len(set(h['legacy']))!=len(h['legacy']) or any(k not in nodes or nodes[k]['type']!='ability' for k in h['legacy']):raise ValueError('Invalid legacy skills.')
    if not isinstance(h.get('ranks'),dict) or any(k not in nodes or not isinstance(v,int) or not 0<=v<=nodes[k]['maxRank'] for k,v in h['ranks'].items()):raise ValueError('Invalid hero skill ranks.')
    if points(p)<0 or any(rank(p,k) and any(not unlocked(p,r) for r in n['requires']) for k,n in nodes.items()):raise ValueError('Invalid skill costs or prerequisites.')
    l=p.get('adventureLoadout')
    if not isinstance(l,dict) or set(l)!={'basic','active','ultimate'} or not isinstance(l['active'],list) or len(l['active'])!=3:raise ValueError('Invalid hero action bar.')
    cat=catalog(p);seen=[]
    for aid,category in [(l['basic'],'light'),*((a,'special') for a in l['active']),(l['ultimate'],'ultimate')]:
        if aid is None:continue
        if not isinstance(aid,str) or aid not in cat or not unlocked(p,aid) or cat[aid]['attackType']!=category or aid in seen:raise ValueError('Invalid equipped skill.')
        seen.append(aid)
    if not l['basic'] or seen!=p['abilities']:raise ValueError('Inconsistent hero loadout.')
