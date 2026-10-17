import tempfile
import unittest
import uuid
from unittest.mock import patch
import adventure
import interactions
import session_flow
from game import GameWorld
from test_adventure import party,finish,travel


class ControlFlowTests(unittest.TestCase):
    def test_released_revive_cannot_start_from_late_request(self):
        w,r,ps=party(('Knight','Healer'));travel(w,r,'road');p,ally=ps
        p.update(x=500,y=400);ally.update(x=510,y=400,hp=0,status='downed')
        w.action(r['code'],p['id'],dict(action='stopRevive',holdToken='released'))
        w.action(r['code'],p['id'],dict(action='interact',target='revive:'+ally['id'],holdToken='released'))
        self.assertFalse(p['reviving'])

    def test_reconnect_retains_safe_solo_position_in_current_area(self):
        w,r,ps=party();travel(w,r,'road');p=ps[0];p.update(x=1050,y=400)
        w.action(r['code'],p['id'],dict(action='disconnect'));w.state(r['code'],p['id'])
        self.assertEqual((p['x'],p['y']),(1050,400));self.assertEqual(r['adventure']['current'],'road')
    def test_distinct_worlds_creation_retry_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            w=GameWorld(storage_dir=directory)
            request=dict(requestId=uuid.uuid4().hex,instance='boot',mode='adventure',hero='Knight',name='Hunter A',title='Adventure A',skipIntro=True)
            code,pid=session_flow.create(w,request,'boot');a=w.rooms[code];finish(w,a,a['players'][pid]);travel(w,a,'road')
            first=a['adventure']['worldId'];session_flow.create(w,request,'boot')
            self.assertEqual(len(w.rooms),1)
            second={**request,'requestId':uuid.uuid4().hex,'title':'Adventure B'}
            code_b,pid_b=session_flow.create(w,second,'boot')
            self.assertNotEqual(first,w.rooms[code_b]['adventure']['worldId']);self.assertNotEqual(pid,pid_b)
            self.assertEqual(w.rooms[code_b]['adventure']['visited'],['home']);self.assertIn('road',a['adventure']['visited'])
            restart=GameWorld(storage_dir=directory)
            self.assertEqual(session_flow.create(restart,request,'different boot'),(code,pid))
            self.assertEqual(restart.rooms[code]['adventure']['worldId'],first);self.assertIn('road',restart.rooms[code]['adventure']['visited'])
            with self.assertRaisesRegex(ValueError,'restarted'):session_flow.create(restart,{**second,'requestId':uuid.uuid4().hex},'different boot')

    def test_gauntlet_creation_keeps_lobby_and_mode_separate(self):
        w=GameWorld();request=dict(requestId=uuid.uuid4().hex,instance='b',mode='gauntlet',hero='Wizard',name='Mage')
        c,p=session_flow.create(w,request,'b');r=w.rooms[c]
        self.assertEqual(r['phase'],'lobby');self.assertEqual(r['players'][p]['abilities'],[])
        self.assertFalse(adventure.active(r));self.assertEqual(session_flow.create(w,request,'b'),(c,p))

    def test_party_join_is_idempotent_and_new_character_bound_to_world(self):
        w,r,ps=party();request=dict(requestId=uuid.uuid4().hex,room=r['code'],name='Friend',hero='Healer')
        code,pid=session_flow.join(w,request);self.assertEqual(code,r['code'])
        self.assertEqual(session_flow.join(w,request),(code,pid));self.assertEqual(len(r['players']),2)
        self.assertEqual(r['players'][pid]['class'],'Healer');self.assertNotEqual(r['players'][pid]['characterId'],ps[0]['characterId'])
        with self.assertRaisesRegex(ValueError,'already in'):session_flow.join(w,{**request,'requestId':uuid.uuid4().hex})

    def test_revive_priority_and_repeated_hold(self):
        w,r,ps=party(('Knight','Healer'));travel(w,r,'road');e=adventure.exits(r)[0]
        p,ally=ps;p.update(x=e['x'],y=e['y']);ally.update(x=p['x']+20,y=p['y'],status='downed',hp=0)
        target=interactions.public(w,r,p);self.assertEqual(target['kind'],'revive')
        w.action(r['code'],p['id'],dict(action='interact',target=target['id'],requestId='one'))
        started=p['reviveStarted'];w.action(r['code'],p['id'],dict(action='interact',target=target['id'],requestId='two'))
        self.assertEqual(p['reviveStarted'],started);self.assertEqual(r['adventure']['current'],'road')

    def test_stale_target_cannot_open_something_else(self):
        w,r,ps=party();p=ps[0];p.update(x=480,y=400)
        with self.assertRaisesRegex(ValueError,'Nothing|target changed'):w.action(r['code'],p['id'],dict(action='interact',target='feature:missing'))
        self.assertEqual(r['adventure']['quests']['hunter'],'active')

    def test_old_input_cannot_reactivate_departed_player_or_cross_door(self):
        w,r,ps=party();p=ps[0];scene=interactions.scene(r,p)
        w.action(r['code'],p['id'],dict(action='disconnect'))
        w.action(r['code'],p['id'],dict(action='input',x=1,y=0,sequence=2,scene=scene,epoch=0))
        self.assertFalse(p['connected']);self.assertEqual(p['dx'],0)
        w.state(r['code'],p['id']);epoch=p['inputEpoch']
        w.action(r['code'],p['id'],dict(action='input',x=1,y=0,sequence=3,scene=scene+':old',epoch=epoch));self.assertEqual(p['dx'],0)
        w.action(r['code'],p['id'],dict(action='input',x=1,y=0,sequence=4,scene=scene,epoch=epoch));self.assertEqual(p['dx'],1)

    def test_interaction_only_commits_one_save(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);travel(w,r,'road');p=ps[0]
            f=next(f for f in adventure.features(r) if f['id']=='tracks');p.update(x=f['x'],y=f['y'])
            with patch.object(w.storage,'save_adventure',wraps=w.storage.save_adventure) as commit:
                w.action(r['code'],p['id'],dict(action='interact'));self.assertEqual(commit.call_count,1)

    def test_rootwater_access_without_unrelated_quest(self):
        w,r,ps=party();travel(w,r,'road');p=ps[0];e=next(e for e in adventure.exits(r) if e['id']=='cave_entry')
        self.assertFalse(e['locked']);self.assertAlmostEqual(e['y']/r['areaSize'][1],.78)
        p.update(x=e['x']-72,y=e['y']);target=interactions.public(w,r,p)
        self.assertEqual(target['id'],'exit:cave_entry');self.assertIn('Enter Rootwater',target['label'])
        w.action(r['code'],p['id'],dict(action='interact',target=target['id']))
        self.assertEqual(r['adventure']['current'],'cave_entry');self.assertEqual(r['adventure']['quests']['hunter'],'active')
