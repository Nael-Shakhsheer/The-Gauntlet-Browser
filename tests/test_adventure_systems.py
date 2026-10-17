import copy
import tempfile
import time
import unittest
from unittest.mock import patch
import acquisitions,adventure,cottage,dialogue_choices,feedback,hero_skills,magic_runes
import outdoor_respawns as respawns
import progression,save_portability,soul_crystal,village_portals
from game import GameWorld
from test_adventure import party,travel,finish
from test_expansion import start


class AdventureSystemsTests(unittest.TestCase):
    def test_all_eight_heroes_learn_equip_and_use_early_woodland_skills(self):
        for hero in __import__('game').CLASSES:
            with self.subTest(hero=hero):
                w,r,ps=start((hero,));p=ps[0];tree=hero_skills.view(r,p)
                self.assertTrue(tree['safe']);self.assertEqual(tree['points'],2)
                candidates=[n for n in tree['nodes'] if n['type']=='ability' and not n['unlocked'] and n['current']['attackType']=='special' and n['cost']<=2 and all(hero_skills.unlocked(p,k) for k in n['requires'])]
                self.assertTrue(candidates);n=next((n for n in candidates if n['id']=='life_barrier'),candidates[0])
                w.action(r['code'],p['id'],dict(action='skillUnlock',node=n['id'],expectedRank=0))
                w.action(r['code'],p['id'],dict(action='skillEquip',slot='active1',ability=n['id']))
                travel(w,r,'road');p.update(x=500,y=400,hp=p['maxHp']//2)
                r['environment']={};r['enemies'][0].update(x=550,y=400);p['abilityCooldowns'][n['id']]=0;p['skillSlotCooldowns']['active1']=0
                w._cast_ability(r,p,1);self.assertTrue(p['abilityCooldowns'].get(n['id'],0)>0 or n['id'] in p.get('activeSummons',{}))

    def test_ascension_requires_dunmere_but_old_ascension_is_preserved(self):
        w,r,ps=start();p=ps[0]
        for key in magic_runes.SOURCES:magic_runes.claim(p,key)
        with self.assertRaisesRegex(ValueError,'Dunmere'):magic_runes.transact(w,r,p,dict(purchase='ascend',requestId='test_gate_ascend_123'))
        p['magicRunes']['ascended']=True;hero_skills.ensure(r,p);self.assertTrue(p['magicRunes']['ascended'])

    def test_dialogue_topics_attitudes_postpone_accept_stale_and_inspection(self):
        w,r,ps=start();p=ps[0];f=next(f for f in adventure.features(r) if f['id']=='runner');p.update(x=f['x'],y=f['y'])
        adventure.interact(w,r,p,f);d=progression.dialogue(p)
        self.assertTrue(d['choices']);payload=dict(action='dialogueChoice',id=d['id'],page=d['page'],revision=d['revision'],choice='region')
        w.action(r['code'],p['id'],payload);self.assertIn('Minotaur',progression.dialogue(p)['text'])
        with self.assertRaisesRegex(ValueError,'stale'):w.action(r['code'],p['id'],payload)
        def choose(key):
            view=progression.dialogue(p);w.action(r['code'],p['id'],dict(action='dialogueChoice',id=view['id'],page=view['page'],revision=view['revision'],choice=key))
        choose('back');choose('skeptical');choose('back');choose('leave')
        self.assertEqual(r['adventure']['chapter']['stages']['hunter'],'offered')
        adventure.interact(w,r,p,f);choose('accept');self.assertEqual(r['adventure']['chapter']['stages']['hunter'],'accepted')
        self.assertEqual(p['dialogueDecisions']['attitudes']['adventure_runner'],'skeptical');dialogue_choices.validate(p)
        progression.inspect(p,'A rock','No conversational choices.');self.assertNotIn('choices',progression.dialogue(p))

    def test_crystal_life_receipts_support_companion_range_and_cap(self):
        w,r,ps=party(('Knight','Healer','Druid'),companion=True);travel(w,r,'road');e=r['enemies'][0]
        for p in ps:p.update(x=e['x']+10,y=e['y']);soul_crystal.ensure(p)['charge']=0
        ps[2]['connected']=False;soul_crystal.grant(r,e);soul_crystal.grant(r,e)
        self.assertEqual([soul_crystal.ensure(p)['charge'] for p in ps],[1,1,0])
        e=dict(e,id=e['id']+'~1',lifeGeneration=1,miniBoss=True);soul_crystal.grant(r,e)
        self.assertEqual(ps[1]['soulCrystal']['charge'],4)
        e.update(lifeGeneration=2,boss=True);ps[1]['soulCrystal']['charge']=19;soul_crystal.grant(r,e)
        self.assertEqual(ps[1]['soulCrystal']['charge'],20)

    def test_respawn_generations_only_unoccupied_full_groups_and_no_unique_rewards(self):
        w,r,ps=party();travel(w,r,'road');p=ps[0];group=r['enemies'][0]['group'];enemies=[e for e in r['enemies'] if e['group']==group]
        for e in enemies:w._damage_enemy(r,p,e,9999)
        g=r['adventure']['areas']['road']['respawns']['groups'][group];self.assertEqual(g['generation'],0);self.assertIsNotNone(g['eligibleAt'])
        runes=r['runes'];facts=copy.deepcopy(r['adventure']['claimed']);charges=copy.deepcopy(p['soulCrystal']['receipts'])
        with patch.object(respawns.time,'time',return_value=g['eligibleAt']+1):respawns.tick(w,r,time.monotonic()+3)
        self.assertFalse(any(e['group']==group for e in r['enemies']))
        travel(w,r,'home')
        with patch.object(respawns.time,'time',return_value=g['eligibleAt']+1):respawns.tick(w,r,time.monotonic()+6)
        self.assertEqual(g['generation'],1);travel(w,r,'road')
        born=[e for e in r['enemies'] if e['group']==group];self.assertEqual(len(born),len(enemies));self.assertTrue(all(e['lifeGeneration']==1 for e in born))
        for e in born:w._damage_enemy(r,p,e,9999)
        self.assertEqual(r['runes']-runes,len(born));self.assertEqual(r['adventure']['claimed'],facts)
        for area in ('camp','clearing','shrine','ruins','tower_1'):
            state=adventure.build_area(w,r,area);respawns.prepare(area,state)
            self.assertTrue(all('shrine' not in k and k not in respawns.EXCLUDED for k in state.get('respawns',{}).get('groups',{})))

    def test_shrine_free_crystal_atomic_failure_and_interrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Healer'),storage_dir=directory);travel(w,r,'road')
            for p in ps:p.update(x=480,y=650,hp=50,mana=30)
            for e in r['enemies']:e.update(x=1200,y=200)
            ps[1]['soulCrystal']['charge']=19
            with self.assertRaisesRegex(ValueError,'20 souls'):village_portals.request(w,r,ps[0],'home','crystal')
            self.assertNotIn('portalChannel',r)
            ps[1]['soulCrystal']['charge']=20
            for p in ps:village_portals.request(w,r,p,'home','crystal')
            when=r['portalChannel']['startedAt']+3.1
            with patch.object(w.storage,'save_adventure',side_effect=OSError('disk')):village_portals.tick(w,r,when)
            self.assertEqual(r['adventure']['current'],'road');ps=[r['players'][p['id']] for p in ps]
            self.assertEqual([p['soulCrystal']['charge'] for p in ps],[20,20])
            for p in ps:village_portals.request(w,r,p,'home','crystal')
            village_portals.tick(w,r,r['portalChannel']['startedAt']+3.1)
            self.assertEqual([p['soulCrystal']['charge'] for p in ps],[0,0]);self.assertEqual([p['hp'] for p in ps],[50,50])
            r['adventure']['discovered'].append('brook');r['adventure']['travelShrines']=dict(version=1,active=['brook'])
            for p in ps:p.update(**village_portals.shrine(r))
            for p in ps:village_portals.request(w,r,p,'brook','shrine')
            village_portals.tick(w,r,r['portalChannel']['startedAt']+3.1)
            self.assertEqual(r['adventure']['current'],'brook');self.assertEqual([p['soulCrystal']['charge'] for p in ps],[0,0])

    def test_cottage_idempotency_shared_cost_no_recharge_or_bed_change(self):
        w,r,ps=party();p=ps[0];p.update(townInterior='cottage',x=480,y=220,hp=21,mana=13);r['runes']=10
        crystal=copy.deepcopy(p['soulCrystal']);checkpoint=copy.deepcopy(r['adventure']['checkpoint']);cd=copy.deepcopy(p['abilityCooldowns'])
        payload=dict(requestId='cottage_treat_request_123',serviceRevision=0)
        cottage.treat(w,r,p,payload);cottage.treat(w,r,p,payload)
        self.assertEqual(r['runes'],5);self.assertEqual((p['hp'],p['mana']),(p['maxHp'],p['maxMana']))
        cottage.treat(w,r,p,dict(requestId='cottage_full_request_123',serviceRevision=1));self.assertEqual(r['runes'],5)
        p['hp']=2;r['runes']=0
        with self.assertRaisesRegex(ValueError,'shared'):cottage.treat(w,r,p,dict(requestId='cottage_poor_request_123',serviceRevision=2))
        self.assertEqual((p['soulCrystal'],p['abilityCooldowns'],r['adventure']['checkpoint']),(crystal,cd,checkpoint))

    def test_confirmed_items_pending_conversion_rune_and_failed_save_notifications(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);p=ps[0];acquisitions.prime(r)
            p['inventory'].append(w._make_item('mana_draught'));magic_runes.claim(p,'shrine:brook')
            with patch.object(w.storage,'save_adventure',side_effect=OSError('disk')):self.assertFalse(adventure.save(w,r))
            kinds=lambda:[e['kind'] for e in feedback.view(r,p['id'])['events']]
            self.assertNotIn('acquisition',kinds());self.assertNotIn('magic_acquired',kinds())
            adventure.save(w,r);self.assertIn('acquisition',kinds());self.assertIn('magic_acquired',kinds())
            total=kinds().count('acquisition');adventure.save(w,r);self.assertEqual(kinds().count('acquisition'),total)
            __import__('adventure_rewards').offer(p,'shrine','Restored shrine');adventure.save(w,r)
            e=next(e for e in feedback.view(r,p['id'])['events'] if e['kind']=='acquisition' and 'pending' in e['destination']);self.assertNotIn('itemKey',e)

    def test_new_records_roundtrip_restart_old_compatibility_and_threshold(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);travel(w,r,'road');p=ps[0]
            enemy=r['enemies'][0];w._damage_enemy(r,p,enemy,9999);adventure.save(w,r)
            doc=save_portability.project(adventure.snapshot(r));save_portability.validate(doc)
            old=copy.deepcopy(doc)
            for char in old['progress']['characters']:
                for k in ('soulCrystal','dialogueDecisions','cottageReceipts'):char.pop(k,None)
            for cache in old['progress']['world']['areas'].values():cache.pop('respawns',None)
            save_portability.validate(old)
            fresh=GameWorld(storage_dir=directory);saved=fresh.rooms[r['code']]
            self.assertEqual(saved['players'][p['id']]['soulCrystal'],p['soulCrystal'])
            self.assertEqual(saved['adventure']['areas']['road']['respawns'],r['adventure']['areas']['road']['respawns'])
            adventure.enter(w,r,'fields','west');e=next(e for e in adventure.exits(r) if e['id']=='eastern_threshold');self.assertEqual(e['edge'],'east')
            travel(w,r,'eastern_threshold');self.assertIn('fields',[e['id'] for e in adventure.exits(r)])
            f=next(f for f in adventure.features(r) if f['id']=='east_landmark');p.update(x=f['x'],y=f['y']);adventure.interact(w,r,p,f)
            self.assertIn('discovery:east_landmark',r['adventure']['claimed']);save_portability.validate(save_portability.project(adventure.snapshot(r)))

    def test_legacy_cleared_group_gets_a_future_timer_and_partial_fight_is_kept(self):
        w,r,ps=party();travel(w,r,'road');state=r['adventure']['areas']['road'];state.pop('respawns')
        group=r['enemies'][0]['group'];dead=[e for e in r['enemies'] if e['group']==group]
        state['defeated']=[e['id'] for e in dead];state['enemies']=[e for e in state['enemies'] if e['group']!=group]
        before=time.time();respawns.prepare('road',state,w,r);g=state['respawns']['groups'][group]
        self.assertGreaterEqual(g['eligibleAt'],before+600);self.assertFalse(any(e['group']==group for e in state['enemies']))
        partial=next(g for k,g in state['respawns']['groups'].items() if k!=group)
        partial['deaths'][partial['templates'][0]['id']]=before
        self.assertIsNone(partial['eligibleAt']);self.assertEqual(partial['generation'],0)

    def test_cottage_failure_restores_pool_and_resources_and_import_rejects_bad_records(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);p=ps[0];p.update(townInterior='cottage',x=480,y=220,hp=17,mana=12);r['runes']=10
            with patch.object(w.storage,'save_adventure',side_effect=OSError('disk')):
                with self.assertRaisesRegex(ValueError,'No Runes spent'):cottage.treat(w,r,p,dict(requestId='cottage_disk_retry_123',serviceRevision=0))
            self.assertEqual((r['runes'],p['hp'],p['mana']),(10,17,12))
            doc=save_portability.project(adventure.snapshot(r))
            for field,value in [('soulCrystal',dict(version=1,charge=21,receipts={})),('dialogueDecisions',dict(version=1,attitudes={},topics=[[]]))]:
                bad=copy.deepcopy(doc);bad['progress']['characters'][0][field]=value
                with self.assertRaises(ValueError):save_portability.validate(bad)

    def test_acquisition_baseline_does_not_copy_inventory_on_steady_ticks(self):
        w,r,ps=party();acquisitions.prime(r)
        with patch.object(acquisitions,'snapshot',wraps=acquisitions.snapshot) as copies:
            for _ in range(100):acquisitions.prime(r)
            self.assertEqual(copies.call_count,0)

    def test_transport_invitation_waits_for_distant_teammate_and_shows_readiness(self):
        w,r,ps=party(('Knight','Healer'));travel(w,r,'road');p,q=ps
        r['enemies']=[];p.update(x=400,y=600);q.update(x=800,y=600)
        village_portals.request(w,r,p,'home','crystal')
        self.assertIsNone(r['portalChannel']['startedAt']);view=village_portals.view(r,p)
        self.assertEqual(view['channel']['ready'],1);self.assertIn('gather',view['channel']['waiting'][0])
        q.update(x=430,y=600);village_portals.request(w,r,q,'home','crystal')
        self.assertIsNotNone(r['portalChannel']['startedAt'])
        q['x']+=15;village_portals.tick(w,r,r['portalChannel']['startedAt']+.2)
        self.assertNotIn('portalChannel',r);self.assertIn('No charge spent',village_portals.view(r,p)['message'])
        self.assertEqual([p['soulCrystal']['charge'] for p in ps],[20,20])
