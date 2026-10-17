import copy
import tempfile
import time
import unittest
from unittest.mock import patch
import adventure
import save_portability
import village_portals as portals
from game import GameWorld
from test_adventure import party,travel


class VillagePortalTests(unittest.TestCase):
    def safe(self,room,players):
        for i,p in enumerate(players):p.update(x=480+i*20,y=650,hp=70,mana=40)
        for e in room['enemies']:e.update(x=1100,y=250)

    def complete(self,world,room):
        portals.tick(world,room,room['portalChannel']['startedAt']+3.1)

    def test_recall_return_no_heal_no_recharge_no_enemy_respawn(self):
        w,r,ps=party();travel(w,r,'road');self.safe(r,ps);p=ps[0]
        r['enemies'][0]['hp']-=3;before=copy.deepcopy(r['enemies']);deadline=time.monotonic()+10
        p['abilityCooldowns'][p['abilities'][1]]=deadline
        portals.request(w,r,p,'home');self.complete(w,r)
        self.assertEqual((r['adventure']['current'],p['hp'],p['mana']),('home',70,40))
        self.assertEqual(p['abilityCooldowns'][p['abilities'][1]],deadline)
        self.assertEqual(p['soulCrystal']['charge'],0)
        p.update(**portals.shrine(r))
        with self.assertRaises(ValueError):portals.request(w,r,p,'road')
        travel(w,r,'road')
        self.assertEqual(r['adventure']['current'],'road');self.assertEqual([(e['id'],e['hp']) for e in r['enemies']],[(e['id'],e['hp']) for e in before])
        self.assertEqual(r['adventure']['portalReturn']['area'],'road')

    def test_connected_humans_confirm_offline_and_companion_do_not_block(self):
        w,r,ps=party(('Knight','Druid','Archer'),companion=True);travel(w,r,'road');self.safe(r,ps)
        ps[2]['connected']=False
        portals.request(w,r,ps[0],'home');self.assertIsNone(r['portalChannel']['startedAt'])
        portals.request(w,r,ps[1],'home');self.assertIsNotNone(r['portalChannel']['startedAt'])
        start=r['portalChannel']['startedAt'];portals.request(w,r,ps[1],'home');self.assertEqual(r['portalChannel']['startedAt'],start)
        self.complete(w,r);self.assertEqual(r['adventure']['current'],'home')

    def test_movement_damage_nearby_enemy_and_seal_prevent_escape(self):
        for cause in ('move','damage','enemy','seal'):
            w,r,ps=party();travel(w,r,'road');self.safe(r,ps);p=ps[0]
            if cause=='seal':
                r['adventure']['locked']=True
                with self.assertRaises(ValueError):portals.request(w,r,p,'home')
                continue
            portals.request(w,r,p,'home')
            if cause=='move':p['x']+=15
            if cause=='damage':p['damageTaken']=p.get('damageTaken',0)+1
            if cause=='enemy':r['enemies'][0].update(x=p['x']+100,y=p['y'])
            self.complete(w,r);self.assertNotIn('portalChannel',r);self.assertEqual(r['adventure']['current'],'road')

    def test_return_survives_save_import_and_restart_without_private_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);travel(w,r,'road');self.safe(r,ps)
            portals.request(w,r,ps[0],'home');self.complete(w,r)
            doc=save_portability.project(adventure.snapshot(r));clean,_=save_portability.validate(doc)
            self.assertEqual(clean['progress']['world']['portalReturn']['area'],'road')
            self.assertNotIn(ps[0]['characterId'],str(doc));fresh=GameWorld(storage_dir=directory)
            self.assertEqual(fresh.rooms[r['code']]['adventure']['portalReturn']['area'],'road')
            bad=copy.deepcopy(doc);bad['progress']['world']['portalReturn']['positions']=[[100000,3]]
            with self.assertRaises(ValueError):save_portability.validate(bad)

    def test_new_player_cannot_teleport_unknown_routes_or_use_while_downed(self):
        w,r,ps=party();p=ps[0]
        with self.assertRaises(ValueError):portals.request(w,r,p,'camp')
        travel(w,r,'road');p['status']='downed'
        with self.assertRaises(ValueError):portals.request(w,r,p,'home')
