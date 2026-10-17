"""Travel geometry, passive navigation and transactional woodland discoveries."""
import copy
import json
import math
import tempfile
import time
import unittest
from pathlib import Path
import adventure
import combat_environment as terrain
from game import GameWorld,CLASS_WEAPONS,ITEMS
from test_adventure import party,travel,interact,read_sign,kill,shrine,finish


class WoodlandReviewTests(unittest.TestCase):
    def test_sign_requires_deliberate_read_and_does_not_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Wizard'),storage_dir=directory);p,q=ps
            travel(w,r,'road');travel(w,r,'crossroads')
            sign=next(f for f in adventure.features(r) if f['id']=='sign');p.update(x=sign['x'],y=sign['y'])
            adventure.tick(w,r,time.monotonic());self.assertNotIn('camp',r['adventure']['discovered'])
            self.assertFalse(p['dialogue']);self.assertEqual(w.state(r['code'],p['id'])['interaction']['label'],'Read signpost')
            w.action(r['code'],p['id'],dict(action='interact'))
            self.assertEqual(w.state(r['code'],p['id'])['dialogue']['presentation'],'signpost')
            self.assertIn('Abandoned camp',p['dialogue']['text']);finish(w,r,p)
            view=w.state(r['code'],p['id'])['adventure']
            self.assertIsNone(view['nearby']);self.assertFalse(p['dialogue'])
            self.assertIsNone(view['signpost'])
            self.assertIsNone(w.state(r['code'],q['id'])['adventure']['signpost'])
            revision=r['adventure']['revision'];adventure.tick(w,r,time.monotonic())
            self.assertEqual(r['adventure']['revision'],revision)
            adventure.tick(w,r,time.monotonic())
            self.assertFalse(p['dialogue'])
            p['x']+=130;self.assertIsNone(adventure.signpost(r,p))
            restart=GameWorld(storage_dir=directory)
            self.assertIn('camp',restart.rooms[r['code']]['adventure']['discovered'])

    def test_offline_and_companions_do_not_read_signs(self):
        w,r,ps=party(companion=True);adventure.enter(w,r,'crossroads','west')
        sign=next(f for f in adventure.features(r) if f['id']=='sign')
        for p in r['players'].values():p.update(x=sign['x'],y=sign['y'],connected=bool(p.get('bot')))
        adventure.tick(w,r,time.monotonic());self.assertNotIn('camp',r['adventure']['discovered'])

    def test_reverse_directions_distinct_exits_and_safe_arrivals(self):
        w,r,ps=party(('Knight','Wizard','Druid'),companion=True)
        r['adventure']['bridge']=True
        for area,spec in adventure.AREAS.items():
            adventure.enter(w,r,area,'south')
            markers=adventure.exits(r)
            self.assertEqual(len({(e['x'],e['y']) for e in markers}),len(markers))
            for destination,edge,reverse in spec['exits']:
                back=next(e for e in adventure.AREAS[destination]['exits'] if e[0]==area)
                self.assertEqual(back[1:],(reverse,edge))
                if {area,destination}!={'crossroads','shrine'}:
                    a,b=spec['pos'],adventure.AREAS[destination]['pos']
                    self.assertTrue({'north':b[1]<a[1],'south':b[1]>a[1],'east':b[0]>a[0],'west':b[0]<a[0]}[edge])
                adventure.enter(w,r,destination,reverse,source=area)
                for p in r['players'].values():self.assertTrue(terrain.walkable(r,p['x'],p['y']))

    def test_broken_bridge_blocks_walk_dash_and_detours_then_only_span_opens(self):
        w,r,ps=party();adventure.enter(w,r,'bridge','east',source='camp');p=ps[0]
        for y in (30,100,260,400,510):
            p.update(x=680,y=y);terrain.move(r,p,490,y,avoid=True)
            self.assertGreaterEqual(p['x'],652)
        p.update(x=670,y=260,dx=-1,dy=0)
        w.action(r['code'],p['id'],dict(action='dash'));self.assertGreaterEqual(p['x'],652)
        with self.assertRaisesRegex(ValueError,'repair kit'):interact(w,r,p,'repair')
        r['adventure']['claimed'].append('repair_kit');interact(w,r,p,'repair')
        p.update(x=680,y=260);terrain.move(r,p,500,260);self.assertAlmostEqual(p['x'],500)
        p.update(x=680,y=150);terrain.move(r,p,500,150);self.assertGreaterEqual(p['x'],652)
        self.assertEqual(len(w.state(r['code'],p['id'])['environment']['barriers']),2)
        self.assertEqual(adventure.area_name(r,'bridge'),'Restored bridge')

    def test_bridge_collision_migrates_old_cache_and_survives_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);p=ps[0]
            adventure.enter(w,r,'bridge','east');r['adventure']['claimed'].append('repair_kit');interact(w,r,p,'repair')
            a=r['adventure'];a['areas']['bridge']['environment'].pop('barriers');adventure.save(w,r)
            # Mimic an older v1 record missing additive fields/derived terrain.
            path=w.storage.adventure_paths[r['adventure']['worldId']];record=json.loads(path.read_text())
            for area in record['room']['world']['areas'].values():area['environment'].pop('barriers',None)
            record['room']['world'].pop('rewardHistory',None);record['room']['world'].pop('notifications',None)
            for player in record['room']['players'].values():player.pop('trackedObjective',None)
            path.write_text(json.dumps(record))
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']]
            adventure.enter(restart,rr,'bridge','east')
            self.assertEqual(len(rr['environment']['barriers']),2)
            self.assertTrue(terrain.walkable(rr,604,260));self.assertFalse(terrain.walkable(rr,604,100))
            self.assertFalse(adventure.reward(restart,rr,'bridge',25,'warding_tonic'))

    def test_summon_at_broken_bank_spawns_on_traversable_ground(self):
        w,r,ps=party(('Druid',));adventure.enter(w,r,'bridge','east');p=ps[0]
        p.update(x=652,y=260);w._summon_companion(r,p,'fire_wolf',10,time.monotonic())
        s=r['summons'][0];self.assertTrue(terrain.walkable(r,s['x'],s['y']))
        self.assertGreaterEqual(s['x'],652)

    def test_tracking_is_personal_routes_known_trails_and_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Druid'),storage_dir=directory);p,q=ps
            w.action(r['code'],p['id'],dict(action='adventureTrack',objective='bridge'))
            travel(w,r,'road');travel(w,r,'crossroads');read_sign(w,r,p)
            travel(w,r,'camp');kill(w,r,p);interact(w,r,p,'kit')
            travel(w,r,'crossroads');travel(w,r,'road')
            a=w.state(r['code'],p['id'])['adventure']
            self.assertEqual(a['tracked']['nextExit'],'crossroads') # Locked shortcut cannot be recommended.
            self.assertEqual(q['trackedObjective'],'hunter')
            self.assertEqual(next(q for q in a['journal'] if q['id']=='region')['visibility'],'undiscovered')
            with self.assertRaises(ValueError):adventure.track(w,r,p,[])
            with self.assertRaises(ValueError):adventure.track(w,r,p,'region')
            restart=GameWorld(storage_dir=directory);self.assertEqual(restart.rooms[r['code']]['players'][p['id']]['trackedObjective'],'bridge')

    def test_optional_finds_reward_once_without_changing_quests(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Wizard'),storage_dir=directory);p=ps[0];before=copy.deepcopy(r['adventure']['quests'])
            travel(w,r,'road');interact(w,r,p,'cache');money=r['runes']
            self.assertNotIn('cache',[f['id'] for f in adventure.features(r)])
            self.assertFalse(adventure.reward(w,r,'discovery:cache',12,'healing_draught'))
            self.assertEqual(r['runes'],money)
            travel(w,r,'crossroads');travel(w,r,'clearing');interact(w,r,p,'watch');money=r['runes']
            interact(w,r,p,'watch');self.assertEqual(r['runes'],money)
            self.assertEqual(r['adventure']['quests'],before)
            self.assertEqual(len(w.state(r['code'],p['id'])['adventure']['discoveries']),2)
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']]
            self.assertFalse(adventure.reward(restart,rr,'discovery:watch',8,'mana_draught'))
            self.assertEqual(rr['runes'],money)

    def test_all_hero_rewards_and_full_pouch_receipts(self):
        for hero,weapon in CLASS_WEAPONS.items():
            with self.subTest(hero=hero):
                w,r,ps=party((hero,));p=ps[0]
                adventure.reward(w,r,'shrine',35,'class_weapon')
                self.assertEqual(p['pendingRewards']['shrine']['options'],['rescuers_cuirass','stormguard_charm'])
                w.action(r['code'],p['id'],dict(action='adventureReward',reward='shrine',item='rescuers_cuirass'))
                self.assertEqual(p['inventory'][-1]['name'],ITEMS['rescuers_cuirass']['name'])
                p['inventory']=[w._make_item('healing_draught') for _ in range(10)]
                before=r['runes'];adventure.reward(w,r,'region',70,'class_reward')
                self.assertEqual(r['runes'],before+70)
                w.action(r['code'],p['id'],dict(action='adventureReward',reward='region',item='aegis_of_dawn',delivery='sell'))
                expected=ITEMS['aegis_of_dawn']
                self.assertEqual(r['runes'],before+70+expected['sell'])
                receipt=r['adventure']['rewardHistory'][-1]['recipients'][0]
                self.assertEqual(receipt['name'],p['name']);self.assertEqual(receipt['convertedRunes'],expected['sell'])
                self.assertEqual(receipt['item'],expected['name'])

    def test_travel_readiness_names_humans_and_disconnect_releases_trip(self):
        w,r,ps=party(('Knight','Druid'),companion=True);p,q=ps
        e=adventure.exits(r)[0];p.update(x=e['x'],y=e['y']);q.update(x=200,y=450)
        w.action(r['code'],p['id'],dict(action='adventureTravel',destination='road'))
        statuses={m['id']:m['state'] for m in w.state(r['code'],p['id'])['adventure']['travelMembers']}
        self.assertEqual(statuses,{p['id']:'ready',q['id']:'gather'})
        q.update(x=e['x'],y=e['y']);self.assertEqual(adventure.view(w,r,p)['travelMembers'][1]['state'],'confirm')
        w._disconnect_player(r,q);adventure.tick(w,r,time.monotonic())
        self.assertEqual(r['adventure']['current'],'road')
        w.state(r['code'],q['id']);self.assertLess(math.dist((p['x'],p['y']),(q['x'],q['y'])),1)

    def test_completed_shrine_and_bridge_survive_new_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);p=ps[0]
            adventure.enter(w,r,'shrine','north');shrine(w,r,p)
            adventure.enter(w,r,'bridge','east');r['adventure']['claimed'].append('repair_kit');interact(w,r,p,'repair')
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']]
            adventure.enter(restart,rr,'shrine','north');self.assertFalse(rr['environment']['zones']);self.assertFalse(rr['enemies'])
            self.assertTrue(adventure.view(restart,rr,rr['players'][p['id']])['shrineRestored'])
            adventure.enter(restart,rr,'bridge','east');self.assertEqual(adventure.area_name(rr,'bridge'),'Restored bridge')


if __name__=='__main__':unittest.main()
