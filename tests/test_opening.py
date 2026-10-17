"""Authoritative state/recovery checks. Forced kills are functional fixtures."""
import copy
import tempfile
import time
import unittest
from unittest.mock import patch
import adventure
import opening
import hero_skills
import session_flow
import save_portability
from game import GameWorld,CLASSES


def new(heroes=('Knight',),directory=None,skip=False,companion=False):
    w=GameWorld(storage_dir=directory);c,h=w.create_room('Caravan tester')
    ids=[h]+[w.join_room(c,'Friend')[1] for _ in heroes[1:]]
    for pid,hero in zip(ids,heroes):w.action(c,pid,dict(action='class',**{'class':hero}))
    w.action(c,h,dict(action='runOptions',mode='adventure',companion=companion))
    w.rooms[c]['_skipOpening']=skip;w.action(c,h,dict(action='start'))
    return w,w.rooms[c],[w.rooms[c]['players'][pid] for pid in ids]


def at(w,r,age):opening.tick(w,r,r['_opening']['startedAt']+age)
def clear(w,r,p):
    for e in list(r['enemies']):w._damage_enemy(r,p,e,100000)
def first(w,r,p):
    at(w,r,8);at(w,r,2);clear(w,r,p);at(w,r,30)
def second(w,r,p):
    at(w,r,2);at(w,r,10);clear(w,r,p);at(w,r,35)


