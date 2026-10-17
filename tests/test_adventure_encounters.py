"""Distributed territories preserve safe travel and persistent enemy defeats."""
import copy
import math
import tempfile
import unittest

import adventure
import combat_environment as terrain
from game import GameWorld
from test_adventure import party, travel


class AdventureEncounterTests(unittest.TestCase):
    def test_large_fields_have_separate_landmark_territories(self):
        world,room,_=party()
        for area in ('road','crossroads','clearing'):
            with self.subTest(area=area):
                state=adventure.build_area(world,room,area)
                groups={e['group'] for e in state['enemies']}
                self.assertEqual(len(groups),3)
                self.assertEqual(len(state['enemies']),4)
                centers=[(sum(e['x'] for e in state['enemies'] if e['group']==g)/
                          sum(e['group']==g for e in state['enemies']),
                          sum(e['y'] for e in state['enemies'] if e['group']==g)/
                          sum(e['group']==g for e in state['enemies'])) for g in groups]
                self.assertTrue(all(math.dist(a,b)>380 for i,a in enumerate(centers) for b in centers[i+1:]))

    def test_seeded_spawns_are_safe_for_all_entries_and_coop_sizes(self):
        world,room,_=party(('Knight','Druid','Wizard','Archer'))
        for seed in range(80):
            room['adventure']['seed']=seed
            for area in adventure.GROUPS:
                state=adventure.build_area(world,room,area)
                layout=dict(areaSize=state['size'],adventure={'current':area},environment=state['environment'])
                entries=[(x+offset,y) for target,edge,_ in adventure.AREAS[area]['exits']
                         for x,y in [adventure.edge_point(layout,edge,entry=True,destination=target)]
                         for offset in (-30,-10,10,30)]
                expected=sum(g[-1] for g in adventure.GROUPS[area])+3
                self.assertEqual(len(state['enemies']),expected)
                for e in state['enemies']:
                    self.assertTrue(terrain.walkable(layout,e['x'],e['y']))
                    self.assertTrue(all(math.dist((e['x'],e['y']),p)>=160 for p in entries))
                    self.assertEqual((e['x'],e['y']),(e['homeX'],e['homeY']))
                    if area=='bridge':self.assertGreater(e['x'],adventure.BRIDGE_LAYOUT['river']['right']+12)
                duplicate=adventure.build_area(world,room,area)
                self.assertEqual(state,duplicate)

    def test_only_nearby_pack_aggroes_and_retreat_remains_bounded(self):
        world,room,players=party();travel(world,room,'road');p=players[0]
        local=room['enemies'][0];p.update(x=local['homeX']+30,y=local['homeY'])
        nearby=local['group']
        for e in room['enemies']:
            returning=adventure.leash(world,room,e,p,1)
            self.assertEqual(e.get('aggro',False),e['group']==nearby)
            self.assertEqual(returning,e['group']!=nearby)
        p.update(x=local['homeX']+local['leashRadius']+30)
        self.assertTrue(adventure.leash(world,room,local,p,2))
        self.assertFalse(local['aggro'])

    def test_revisit_and_restart_keep_partial_defeats_without_new_mobs(self):
        with tempfile.TemporaryDirectory() as directory:
            world,room,players=party(storage_dir=directory);travel(world,room,'road');p=players[0]
            killed=room['enemies'][0]['id'];world._damage_enemy(room,p,room['enemies'][0],9999)
            world._damage_enemy(room,p,room['enemies'][0],5)
            before=adventure.clean_enemies(room['enemies']);runes=room['runes']
            travel(world,room,'home');travel(world,room,'road')
            self.assertEqual(adventure.clean_enemies(room['enemies']),before)
            adventure.save(world,room)
            restart=GameWorld(storage_dir=directory);restored=restart.rooms[room['code']]
            restart.state(room['code'],p['id']);travel(restart,restored,'road')
            self.assertEqual(adventure.clean_enemies(restored['enemies']),before)
            self.assertNotIn(killed,{e['id'] for e in restored['enemies']})
            self.assertEqual(restored['runes'],runes)

    def test_old_large_fields_scatter_survivors_once_without_healing_or_respawning(self):
        world,room,players=party();travel(world,room,'road')
        e=room['enemies'][0]
        old=[copy.deepcopy(e),copy.deepcopy(e)]
        for i,enemy in enumerate(old):
            enemy.update(id='road-road_wolves-'+str(i),group='road_wolves',
                         x=1210+i*40,y=300,homeX=1210+i*40,homeY=300,hp=13+i)
        room['enemies']=old;adventure.capture(room)
        state=room['adventure']['areas']['road'];state.pop('encounterLayout')
        state['defeated']=['road-road_wolves-2'];room['adventure']['claimed'].append('enemy:road-road_wolves-2')
        runes=room['runes'];travel(world,room,'home');travel(world,room,'road')
        self.assertEqual([e['id'] for e in room['enemies']],[e['id'] for e in old])
        self.assertEqual([e['hp'] for e in room['enemies']],[13,14])
        self.assertGreater(math.dist((room['enemies'][0]['x'],room['enemies'][0]['y']),
                                    (room['enemies'][1]['x'],room['enemies'][1]['y'])),380)
        scattered=adventure.clean_enemies(room['enemies'])
        travel(world,room,'home');travel(world,room,'road')
        self.assertEqual(adventure.clean_enemies(room['enemies']),scattered)
        self.assertEqual(state['defeated'],['road-road_wolves-2'])
        self.assertIn('enemy:road-road_wolves-2',room['adventure']['claimed'])
        self.assertEqual(room['runes'],runes)
        # Fully cleared and original compact cached areas remain untouched.
        state['enemies']=[];state.pop('encounterLayout')
        adventure.scatter_legacy_enemies('road',state,42);self.assertEqual(state['enemies'],[])
        compact=copy.deepcopy(state);compact.update(size=[960,540],enemies=old);compact.pop('encounterLayout')
        adventure.scatter_legacy_enemies('road',compact,42);self.assertEqual(compact['enemies'],old)
