import json
import tempfile
import unittest
from unittest.mock import patch
import adventure
from adventure_recovery import Recovery
from test_adventure import party


class SaveSlotTests(unittest.TestCase):
    def test_two_adventure_slots_per_character_previous_confirmed_and_new_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(('Knight','Druid'),storage_dir=directory);s=Recovery(w)
            self.assertEqual(s.slots(s.session(r['code'],ps[0]['id']))['backup']['runes'],0)
            r['runes']=33;adventure.save(w,r);r['runes']=55;adventure.save(w,r)
            ref=s.session(r['code'],ps[1]['id']);slots=s.slots(ref)
            self.assertEqual((slots['current']['runes'],slots['backup']['runes']),(55,33))
            view=s.slots(ref,True);self.assertEqual(view['character'],1)
            result=s.commit(dict(preview=view['preview'],character=view['character'],confirm=True))
            self.assertEqual(w.rooms[result['room']]['runes'],33);self.assertEqual(r['runes'],55)
            self.assertEqual(s.commit(dict(preview=view['preview'],character=1,confirm=True)),result)

    def test_failed_atomic_current_write_does_not_advance_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);adventure.save(w,r)
            path=w.storage.adventure_paths[r['adventure']['worldId']];before=path.read_bytes();revision=r['adventure']['revision']
            import run_storage
            original=run_storage.os.replace
            def fail_current(source,destination):
                if destination==path:raise PermissionError('Environment denied atomic replacement')
                return original(source,destination)
            with patch('run_storage.os.replace',side_effect=fail_current),self.assertLogs(level='ERROR'):
                self.assertFalse(adventure.save(w,r))
            self.assertEqual(path.read_bytes(),before);self.assertEqual(r['adventure']['revision'],revision)
            self.assertEqual(w.storage.adventure_backup(r['adventure']['worldId'])['room']['world']['revision'],revision)

    def test_private_proof_required_and_bad_backup_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            w,r,ps=party(storage_dir=directory);adventure.save(w,r);s=Recovery(w);ref=s.session(r['code'],ps[0]['id'])
            with self.assertRaises(ValueError):s.slots({**ref,'recovery':'wrong'})
            path=w.storage.directory/'adventure-backups'/(r['adventure']['worldId']+'.json');path.write_text('invalid')
            with self.assertRaises(ValueError):s.slots(ref,True)
            self.assertEqual(path.read_text(),'invalid')