class OpeningTests(unittest.TestCase):
    def test_all_eight_real_starter_kits_and_immediate_control(self):
        for hero in CLASSES:
            with self.subTest(hero=hero):
                w,r,ps=new((hero,));p=ps[0]
                self.assertEqual(r['adventure']['current'],'caravan');self.assertIsNone(p['dialogue'])
                self.assertEqual(hero_skills.points(p),2);self.assertEqual(len(p['abilities']),2)
                self.assertEqual(p['maxHp'],CLASSES[hero]['hp']);self.assertFalse(w.state(r['code'],p['id'])['movementLocked'])
                at(w,r,8);at(w,r,2);e=r['enemies'][0];p.update(x=e['x']+25,y=e['y'])
                before=e['hp'];w._cast_ability(r,p,0);w._tick_projectiles(r,time.monotonic()+1)
                self.assertTrue(e['hp']<before or r['projectiles'],'The real basic attack resolves or launches a projectile')

    def test_complete_finite_sequence_without_rewards_or_chapter_shortcuts(self):
        w,r,ps=new();p=ps[0];first(w,r,p);self.assertEqual(r['adventure']['opening']['facts'],list(opening.FACTS[:2]))
        second(w,r,p);self.assertEqual(r['_opening']['phase'],'withdrawal')
        p.update(x=opening.MUSTER[0],y=opening.MUSTER[1]);at(w,r,19);self.assertTrue(opening.active(r))
        at(w,r,20);self.assertFalse(opening.active(r));self.assertEqual(r['adventure']['current'],'home')
        self.assertEqual(r['adventure']['opening']['facts'],list(opening.FACTS));self.assertEqual(r['runes'],0)
        self.assertEqual(hero_skills.points(p),2);self.assertTrue(all(q=='active' for q in r['adventure']['quests'].values()))
        opening.complete(w,r);self.assertEqual(hero_skills.points(p),2)

    def test_wipe_retry_preserves_finished_step_no_currency_penalty(self):
        w,r,ps=new();p=ps[0];r['runes']=37;first(w,r,p);at(w,r,2);at(w,r,10)
        p.update(status='downed',hp=0);w._check_party_wipe(r);self.assertEqual(r['phase'],'defeat');self.assertEqual(r['runes'],37)
        w.action(r['code'],p['id'],dict(action='openingRetry'));self.assertEqual(r['_opening']['phase'],'second')
        self.assertEqual(p['hp'],p['maxHp']);self.assertEqual(r['adventure']['opening']['attempt'],1)
        at(w,r,2);self.assertTrue(all('flank' in e['id'] for e in r['enemies']))
        clear(w,r,p);self.assertEqual(r['runes'],37);self.assertEqual(hero_skills.points(p),2)

    def test_restart_each_saved_stage_rebuilds_whole_unfinished_encounter(self):
        for stage in range(1,5):
            with self.subTest(stage=stage),tempfile.TemporaryDirectory() as directory:
                w,r,ps=new(directory=directory);p=ps[0]
                if stage>=2:first(w,r,p)
                if stage>=3:at(w,r,2);at(w,r,10)
                if stage>=4:clear(w,r,p);at(w,r,35)
                if r['enemies']:r['enemies'][0]['hp']=1
                adventure.save(w,r);record=save_portability.project(adventure.snapshot(r));save_portability.validate(record)
                reboot=GameWorld(storage_dir=directory);restored=reboot.rooms[r['code']]
                self.assertEqual(restored['adventure']['current'],'caravan');self.assertEqual(restored['adventure']['opening']['facts'],list(opening.FACTS[:stage]))
                self.assertFalse(restored['enemies'],'No partial enemy list coexists with a new attempt')
                if stage>=2 and stage<4:at(reboot,restored,2);self.assertTrue(all(e['hp']==e['maxHp'] and 'flank' in e['id'] for e in restored['enemies']))
                self.assertEqual(hero_skills.points(restored['players'][p['id']]),2)

    def test_connected_party_gather_offline_companion_and_no_premature_completion(self):
        for size in range(1,5):
            with self.subTest(size=size):
                w,r,ps=new(tuple(CLASSES)[:size]);p=ps[0];at(w,r,8);at(w,r,2)
                self.assertEqual(len(r['enemies']),2+size-1)
                clear(w,r,p);at(w,r,30);second(w,r,p);p.update(x=1040,y=150)
                at(w,r,25)
                self.assertEqual(opening.active(r),size>1)
                if size>1:
                    for ally in ps[1:]:w._disconnect_player(r,ally)
                    at(w,r,26);self.assertFalse(opening.active(r))
        w,r,ps=new(companion=True);first(w,r,ps[0]);second(w,r,ps[0]);ps[0].update(x=1040,y=150);at(w,r,25);self.assertFalse(opening.active(r))

    def test_mid_battle_join_preserves_scene_facts_and_scales_next_pack(self):
        import uuid
        w,r,ps=new();at(w,r,8);at(w,r,2);before=[e['id'] for e in r['enemies']]
        _,pid=session_flow.join(w,dict(requestId=uuid.uuid4().hex,room=r['code'],hero='Healer',name='Joiner'))
        self.assertEqual(before,[e['id'] for e in r['enemies']]);self.assertEqual(hero_skills.points(r['players'][pid]),2)
        clear(w,r,ps[0]);at(w,r,30);at(w,r,2);self.assertEqual(len(r['enemies']),4)

    def test_skip_legacy_import_and_creation_retry_are_compatible(self):
        import uuid
        w=GameWorld();request=dict(requestId=uuid.uuid4().hex,instance='boot',mode='adventure',hero='Knight',skipIntro=True)
        c,pid=session_flow.create(w,request,'boot');r=w.rooms[c];self.assertEqual(r['adventure']['current'],'home')
        self.assertTrue(r['adventure']['opening']['skipped']);self.assertEqual(hero_skills.points(r['players'][pid]),2)
        self.assertEqual(session_flow.create(w,request,'boot'),(c,pid))
        legacy=adventure.snapshot(r);legacy['room']['world'].pop('opening')
        with tempfile.TemporaryDirectory() as directory:
            target=GameWorld(storage_dir=directory);adventure.restore(target,legacy)
            self.assertEqual(target.rooms[c]['adventure']['current'],'home');self.assertNotIn('opening',target.rooms[c]['adventure'])
        bad=copy.deepcopy(save_portability.project(adventure.snapshot(r)));bad['progress']['world']['opening']['version']=99
        with self.assertRaisesRegex(ValueError,'Unsupported opening'):save_portability.validate(bad)

    def test_manifest_once_and_pause_clocks_without_replaying_watch(self):
        w,r,ps=new();p=ps[0];point=adventure.features(r)[0];p.update(x=point['x'],y=point['y'])
        adventure.interact(w,r,p,point);self.assertTrue(r['adventure']['opening']['manifestRead']);self.assertEqual(r['runes'],0)
        self.assertFalse(any(f['id']=='caravan_manifest' for f in adventure.features(r)))
        before=r['_opening']['startedAt'];GameWorld._shift_clocks(r,60);self.assertEqual(r['_opening']['startedAt'],before+60)
        first(w,r,p);at(w,r,2);at(w,r,10);opening.prepare(w,r)
        self.assertIsNone(r['_opening']['eventAt']);self.assertIn('watch_event_observed',r['adventure']['opening']['facts'])
