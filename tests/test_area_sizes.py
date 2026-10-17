"""Large Adventure fields preserve server combat and old cached layouts."""
import copy
import math
import tempfile
import time
import unittest

import adventure
import combat_environment as terrain
import enemy_roles
from game import GameWorld
from test_adventure import party, travel


class AreaSizeTests(unittest.TestCase):
    def test_selected_areas_only_and_bidirectional_arrivals(self):
        world, room, players = party(('Knight', 'Wizard'), companion=True)
        self.assertEqual(room['areaSize'], [960,540])
        travel(world,room,'road')
        self.assertEqual(world.state(room['code'],players[0]['id'])['areaSize'],[1800,900])
        self.assertEqual(adventure.edge_point(room,'east'),(1752,450))
        self.assertAlmostEqual(sum(p['x'] for p in room['players'].values())/3,900)
        self.assertEqual(players[0]['y'],108)
        travel(world,room,'crossroads')
        self.assertEqual(room['areaSize'],[1920,1080]);self.assertEqual(players[0]['x'],88)
        travel(world,room,'camp');self.assertEqual(room['areaSize'],[960,540])
        travel(world,room,'crossroads');self.assertEqual(players[0]['y'],972)
        travel(world,room,'clearing');self.assertEqual(room['areaSize'],[1440,900])
        travel(world,room,'shrine');self.assertEqual(room['areaSize'],[960,540])

    def test_authoritative_player_dash_and_enemy_bounds_use_large_field(self):
        w,r,ps=party();travel(w,r,'road');p=ps[0]
        p.update(x=1200,y=650)
        terrain.player_move(r,p,1,1,140,.1)
        self.assertAlmostEqual(p['x'],1214);self.assertAlmostEqual(p['y'],664)
        terrain.move(r,p,1900,1000)
        self.assertEqual((p['x'],p['y']),(1772,870))
        e=r['enemies'][0];e.update(x=1250,y=600,combatRole='ambusher')
        enemy_roles.approach(r,e,{'x':1350,'y':660},time.monotonic(),.1,20)
        self.assertGreater(e['x'],1250);self.assertGreater(e['y'],600)
        p.update(x=1300,y=650,dx=1,dy=0)
        w.action(r['code'],p['id'],dict(action='dash'))
        self.assertGreater(p['x'],1300);self.assertGreater(p['y'],540)

    def test_summon_and_projectile_beyond_legacy_field(self):
        w,r,ps=party(('Druid',));travel(w,r,'road');p=ps[0];now=time.monotonic()
        p.update(x=1500,y=700)
        w._summon_companion(r,p,'fire_wolf',5,now)
        s=r['summons'][0];self.assertEqual((s['x'],s['y']),(1468,672))
        e=r['enemies'][0];e.update(x=1650,y=692)
        w._launch_projectile(r,side='hero',owner_id=p['id'],target_id=e['id'],x=1500,y=692,
                             damage=5,color='#fff000',attack_class='Druid',speed=200)
        hp=e['hp']
        for i in range(10):w._tick_projectiles(r,now+(i+1)*.1)
        self.assertLess(e['hp'],hp)

    def test_large_features_revisit_save_and_old_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);travel(w,r,'road')
            feature=adventure.features(r)[0];self.assertGreater(feature['y'],510)
            e=r['enemies'][0];w._damage_enemy(r,ps[0],e,5)
            before=copy.deepcopy(r['enemies']);code=r['code']
            travel(w,r,'home');travel(w,r,'road')
            self.assertEqual(room_enemies(r),room_enemies({'enemies':before}))
            adventure.save(w,r);restored=GameWorld(storage_dir=directory).rooms[code]
            self.assertEqual(restored['adventure']['areas']['road']['size'],[1800,900])
            travel(w,r,'home')
            legacy=r['adventure']['areas']['road'];legacy.pop('size')
            legacy['enemies'][0].update(x=630,y=180,homeX=630,homeY=180)
            travel(w,r,'road')
            self.assertEqual(r['areaSize'],[960,540]);self.assertEqual(adventure.exits(r)[1]['x'],912)
            self.assertEqual(adventure.features(r)[0]['x'],405)
            self.assertEqual(r['enemies'][0]['x'],630)

    def test_large_reconnect_and_gather_ignore_offline_and_companion(self):
        w,r,ps=party(('Knight','Druid'),companion=True);travel(w,r,'road')
        e=next(e for e in adventure.exits(r) if e['id']=='crossroads')
        ps[0].update(x=e['x'],y=e['y']);w._disconnect_player(r,ps[1])
        w.action(r['code'],ps[0]['id'],dict(action='adventureTravel',destination='crossroads'))
        self.assertEqual(r['adventure']['current'],'crossroads')
        ps[0].update(x=1600,y=800)
        w.state(r['code'],ps[1]['id'])
        self.assertEqual((ps[1]['x'],ps[1]['y']),(1600,800))

    def test_gauntlet_and_puzzle_bounds_are_compact(self):
        self.assertEqual(terrain.dimensions({'mode':'gauntlet','areaSize':[1800,900]}),(960,540))
        self.assertEqual(terrain.dimensions({'mode':'adventure','phase':'puzzle','areaSize':[1800,900]}),(960,540))


def room_enemies(room):
    return [(e['id'],e['x'],e['y'],e['hp']) for e in room['enemies']]
