import copy
import tempfile
import unittest
import chapter_flow as chapter
import adventure,save_portability
from test_opening import new
from test_adventure import finish


class ChapterFlowTests(unittest.TestCase):
    def village(self):
        w,r,ps=new(skip=True);p=ps[0];finish(w,r,p)
        point=next(f for f in adventure.features(r) if f['id']=='runner');p.update(x=point['x'],y=point['y'])
        return w,r,p

    def test_fresh_world_needs_acceptance_and_report_before_bridge(self):
        w,r,p=self.village();self.assertEqual(r['adventure']['chapter']['stages']['hunter'],'offered')
        with self.assertRaisesRegex(ValueError,'Accept'):chapter.require(r,'hunter')
        w.action(r['code'],p['id'],dict(action='chapterAccept',quest='hunter'));chapter.require(r,'hunter')
        r['adventure']['quests']['hunter']='complete';chapter.reconcile(r)
        self.assertEqual(r['adventure']['chapter']['stages']['hunter'],'ready-to-turn-in')
        with self.assertRaisesRegex(ValueError,'Accept'):chapter.require(r,'bridge')
        w.action(r['code'],p['id'],dict(action='chapterReport',quest='hunter'))
        self.assertEqual(r['adventure']['chapter']['stages']['bridge'],'offered')
        w.action(r['code'],p['id'],dict(action='chapterReport',quest='hunter'))
        self.assertEqual(r['adventure']['chapter']['turnedIn'].count('hunter'),1)

    def test_early_evidence_is_retained_without_completing_unaccepted_assignment(self):
        w,r,p=self.village();chapter.evidence(r,'brook_outlet');chapter.evidence(r,'mill_wheel')
        self.assertEqual(r['adventure']['chapter']['stages']['water'],'unavailable')
        chapter.evidence(r,'brook_outlet');self.assertEqual(r['adventure']['chapter']['evidence'].count('brook_outlet'),1)
        with self.assertRaisesRegex(ValueError,'previous'):w.action(r['code'],p['id'],dict(action='chapterAccept',quest='water'))

    def test_old_completed_woodland_reconciles_border_without_replaying_quests(self):
        w,r,p=self.village();r['adventure'].pop('chapter');r['adventure']['quests']={k:'complete' for k in adventure.QUESTS};r['adventure'].update(bridge=True,bossComplete=True)
        state=chapter.ensure(r);self.assertTrue(state['legacy']);self.assertEqual(state['stages']['border'],'offered')
        self.assertEqual(sum(chapter.available_rewards(r).values()),5);self.assertEqual(r['runes'],0)
        chapter.validate(state)

    def test_export_and_unsupported_chapter_preserve_originals(self):
        w,r,p=self.village();w.action(r['code'],p['id'],dict(action='chapterAccept',quest='hunter'))
        document=save_portability.project(adventure.snapshot(r));save_portability.validate(document)
        original=copy.deepcopy(document);document['progress']['world']['chapter']['version']=99
        with self.assertRaisesRegex(ValueError,'Unsupported chapter'):save_portability.validate(document)
        self.assertEqual(original['progress']['world']['chapter']['version'],1)
