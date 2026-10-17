"""Optimizations must preserve live state, isolation and safe packaging."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hero_skills,magic_runes,adventure
from test_expansion import start
from tools.package_game import source_files


class PerformanceAuditTests(unittest.TestCase):
    def test_catalog_negotiation_keeps_live_authoritative_fields(self):
        w,r,ps=start();p=ps[0];full=w.state(r['code'],p['id'])
        live=w.state(r['code'],p['id'],include_catalog=False,known_skill_revision=full['heroSkillsRevision'])
        for key in ('abilityOptions','classes','skills','difficulties','heroSkills'):self.assertNotIn(key,live)
        for key in ('movement','enemies','abilitySlots','adventure','interaction','inventory'):self.assertIn(key,live)
        self.assertEqual(live['movement']['epoch'],full['movement']['epoch'])
        self.assertIn('heroSkills',w.state(r['code'],p['id'],known_skill_revision='stale'))

    def test_skill_token_invalidates_for_safety_loadout_milestones_and_ascension(self):
        w,r,ps=start();p=ps[0]
        def token():return hero_skills.revision(r,p)
        old=token();p['status']='downed';self.assertNotEqual(old,token());p['status']='alive';self.assertEqual(old,token())
        adventure.enter(w,r,'road','north');next=token();self.assertNotEqual(old,next)
        p['magicRunes']['ascended']=True;self.assertNotEqual(next,token())
        p['class']='Healer';self.assertNotEqual(old,token())

    def test_repeated_negotiated_polls_do_not_rebuild_tree_or_catalog(self):
        w,r,ps=start();p=ps[0];full=w.state(r['code'],p['id'])
        with patch.object(hero_skills,'view',side_effect=AssertionError('Unchanged tree rebuilt')):
            for _ in range(3):w.state(r['code'],p['id'],include_catalog=False,known_skill_revision=full['heroSkillsRevision'])
        self.assertEqual(full['selectedAbilities'],p['abilities'])

    def test_packaging_excludes_secrets_logs_and_dev_previews_but_preserves_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('server.py','static/app.js','.env','.env.local','.env.example','server.key','data/adventures/private.json',
                         'art/audio/build-sounds.cjs','art/audio/LICENSE.md','art/audio/mixed-combat.wav','reports/debug.log','tests/test_game.py','art/exports/source.zip'):
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture',encoding='utf-8')
            runtime={name for name,_ in source_files(root,runtime_only=True)}
            self.assertTrue({'server.py','static/app.js','.env.example','art/audio/build-sounds.cjs','art/audio/LICENSE.md'}<=runtime)
            self.assertFalse({'.env','.env.local','server.key','data/adventures/private.json','reports/debug.log','art/audio/mixed-combat.wav'}&runtime)
            source={name for name,_ in source_files(root)}
            self.assertIn('art/exports/source.zip',source);self.assertIn('tests/test_game.py',source)
            self.assertNotIn('reports/debug.log',source)
            self.assertTrue((root/'art/audio/mixed-combat.wav').exists())
