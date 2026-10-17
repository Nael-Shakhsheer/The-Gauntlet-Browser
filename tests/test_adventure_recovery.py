import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import adventure,adventure_rewards,dungeons,save_portability as portable
from adventure_recovery import Recovery
from game import GameWorld
from test_adventure import party,travel,interact,kill,shrine
from test_dungeons import begin,clear_floor


class RecoveryTests(unittest.TestCase):
    def test_export_contains_progress_and_no_private_recovery_or_logs(self):
        w,r,ps=party(('Knight','Druid'),companion=True)
        r['adventure']['ownerAccount']='private-account';r['chat']=[{'text':'PRIVATE'}]
        service=Recovery(w);doc=service.read(service.session(r['code'],ps[0]['id']),True)
        raw=json.dumps(doc)
        for secret in (r['code'],ps[0]['id'],ps[1]['id'],ps[0]['recoveryProof'],'private-account','PRIVATE',r['runId']):self.assertNotIn(secret,raw)
        clean,_=portable.validate(doc);self.assertEqual(len(clean['progress']['characters']),3)

    def test_new_copy_summary_confirmation_retry_original_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Druid'),storage_dir=directory);service=Recovery(w)
            path=w.storage.adventure_paths[r['adventure']['worldId']];before=path.read_bytes()
            doc=service.read(service.session(r['code'],ps[0]['id']),True);view=service.preview(doc)
            self.assertEqual(view['summary']['characters'][1]['hero'],'Druid')
            self.assertEqual(len(w.rooms),1);self.assertEqual(path.read_bytes(),before)
            with self.assertRaises(ValueError):service.commit(dict(preview=view['preview'],character=1))
            result=service.commit(dict(preview=view['preview'],character=1,confirm=True))
            self.assertEqual(service.commit(dict(preview=view['preview'],character=1,confirm=True)),result)
            new=w.rooms[result['room']];self.assertNotEqual(new['adventure']['worldId'],r['adventure']['worldId'])
            state=w.state(result['room'],result['player']);self.assertTrue(state['townHouses']);self.assertEqual(state['adventure']['area'],'home')
            self.assertNotEqual(result['player'],ps[1]['id']);self.assertEqual(new['players'][result['player']]['class'],'Druid')
            self.assertEqual(path.read_bytes(),before);self.assertEqual(len(list((Path(directory)/'adventures').glob('*.json'))),2)
            restart=GameWorld(storage_dir=directory);self.assertEqual(len(restart.rooms),2)

    def test_older_internal_v1_migration_preserves_completed_bridge_shrine(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);r['adventure']['bridge']=True;r['adventure']['quests']['bridge']='complete'
            r['adventure']['quests']['shrine']='complete';record=adventure.snapshot(r)
            record['room']['world'].pop('worldId');record['room']['world'].pop('creatorCharacter');record['room']['world'].pop('dungeons')
            service=Recovery(w);view=service.preview(record);self.assertTrue(view['summary']['migrated'])
            ref=service.commit(dict(preview=view['preview'],confirm=True,character=0));new=w.rooms[ref['room']]
            self.assertTrue(new['adventure']['bridge']);self.assertEqual(new['adventure']['quests']['shrine'],'complete')

    def test_untrusted_invalid_backups_do_not_write_or_install(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);service=Recovery(w);base=portable.project(adventure.snapshot(r))
            cases=[]
            for key,val in (('version',99),('current','../../data'),('quests',{})):
                bad=copy.deepcopy(base);bad['progress']['world'][key]=val;cases.append(bad)
            for bad in (None,[],dict(version=42),*cases):
                before={p.name:p.read_bytes() for p in (Path(directory)/'adventures').glob('*.json')}
                with self.assertRaises((ValueError,AttributeError)):service.preview(bad)
                self.assertEqual(len(w.rooms),1);self.assertEqual(before,{p.name:p.read_bytes() for p in (Path(directory)/'adventures').glob('*.json')})
            bad=copy.deepcopy(base);bad['progress']['characters'][0]['maxHp']=float('nan')
            with self.assertRaises(ValueError):service.preview(bad)

    def test_import_item_effects_are_canonical_and_ids_not_paths(self):
        w,r,ps=party();p=ps[0];p['inventory']=[w._make_item('healing_draught')]
        doc=portable.project(adventure.snapshot(r));item=doc['progress']['characters'][0]['inventory'][0]
        item.update(factor=999,heal=999,effect='secret',sell=999)
        clean,_=portable.validate(doc);item=clean['progress']['characters'][0]['inventory'][0]
        self.assertEqual((item['heal'],item['sell']),(40,4));self.assertIsNone(item['effect'])
        item['id']='../private';
        with self.assertRaises(ValueError):portable.validate(clean)

    def test_save_failure_does_not_advance_confirmed_time_or_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);a=r['adventure'];stamp=a['savedAt'];revision=a['revision'];before=w.storage.adventure_paths[a['worldId']].read_bytes()
            with patch.object(w.storage,'save_adventure',side_effect=OSError('Disk full')),self.assertLogs(level='ERROR'):
                self.assertFalse(adventure.save(w,r))
            self.assertEqual((a['savedAt'],a['revision']),(stamp,revision));self.assertTrue(w.adventure_summary(r,ps[0])['error'])
            self.assertEqual(before,w.storage.adventure_paths[a['worldId']].read_bytes())
            self.assertTrue(adventure.save(w,r));self.assertNotIn('saveError',a)

    def test_two_local_writers_detect_revision_conflict_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);other=GameWorld(storage_dir=directory);stale=other.rooms[r['code']]
            r['runes']=432;self.assertTrue(adventure.save(w,r));path=w.storage.adventure_paths[r['adventure']['worldId']];before=path.read_bytes()
            stale['runes']=1
            with self.assertLogs(level='ERROR'):self.assertFalse(adventure.save(other,stale))
            self.assertEqual(path.read_bytes(),before);self.assertIn('conflict',stale['adventure']['saveError'].lower())

    def test_unloaded_original_uuid_record_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);record=adventure.snapshot(r);path=w.storage.adventure_paths[r['adventure']['worldId']]
            record['version']=99;path.write_text(json.dumps(record));before=path.read_bytes()
            with self.assertLogs(level='ERROR'):fresh=GameWorld(storage_dir=directory)
            good=adventure.snapshot(r);good['room']['world']['revision']+=1
            with self.assertRaises(OSError):fresh.storage.save_adventure(good)
            self.assertEqual(path.read_bytes(),before)

    def test_import_storage_failure_preserves_original_and_can_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);s=Recovery(w);view=s.preview(portable.project(adventure.snapshot(r)))
            with patch.object(w.storage,'save_adventure',side_effect=OSError('Full')),self.assertLogs(level='ERROR'):
                with self.assertRaises(ValueError):s.commit(dict(preview=view['preview'],confirm=True,character=0))
            self.assertEqual(len(w.rooms),1)
            ref=s.commit(dict(preview=view['preview'],confirm=True,character=0));self.assertIn(ref['room'],w.rooms)

    def test_legacy_file_identity_migration_load_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);path=w.storage.adventure_paths[r['adventure']['worldId']]
            doc=json.loads(path.read_text());doc['room']['world'].pop('worldId');doc['room']['world'].pop('creatorCharacter');doc['room']['world'].pop('name')
            legacy=path.parent/(r['code']+'.json');legacy.write_text(json.dumps(doc));path.unlink();before=legacy.read_bytes()
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']];wid=rr['adventure']['worldId']
            self.assertEqual(legacy.read_bytes(),before);adventure.save(restart,rr);self.assertEqual(restart.storage.adventure_paths[wid],legacy)

    def test_host_changes_and_leaving_do_not_transfer_creator_or_delete_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Druid'),storage_dir=directory);creator=r['adventure']['creatorCharacter'];wid=r['adventure']['worldId']
            w.action(r['code'],ps[0]['id'],dict(action='leaveRoom'));self.assertEqual(r['adventure']['creatorCharacter'],creator)
            self.assertIn(ps[0]['id'],r['players']);self.assertTrue(w.storage.adventure_paths[wid].exists())
            self.assertFalse(w.adventure_summary(r,ps[1])['creator'])

    def test_private_invite_requires_creator_proof_and_keeps_character_gear(self):
        w,r,ps=party(('Knight','Druid'));s=Recovery(w);payload=s.session(r['code'],ps[0]['id']);payload['character']=ps[1]['characterId']
        with self.assertRaises(ValueError):s.guest_invite({**payload,'recovery':''})
        guest=s.guest_invite(payload);self.assertEqual(guest['player'],ps[1]['id'])
        with self.assertRaises(ValueError):s.guest_invite({**s.session(r['code'],ps[1]['id']),'character':ps[0]['characterId']})

    def test_pending_rewards_survive_travel_restore_import_and_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Druid'),storage_dir=directory)
            adventure.reward(w,r,'dungeon:tower',40,'class_weapon');adventure.save(w,r)
            self.assertEqual(ps[0]['pendingRewards']['dungeon:tower']['options'],['iron_sword','pursuit_blade'])
            self.assertIn('summoners_staff',ps[1]['pendingRewards']['dungeon:tower']['options'])
            restart=GameWorld(storage_dir=directory);rr=restart.rooms[r['code']];p=rr['players'][ps[1]['id']]
            payload=dict(action='adventureReward',reward='dungeon:tower',item='summoners_staff',delivery='pouch')
            restart.action(rr['code'],p['id'],payload);money=rr['runes'];inventory=copy.deepcopy(p['inventory'])
            restart.action(rr['code'],p['id'],payload);self.assertEqual((rr['runes'],p['inventory']),(money,inventory))
            clean,_=portable.validate(portable.project(adventure.snapshot(rr)));self.assertTrue(clean['progress']['characters'][1]['resolvedRewards'])

    def test_full_pouch_explicit_sell_or_replace_and_receipt(self):
        w,r,ps=party();p=ps[0];p['inventory']=[w._make_item('mana_draught') for _ in range(10)]
        adventure.reward(w,r,'dungeon:cave',40,'class_weapon');before=r['runes']
        with self.assertRaises(ValueError):adventure_rewards.claim(w,r,p,dict(reward='dungeon:cave',item='phoenix_flask'))
        self.assertEqual(r['runes'],before);self.assertIn('dungeon:cave',p['pendingRewards'])
        old=p['inventory'][0];adventure_rewards.claim(w,r,p,dict(reward='dungeon:cave',item='phoenix_flask',replace=old['id']))
        self.assertEqual(len(p['inventory']),10);self.assertEqual(r['runes'],before+old['sell']);self.assertEqual(p['inventory'][-1]['key'],'phoenix_flask')

    def test_existing_claims_are_not_reclaimed_or_replaced(self):
        w,r,ps=party();r['adventure']['claimed'].append('shrine');ps[0]['inventory']=[w._make_item('moonsteel_sword')]
        self.assertFalse(adventure.reward(w,r,'shrine',35,'class_reward'))
        self.assertNotIn('pendingRewards',ps[0]);self.assertEqual(ps[0]['inventory'][0]['key'],'moonsteel_sword')

    def test_tower_roles_timing_guard_pressure_and_revive_spawn_space(self):
        for heroes in (('Knight',),('Knight','Druid','Wizard','Healer')):
            for area in ('tower_1','tower_2','tower_3'):
                w,r,ps=party(heroes)
                adventure.enter(w,r,area,'south');begin(w,r,ps)
                guards=[e for e in r['enemies'] if not e.get('boss')]
                self.assertIn('ranged',[e['combatRole'] for e in guards])
                self.assertNotIn('support',[e['combatRole'] for e in guards])
                if area=='tower_3':self.assertLessEqual(len(guards),2)
                self.assertGreater(len({e['roleReadyAt'] for e in guards}),1 if len(guards)>1 else 0)
                for e in r['enemies']:self.assertTrue(all(__import__('math').dist((e['x'],e['y']),(p['x'],p['y']))>=85 for p in ps))


if __name__=='__main__':unittest.main()
