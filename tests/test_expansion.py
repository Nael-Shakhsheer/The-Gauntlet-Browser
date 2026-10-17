"""Expansion functional fixtures. Forced encounter clears are not balance playtests."""
import copy
import math
import tempfile
import time
import unittest
from unittest.mock import patch
import adventure,ascension,chapter_flow as chapter,magic_runes as magic,region_content as region
import combat_environment as terrain
import hero_skills,save_portability,village_portals
from game import GameWorld,CLASSES
from test_opening import new,clear
from test_adventure import finish,interact


def start(heroes=('Knight',),directory=None):
    w,r,ps=new(heroes,directory=directory,skip=True)
    for p in ps:finish(w,r,p)
    return w,r,ps


def runner(w,r,p):
    finish(w,r,p);p.update(townInterior=None)
    f=next(f for f in adventure.features(r) if f['id']=='runner');p.update(x=f['x'],y=f['y'])


def report_chain(w,r,p,key):
    for current in chapter.ORDER[:chapter.ORDER.index(key)+1]:
        hub=chapter.SPECS[current]['hub'];adventure.enter(w,r,hub,'south');runner(w,r,p)
        chapter.reconcile(r);w.action(r['code'],p['id'],dict(action='chapterAccept',quest=current))
        for fact in chapter.SPECS[current]['requires']:chapter.evidence(r,fact)
        if current=='border':adventure.enter(w,r,'dunmere','north');runner(w,r,p)
        w.action(r['code'],p['id'],dict(action='chapterReport',quest=current))


