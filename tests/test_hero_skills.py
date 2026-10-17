import copy
import tempfile
import time
import unittest
import adventure
import hero_skills as skills
import skill_casts
from game import GameWorld
from test_adventure import party,travel,finish


class HeroSkillTests(unittest.TestCase):
    def unlock(self,w,r,p,node):w.action(r['code'],p['id'],dict(action='skillUnlock',node=node))
    def equip(self,w,r,p,aid,slot='active1'):w.action(r['code'],p['id'],dict(action='skillEquip',ability=aid,slot=slot))

    def test_knight_and_healer_starters_prerequisites_and_point_receipts(self):
        w,r,ps=party(('Knight','Healer'))
        for p in ps:
            self.assertEqual(len([n for n in skills.view(r,p)['nodes'] if n['branch']!='Ascension']),15);self.assertEqual(skills.points(p),2)
            self.assertEqual(len(p['abilities']),2)
        p=ps[0]
        with self.assertRaisesRegex(ValueError,'prerequisite'):self.unlock(w,r,p,'knight_pursuit')
        self.unlock(w,r,p,'shield_rush');self.assertEqual(skills.points(p),0)
        self.equip(w,r,p,'shield_rush');travel(w,r,'road');skills.ensure(r,p)
        self.assertEqual(skills.points(p),1);skills.ensure(r,p);self.assertEqual(skills.points(p),1)
        with self.assertRaisesRegex(ValueError,'Oakvale'):self.unlock(w,r,p,'cleaving_arc')

    def test_knight_rush_parry_and_healer_barrier_triage_beacon(self):
        w,r,ps=party(('Knight','Healer'));k,h=ps
        self.unlock(w,r,k,'shield_rush');self.equip(w,r,k,'shield_rush')
        self.unlock(w,r,h,'life_barrier');self.equip(w,r,h,'life_barrier')
        travel(w,r,'road');k.update(x=500,y=400,facingX=1,facingY=0);h.update(x=510,y=400)
        hp=k['hp'];w._cast_ability(r,k,1);self.assertGreater(k['x'],550);self.assertEqual(k['skillBarrier'],10)
        k['hp']=70;w._cast_ability(r,h,1);self.assertEqual(k['skillBarrier'],32)
        w._damage_player(r,{'boss':False},k,20);self.assertEqual(k['hp'],70);self.assertEqual(k['skillBarrier'],12)
        a=skills.catalog(h);h['mana']=100
        skill_casts.cast(w,r,h,a['triage']);self.assertEqual(k['hp'],88)
        skill_casts.tick(w,r,time.monotonic()+1.1);self.assertEqual(k['hp'],92)
        skill_casts.cast(w,r,h,a['rescue_beacon']);h['reviving']=k['id'];skill_casts.tick(w,r,time.monotonic())
        self.assertGreater(h['beaconUntil'],time.monotonic());self.assertEqual(h['wardFactor'],.65)
        k['mana']=100;skill_casts.cast(w,r,k,skills.catalog(k)['riposte']);k['skillBarrier']=0
        before=k['hp'];w._damage_player(r,{},k,15);self.assertEqual(k['hp'],before-3)

    def test_respec_and_swapping_preserve_health_and_slot_recharge(self):
        w,r,ps=party();p=ps[0];self.unlock(w,r,p,'shield_rush');self.equip(w,r,p,'shield_rush')
        deadline=time.monotonic()+8;p['abilityCooldowns']['shield_rush']=deadline;skills.commit_cooldown(p,'shield_rush',deadline)
        p['hp']=47;p['mana']=23
        w.action(r['code'],p['id'],dict(action='skillRespec'))
        self.assertEqual(skills.points(p),2);self.assertEqual((p['hp'],p['mana']),(47,23))
        self.assertEqual(skills.ready_at(p,'iron_wall'),deadline)
        w.action(r['code'],p['id'],dict(action='skillRespec'));self.assertEqual(skills.points(p),2)

    def test_legacy_loadout_training_and_export_restart_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            w,r,ps=party(storage_dir=root);p=ps[0];p.pop('heroProgress');p.pop('adventureLoadout')
            p.update(abilities=['cleaving_arc','challenge','earthshaker'],skillPoints=2,skillRanks={'power':2,'focus':1,'vitality':1})
            skills.ensure(r,p);self.assertTrue(all(skills.unlocked(p,a) for a in p['abilities']));self.assertEqual(skills.points(p),4)
            p['abilityCooldowns']['earthshaker']=time.monotonic()+9;skills.commit_cooldown(p,'earthshaker',time.monotonic()+9)
            adventure.save(w,r)
            from save_portability import project,validate
            portable,_=validate(project(adventure.snapshot(r)));self.assertNotIn('recoveryProof',str(portable))
            restored=GameWorld(storage_dir=root).rooms[r['code']]['players'][p['id']]
            self.assertEqual(restored['skillRanks'],p['skillRanks']);self.assertEqual(restored['heroProgress'],p['heroProgress'])
            self.assertGreater(skills.ready_at(restored,'earthshaker'),time.monotonic()+8)
            invalid=copy.deepcopy(portable);invalid['progress']['characters'][0]['heroProgress']['ranks']['no_such_node']=1
            with self.assertRaises(ValueError):validate(invalid)

    def test_all_eight_trees_have_functioning_active_casts_and_modifiers(self):
        # Functional fixtures unlock all nodes with explicit migration credit;
        # this is NOT an ordinary-stat progression or balance playthrough.
        from game import CLASSES
        for hero in CLASSES:
            with self.subTest(hero=hero):
                w,r,ps=party((hero,));p=ps[0];p['heroProgress']['legacyPoints']=99
                for n in skills.TREES[hero]:
                    for _ in range(n['maxRank']):
                        if not n['starter']:self.unlock(w,r,p,n['id'])
                skills.validate(p);cat=skills.catalog(p)
                for n in skills.TREES[hero]:
                    if n['type']=='modifier':
                        for k,v in n['changes'][-1].items():self.assertEqual(cat[n['requires'][0]][k],v)
                travel(w,r,'road');p.update(x=500,y=400,facingX=1,facingY=0,hp=30)
                if hero=='Druid':w._summon_companion(r,p,'fire_wolf',8,time.monotonic())
                for n in skills.TREES[hero]:
                    if n['type']!='ability' or n['ability']['kind'] not in skill_casts.KINDS:continue
                    # Keep one real, harmless target to inspect target selection,
                    # projectile creation, delayed effects and wall-safe movement.
                    e=copy.deepcopy(r['enemies'][0]) if r['enemies'] else None
                    if e is None:
                        e=dict(id='fixture',kind='serpent',hp=100,maxHp=100,damage=3,speed=60,x=560,y=400,stunUntil=0)
                    e.update(id='fixture',x=p['x']+50,y=p['y'],hp=1000,maxHp=1000);r['enemies']=[e]
                    p['mana']=100;p['hp']=30;before=p['mana']
                    skill_casts.cast(w,r,p,cat[n['id']]);self.assertLess(p['mana'],before)
                    skill_casts.tick(w,r,time.monotonic()+1.1)
                    self.assertGreater(p['abilityCooldowns'][n['id']],time.monotonic())
                    self.assertTrue(terrain_walkable(r,p))

    def test_modifier_retry_does_not_spend_twice_and_five_slots_persist(self):
        w,r,ps=party();p=ps[0]
        request=dict(action='skillUnlock',node='bash_training',expectedRank=0)
        w.action(r['code'],p['id'],request);available=skills.points(p)
        with self.assertRaisesRegex(ValueError,'already succeeded'):w.action(r['code'],p['id'],request)
        self.assertEqual(skills.points(p),available)
        r['adventure']['visited'].append('road');r['adventure']['quests']['hunter']='complete';p['heroProgress']['legacyPoints']=20
        skills.ensure(r,p)
        for aid,s in [('shield_rush','active2'),('rally_banner','active3'),('earthshaker','ultimate')]:self.unlock(w,r,p,aid);self.equip(w,r,p,aid,s)
        self.assertEqual(len(p['abilities']),5);self.assertGreater(skills.ready_at(p,'earthshaker'),time.monotonic()+14)
        view=w.state(r['code'],p['id']);self.assertEqual([s['barSlot'] for s in view['abilitySlots']],['basic','active1','active2','active3','ultimate'])
        from save_portability import validate,project
        result,_=validate(project(adventure.snapshot(r)));self.assertEqual(result['progress']['characters'][0]['adventureLoadout'],p['adventureLoadout'])

    def test_all_passive_families_change_actual_combat_or_resources(self):
        from game import CLASSES,SUMMON_TYPES
        for hero in CLASSES:
            with self.subTest(hero=hero):
                w,r,ps=party((hero,));p=ps[0];travel(w,r,'road');now=time.monotonic()
                p['heroProgress']['ranks']={n['id']:1 for n in skills.TREES[hero] if n['type']=='passive'}
                p.update(x=500,y=400,hp=30,mana=10,dx=0,dy=0)
                e=copy.deepcopy(r['enemies'][0]);e.update(x=510,y=400,hp=100,rootUntil=now+2,bleedUntil=now+2)
                ally=w._player('ally','Test ally');ally.update(**{'class':'Healer'},x=510,y=400,hp=40,mana=0);r['players']['ally']=ally
                if hero=='Knight':
                    self.assertEqual(skill_casts.incoming(w,r,p,e,20,now),14);skill_casts.dashed(r,p,now)
                    self.assertEqual(skill_casts.outgoing(r,p,e,20,None,now),30);skill_casts.revived(r,p,ally);self.assertEqual(ally['skillBarrier'],18)
                elif hero=='Healer':
                    p['hp']=p['maxHp'];skill_casts.heal(r,p,p,20);self.assertEqual(p['skillBarrier'],12)
                    skill_casts.revive_start(r,p,now);self.assertEqual(p['skillBarrier'],16);skill_casts.revived(r,p,ally);self.assertEqual(ally['mana'],15)
                elif hero=='Wizard':
                    skill_casts.dashed(r,p,now);self.assertEqual(p['skillBarrier'],10)
                    skill_casts.after_cast(r,p,dict(attackType='special',kind='banner'),now);self.assertEqual(p['mana'],16)
                    skill_casts.outgoing(r,p,e,20,None,now);self.assertEqual(p['mana'],19)
                elif hero=='Archer':
                    e['x']=780;self.assertEqual(skill_casts.outgoing(r,p,e,20,None,now),26)
                    skill_casts.dashed(r,p,now);self.assertEqual(skill_casts.outgoing(r,p,e,20,None,now),36)
                    skill_casts.revived(r,p,ally);self.assertEqual(ally['speedBoost'],1.3)
                elif hero=='Cleric':
                    skill_casts.outgoing(r,p,e,20,None,now);self.assertEqual(p['mana'],12)
                    skill_casts.potion(w,r,p,'heal');self.assertEqual(ally['skillBarrier'],12)
                    skill_casts.revive_start(r,p,now);self.assertEqual(p['skillBarrier'],16)
                elif hero=='Rogue':
                    self.assertEqual(skill_casts.outgoing(r,p,e,20,None,now),26);skill_casts.dashed(r,p,now);self.assertGreater(p['invisibleUntil'],now)
                    skill_casts.killed(r,p,e,now);self.assertEqual(p['hp'],36)
                elif hero=='Druid':
                    w._summon_companion(r,p,'fire_wolf',8,now);s=r['summons'][0];self.assertEqual(s['maxHp'],SUMMON_TYPES['fire_wolf']['hp']+25)
                    skill_casts.outgoing(r,p,e,20,None,now);self.assertEqual(p['mana'],13)
                    s['hp']=10;skill_casts.potion(w,r,p,'heal');self.assertEqual(s['hp'],30)
                elif hero=='Bard':
                    skill_casts.after_cast(r,p,dict(attackType='special',kind='banner'),now);skill_casts.outgoing(r,p,e,20,None,now);self.assertEqual(p['mana'],16)
                    skill_casts.potion(w,r,p,'mana');self.assertEqual(ally['mana'],8)
                    skill_casts.revived(r,p,ally);self.assertEqual(ally['skillBarrier'],18)

    def test_summon_recovery_slot_lock_and_companion_tree(self):
        w,r,ps=party(('Druid',));p=ps[0]
        p['heroProgress']['legacy']+=['ice_bear','nature_golem'];self.equip(w,r,p,'ice_bear','ultimate')
        p['abilityCooldowns']={};p['skillSlotCooldowns']={};travel(w,r,'road');w._cast_ability(r,p,p['abilities'].index('ice_bear'))
        saved=adventure.snapshot(r)['room']['players'][p['id']]
        self.assertEqual(saved['slotCooldownRemaining']['ultimate'],15);self.assertEqual(saved['cooldownRemaining']['ice_bear'],15)
        w,r,ps=party(companion=True);bot=next(p for p in r['players'].values() if p.get('bot'))
        self.assertEqual(len([n for n in skills.view(r,bot)['nodes'] if n['branch']!='Ascension']),15);self.assertGreaterEqual(skills.points(bot),0)


def terrain_walkable(room,p):return __import__('combat_environment').walkable(room,p['x'],p['y'])