class ExpansionTests(unittest.TestCase):
    def test_source_budget_and_personal_claims(self):
        w,r,ps=start(('Knight','Healer'));p,q=ps
        self.assertEqual(sum(magic.SOURCES.values()),16)
        self.assertEqual(sum(v for k,v in magic.SOURCES.items() if k.startswith('report:') and k.split(':')[1] in ('failed_harvest','irrigation','mill_cellar','chapter_outcome')),7)
        self.assertTrue(magic.claim(p,'shrine:brook'));self.assertFalse(magic.claim(p,'shrine:brook'))
        self.assertEqual(magic.ensure(q)['balance'],0);self.assertEqual(r['runes'],0)
        for key in magic.SOURCES:magic.claim(p,key)
        magic.validate(p);self.assertEqual(magic.ensure(p)['balance'],16)

    def test_stat_purchases_all_heroes_additive_proportional_and_capped(self):
        for hero in CLASSES:
            w,r,ps=start((hero,));p=ps[0]
            for key in magic.SOURCES:magic.claim(p,key)
            p.update(hp=p['maxHp']*.5,mana=40);p['abilityCooldowns']['sentinel']=time.monotonic()+50
            for i in range(5):
                w.action(r['code'],p['id'],dict(action='magicPurchase',purchase='health',expectedRank=i,requestId='health_purchase_'+str(i)))
                self.assertEqual(p['maxHp'],math.ceil(CLASSES[hero]['hp']*(100+5*(i+1))/100))
                self.assertLessEqual(p['hp']/p['maxHp'],.5)
            for i in range(5):w.action(r['code'],p['id'],dict(action='magicPurchase',purchase='mana',expectedRank=i,requestId='mana_purchase___'+str(i)))
            self.assertEqual((p['maxMana'],p['mana']),(125,50));self.assertEqual(magic.ensure(p)['balance'],6)
            before=copy.deepcopy(p['magicRunes']);magic.refresh(p);magic.refresh(p);self.assertEqual(before,p['magicRunes'])
            with self.assertRaisesRegex(ValueError,'capped'):magic.transact(w,r,p,dict(purchase='health',expectedRank=5,requestId='over_cap_purchase'))
            with self.assertRaisesRegex(ValueError,'15 currently'):magic.transact(w,r,p,dict(purchase='ascend',requestId='not_enough_runes_'))
            self.assertGreater(p['abilityCooldowns']['sentinel'],time.monotonic())

    def test_exact_fifteen_retry_storage_failure_and_downed(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=start(directory=directory);p=ps[0]
            for key in magic.SOURCES:
                if key!='cache:dry_spring':magic.claim(p,key)
            self.assertEqual(p['magicRunes']['balance'],15)
            r['adventure']['chapter']['turnedIn'].append('chapter_outcome');r['adventure']['chapter']['stages']['chapter_outcome']='complete'
            payload=dict(purchase='ascend',requestId='same_permanent_transaction')
            original=copy.deepcopy(p)
            with patch.object(w.storage,'save_adventure',side_effect=OSError('test disk failure')):
                with self.assertRaisesRegex(ValueError,'not committed'):magic.transact(w,r,p,payload)
            self.assertEqual(p['magicRunes'],original['magicRunes']);self.assertEqual(p['hp'],original['hp'])
            magic.transact(w,r,p,payload);magic.transact(w,r,p,payload)
            self.assertTrue(ascension.active(p));self.assertEqual(p['magicRunes']['balance'],0)
            magic.validate(p);p.update(status='downed',hp=0)
            magic.refresh(p);self.assertEqual(p['hp'],0)
            with self.assertRaisesRegex(ValueError,'safely'):magic.transact(w,r,p,dict(purchase='health',expectedRank=0,requestId='downed_purchase_'))

    def test_all_signatures_execute_with_cost_recharge_and_real_effects(self):
        for hero in CLASSES:
            with self.subTest(hero=hero):
                w,r,ps=start((hero,));p=ps[0]
                p['magicRunes'].update(ascended=True,balance=0,claims=[k for k in magic.SOURCES if k!='cache:dry_spring'])
                magic.refresh(p);a=ascension.ability(p)
                hero_skills.action(w,r,p,dict(action='skillEquip',slot='active1',ability=a['id']))
                adventure.enter(w,r,'brook','east');p.update(x=650,y=500)
                e=r['enemies'][0];e.update(x=710,y=500,hp=5000,maxHp=5000,homeX=710,homeY=500)
                before=e['hp'];mana=p['mana'];p['hp']=p['maxHp']//2
                w._cast_ability(r,p,p['abilities'].index(a['id']))
                self.assertLess(p['mana'],mana);self.assertGreater(hero_skills.ready_at(p,a['id']),time.monotonic());self.assertEqual(len(r['ascensionCasts']),1)
                ascension.tick(w,r,time.monotonic()+1)
                self.assertFalse(r['ascensionCasts'])
                if hero!='Healer':self.assertLess(e['hp'],before)
                else:self.assertGreater(p['skillBarrier'],0);self.assertGreater(p['hp'],p['maxHp']//2)
                if hero=='Druid':self.assertGreater(p['elderAccordUntil'],time.monotonic())
                with self.assertRaisesRegex(ValueError,'ready in'):w._cast_ability(r,p,p['abilities'].index(a['id']))
                hero_skills.validate(p)

    def test_ascended_passive_pairs_have_functional_hooks(self):
        import skill_casts as s
        for hero in CLASSES:
            w,r,ps=start((hero,));p=ps[0];p['magicRunes']['ascended']=True
            e=dict(id='passive-enemy',x=p['x']+30,y=p['y'],rootUntil=time.monotonic()+2,bleedUntil=time.monotonic()+3)
            now=time.monotonic();p['mana']=0
            if hero in ('Knight','Wizard'):
                self.assertGreater(ascension.outgoing(r,p,e,10,None,now),11)
            if hero=='Knight':s.shield(r,p,20);self.assertEqual(ascension.incoming(p,10,now),6)
            if hero=='Wizard':s.after_cast(r,p,dict(attackType='special',kind='barrier'),now);self.assertGreaterEqual(p['mana'],3)
            if hero=='Archer':e['x']=p['x']+300;self.assertGreater(ascension.outgoing(r,p,e,10,None,now),11);s.dashed(r,p,now);self.assertEqual(p['skillBarrier'],12)
            if hero=='Cleric':ascension.outgoing(r,p,e,10,None,now);self.assertGreater(e['ascWeakenUntil'],now);s.potion(w,r,p,'heal');self.assertEqual(p['skillBarrier'],18)
            if hero=='Rogue':s.dashed(r,p,now);self.assertGreater(p['invisibleUntil'],now);s.killed(r,p,e,now);self.assertEqual(p['mana'],6)
            if hero=='Druid':
                p['hp']-=10;before=p['hp'];ascension.outgoing(r,p,e,10,'summon',now);self.assertEqual(p['hp'],before+2)
                w._summon_companion(r,p,'fire_wolf',10,now);self.assertEqual(r['summons'][0]['trainingHp'],35)
            if hero=='Bard':s.after_cast(r,p,dict(attackType='special',kind='cadence'),now);self.assertEqual(p['skillBarrier'],8);ascension.outgoing(r,p,e,10,None,now);self.assertEqual(p['mana'],2)
            if hero=='Healer':p['hp']=1;self.assertEqual(ascension.incoming(p,10,now),2);s.revive_start(r,p,now);self.assertEqual(p['skillBarrier'],24);s.revived(r,p,p);self.assertEqual(p['skillBarrier'],25)

    def test_ascension_class_change_and_respec_do_not_refund_or_reset(self):
        w,r,ps=start();p=ps[0];p['magicRunes'].update(ascended=True,balance=0,claims=[k for k in magic.SOURCES if k!='cache:dry_spring'])
        a=ascension.ability(p);hero_skills.action(w,r,p,dict(action='skillEquip',slot='active1',ability=a['id']))
        hero_skills.commit_cooldown(p,a['id'],time.monotonic()+20);p['class']='Healer';hero_skills.ensure(r,p);magic.refresh(p)
        self.assertNotIn(a['id'],hero_skills.catalog(p));self.assertIn('second_dawn',hero_skills.catalog(p));self.assertTrue(ascension.active(p))
        hero_skills.action(w,r,p,dict(action='skillEquip',slot='active1',ability='second_dawn'))
        self.assertGreater(hero_skills.ready_at(p,'second_dawn'),time.monotonic()+18)
        before=copy.deepcopy(p['magicRunes']);hero_skills.action(w,r,p,dict(action='skillRespec'));self.assertEqual(before,p['magicRunes']);hero_skills.validate(p)

    def test_shrine_guard_conditions_world_and_personal_claims(self):
        w,r,ps=start(('Knight','Healer'));p,q=ps;adventure.enter(w,r,'brook','east')
        f=next(f for f in adventure.features(r) if f['id']=='attune_brook')
        with self.assertRaises(ValueError):region.interact(w,r,p,f)
        clear(w,r,p);region.interact(w,r,p,f);region.interact(w,r,p,f);region.interact(w,r,q,f)
        self.assertEqual(region.shrine_state(r)['active'],['brook']);self.assertEqual(p['magicRunes']['balance'],1);self.assertEqual(q['magicRunes']['balance'],1)
        adventure.enter(w,r,'watch','north');clear(w,r,p);f=next(f for f in adventure.features(r) if f['id']=='attune_watch')
        with self.assertRaisesRegex(ValueError,'register'):region.interact(w,r,p,f)
        chapter.evidence(r,'watch_register');region.interact(w,r,p,f)

    def test_optional_find_once_and_reports_earned_not_given_on_entry(self):
        w,r,ps=start();p=ps[0];adventure.enter(w,r,'dunmere','north')
        self.assertEqual(p['magicRunes']['balance'],0)
        adventure.enter(w,r,'hollow','west');f=next(f for f in adventure.features(r) if f['id']=='dry_spring')
        region.interact(w,r,p,f);finish(w,r,p);region.interact(w,r,p,f);self.assertEqual(p['magicRunes']['balance'],1)
        finish(w,r,p);report_chain(w,r,p,'chapter_outcome')
        self.assertEqual(p['magicRunes']['balance'],13);self.assertEqual(sum(magic.SOURCES[k] for k in p['magicRunes']['claims'] if k in ('report:failed_harvest','report:irrigation','report:mill_cellar','report:chapter_outcome')),7)

    def test_new_graph_reverse_exits_and_safe_arrivals_keep_old_dungeons(self):
        w,r,ps=start()
        for area in region.AREAS:
            for target,edge,entry in adventure.AREAS[area]['exits']:
                self.assertIn((area,entry,edge),adventure.AREAS[target]['exits'])
                adventure.enter(w,r,area,edge,source=target)
                for p in ps:self.assertTrue(terrain.walkable(r,p['x'],p['y']),(area,target))
        self.assertIn(('cave_entry','east','west'),adventure.AREAS['road']['exits'])
        self.assertIn(('tower_3','east','west'),adventure.AREAS['bridge']['exits'])

    def test_dunmere_bed_export_restart_and_partial_cellar_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=start(directory=directory);p=ps[0];report_chain(w,r,p,'irrigation')
            adventure.enter(w,r,'dunmere','north');runner(w,r,p);w.action(r['code'],p['id'],dict(action='chapterAccept',quest='mill_cellar'))
            bed=next(b for b in r['innRooms'] if not b['locked']);p.update(townInterior='inn',innFloor=2)
            adventure.rest(w,r,p,'bed_'+bed['id']);adventure.enter(w,r,'cellar','west');clear(w,r,p);region.begin_cellar(w,r)
            r['enemies'][0]['hp']=1;adventure.save(w,r)
            document=save_portability.project(adventure.snapshot(r));save_portability.validate(document)
            fresh=GameWorld(storage_dir=directory);restored=fresh.rooms[r['code']];rp=restored['players'][p['id']]
            self.assertEqual(restored['adventure']['current'],'dunmere');self.assertEqual(rp['innFloor'],2)
            adventure.enter(fresh,restored,'cellar','west');self.assertFalse(restored['enemies']);region.begin_cellar(fresh,restored)
            self.assertGreater(restored['enemies'][0]['hp'],1);clear(fresh,restored,rp)
            self.assertTrue(region.ensure(restored)['cellarComplete']);self.assertIsNone(region.blocked(restored,'fields','cellar'))

    def test_cellar_wipe_no_partial_boss_reappearance_or_double_penalty(self):
        w,r,ps=start();p=ps[0];report_chain(w,r,p,'irrigation');adventure.enter(w,r,'dunmere','north');runner(w,r,p)
        w.action(r['code'],p['id'],dict(action='chapterAccept',quest='mill_cellar'));adventure.enter(w,r,'cellar','west');clear(w,r,p);region.begin_cellar(w,r)
        r['runes']=100;p.update(status='downed',hp=0);w._check_party_wipe(r);self.assertEqual(r['runes'],60);w._check_party_wipe(r);self.assertEqual(r['runes'],60)
        adventure.enter(w,r,'cellar','west');self.assertFalse(r['enemies']);region.begin_cellar(w,r);self.assertEqual(len(r['enemies']),1)

    def test_activated_shrine_portal_carries_resources_and_recharge(self):
        w,r,ps=start();p=ps[0];adventure.enter(w,r,'brook','east');clear(w,r,p)
        f=next(f for f in adventure.features(r) if f['id']=='attune_brook');p.update(x=f['x'],y=f['y']+45);region.interact(w,r,p,f)
        p.update(hp=41,mana=37);p['abilityCooldowns'][p['abilities'][1]]=time.monotonic()+40
        village_portals.request(w,r,p,'home');village_portals.tick(w,r,r['portalChannel']['startedAt']+3.1)
        self.assertEqual(r['adventure']['current'],'home');village_portals.request(w,r,p,'brook');village_portals.tick(w,r,r['portalChannel']['startedAt']+3.1)
        self.assertEqual((p['hp'],p['mana']),(41,37));self.assertGreater(hero_skills.ready_at(p,p['abilities'][1]),time.monotonic()+38)
        self.assertEqual(r['adventure']['current'],'brook');self.assertTrue(terrain.walkable(r,p['x'],p['y']))

    def test_invalid_additive_records_rejected_without_changing_original(self):
        w,r,ps=start();document=save_portability.project(adventure.snapshot(r));save_portability.validate(document)
        for field,value in [('regionProgress',dict(version=99)),('travelShrines',dict(version=1,active=['unknown']))]:
            bad=copy.deepcopy(document);bad['progress']['world'][field]=value
            with self.assertRaises(ValueError):save_portability.validate(bad)
        bad=copy.deepcopy(document);bad['progress']['characters'][0]['magicRunes']['balance']=15
        with self.assertRaisesRegex(ValueError,'balance'):save_portability.validate(bad)
        self.assertEqual(document['progress']['characters'][0]['magicRunes']['balance'],0)

    def test_complete_sequential_chapters_through_real_objects_and_reports(self):
        w,r,ps=start();p=ps[0]
        def go(area):adventure.enter(w,r,area,'south');finish(w,r,p)
        def accept(key):
            go(chapter.SPECS[key]['hub']);runner(w,r,p);w.action(r['code'],p['id'],dict(action='chapterAccept',quest=key))
        def report(key,hub=None):
            go(hub or chapter.SPECS[key]['hub']);runner(w,r,p);w.action(r['code'],p['id'],dict(action='chapterReport',quest=key))
        def obj(key):interact(w,r,p,key)
        accept('hunter');go('road');obj('tracks');go('clearing');clear(w,r,p);obj('hunter');report('hunter')
        accept('bridge');go('camp');clear(w,r,p);obj('kit');go('bridge');obj('repair');report('bridge')
        accept('water');go('brook');obj('brook_outlet');clear(w,r,p);obj('attune_brook');go('mill_trail');obj('mill_wheel');report('water')
        accept('shrine');go('shrine');obj('altar')
        # Puzzle solution is functional fixture input, not a claim of human solving.
        adventure.puzzle_solved(w,r);clear(w,r,p);report('shrine')
        accept('watch');go('watch');clear(w,r,p);obj('watch_register');obj('attune_watch');go('hollow');clear(w,r,p);obj('attune_deepwood');go('network');obj('network_seal');report('watch')
        accept('ruins');go('ruins');obj('seal');clear(w,r,p);finish(w,r,p);obj('pumping_register');report('ruins')
        accept('border');go('ruins')
        from test_adventure import travel
        travel(w,r,'border');travel(w,r,'dunmere');report('border','dunmere')
        accept('failed_harvest');go('fields')
        for key in ('dry_ditch','rooted_crop','empty_granary'):obj(key)
        report('failed_harvest');accept('irrigation');go('mill');clear(w,r,p)
        for key in ('channel_west','channel_east','sluice_open'):obj(key)
        report('irrigation');accept('mill_cellar');go('cellar');clear(w,r,p);obj('cellar_begin');clear(w,r,p);obj('additive_ledger');report('mill_cellar')
        accept('chapter_outcome');go('fields');obj('field_restored');report('chapter_outcome')
        self.assertTrue(all(v=='complete' for v in chapter.ensure(r)['stages'].values()))
        self.assertEqual(p['magicRunes']['balance'],15);self.assertTrue(region.ensure(r)['cellarComplete'])
        before=copy.deepcopy(p['magicRunes']);w.action(r['code'],p['id'],dict(action='chapterReport',quest='chapter_outcome'));self.assertEqual(before,p['magicRunes'])
        document=save_portability.project(adventure.snapshot(r));save_portability.validate(document)
        magic.transact(w,r,p,dict(purchase='ascend',requestId='earned_chain_ascension_1234'))
        saved=adventure.snapshot(r);save_portability.validate(save_portability.project(saved))
        fresh=GameWorld();adventure.restore(fresh,saved);restored=fresh.rooms[r['code']]['players'][p['id']]
        self.assertTrue(ascension.active(restored));self.assertEqual(restored['magicRunes']['balance'],0)

    def test_shared_report_offline_member_late_join_and_retry(self):
        import session_flow
        w,r,ps=start(('Knight','Healer'));p,q=ps;runner(w,r,p)
        w.action(r['code'],p['id'],dict(action='chapterAccept',quest='hunter'));q['connected']=False
        r['adventure']['quests']['hunter']='complete';chapter.reconcile(r)
        w.action(r['code'],p['id'],dict(action='chapterReport',quest='hunter'))
        self.assertEqual((p['magicRunes']['balance'],q['magicRunes']['balance']),(1,1))
        c,pid=session_flow.join(w,dict(room=r['code'],name='Late hunter',hero='Wizard',requestId='late_hunter_request_12345678'))
        late=r['players'][pid];self.assertEqual(late['magicRunes']['balance'],1)
        self.assertEqual(chapter.ensure(r)['stages']['bridge'],'offered')
        magic.reconcile_reports(r);self.assertEqual(late['magicRunes']['balance'],1)
        self.assertEqual(r['runes'],0)

    def test_report_storage_failure_rolls_back_rewards_and_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=start(directory=directory);p=ps[0];runner(w,r,p)
            w.action(r['code'],p['id'],dict(action='chapterAccept',quest='hunter'));r['adventure']['quests']['hunter']='complete';chapter.reconcile(r)
            before=copy.deepcopy(p['magicRunes'])
            with patch.object(w.storage,'save_adventure',side_effect=OSError('simulated write failure')):
                with self.assertRaisesRegex(ValueError,'not committed'):w.action(r['code'],p['id'],dict(action='chapterReport',quest='hunter'))
            self.assertEqual(chapter.ensure(r)['stages']['hunter'],'ready-to-turn-in');self.assertEqual(before,p['magicRunes'])
            w.action(r['code'],p['id'],dict(action='chapterReport',quest='hunter'));self.assertEqual(p['magicRunes']['balance'],1)

    def test_new_hub_exits_remain_reachable_with_authoritative_solids(self):
        import town_layout
        for seed in range(24):
            v=town_layout.generate(seed+104729)
            gates=region.hub_exits(v,seed+104729)
            self.assertTrue(town_layout.accessible(v['townLayout'],[(gates['north'],48),(912,gates['east']),(480,460),(480,335)]),seed)
            town_layout.validate(v) # Including every added path segment.

    def test_cellar_legacy_area_and_ascended_targeting_respect_walls(self):
        w,r,ps=start(('Bard',));p=ps[0];adventure.enter(w,r,'cellar','west');p.update(x=230,y=180)
        e=r['enemies'][0];e.update(x=350,y=180,homeX=350,homeY=180)
        self.assertFalse(terrain.line_clear(r,p,e));before=e['hp']
        with self.assertRaises(ValueError):w._cast_ability(r,p,0)
        self.assertEqual(e['hp'],before)
        p['class']='Wizard';hero_skills.ensure(r,p);p['magicRunes']['ascended']=True
        with self.assertRaisesRegex(ValueError,'visible'):ascension.cast(w,r,p,ascension.ability(p))
