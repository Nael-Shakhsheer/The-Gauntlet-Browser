import time
import unittest
from unittest.mock import patch
import feedback
import adventure,ascension,magic_runes
from test_expansion import start,runner


class AudioOutcomeTests(unittest.TestCase):
    def events(self,r,kind):return [e for e in feedback.view(r,next(iter(r['players'])))['events'] if e['kind']==kind]

    def test_rejected_and_retried_rune_purchases_are_silent(self):
        w,r,ps=start();p=ps[0];p['magicRunes']['balance']=15
        with self.assertRaises(ValueError):w.action(r['code'],p['id'],dict(action='magicPurchase',purchase='ascend',requestId='bad'))
        self.assertFalse(self.events(r,'ascension'))
        action=dict(action='magicPurchase',purchase='ascend',requestId='audio_ascend_request_123')
        r['adventure']['chapter']['turnedIn'].append('chapter_outcome');r['adventure']['chapter']['stages']['chapter_outcome']='complete'
        w.action(r['code'],p['id'],action)
        self.assertEqual(len(self.events(r,'ascension')),1)
        w.action(r['code'],p['id'],action)
        self.assertEqual(len(self.events(r,'ascension')),1)

    def test_request_boundaries_capture_inspection_not_polling(self):
        w,r,ps=start();p=ps[0];before=feedback.action_state(r,p)
        __import__('progression').inspect(p,'Sign','A real sign.','sign')
        feedback.accepted_action(r,p,dict(action='interact'),before)
        self.assertEqual(len(self.events(r,'inspect')),1)
        for _ in range(10):feedback.view(r,p['id'])
        self.assertEqual(len(self.events(r,'inspect')),1)

    def test_projectile_families_and_stable_launch_event(self):
        self.assertEqual(feedback.projectile_family(dict(side='enemy',ownerKind='draco',affinity='Fire',**{'class':'Wizard'})),'fire')
        self.assertEqual(feedback.projectile_family(dict(side='hero',abilityId='frost_lance',**{'class':'Wizard'})),'frost')
        w,r,ps=start(('Archer',));p=ps[0];adventure.enter(w,r,'road','west')
        e=r['enemies'][0]
        w._launch_projectile(r,side='hero',owner_id=p['id'],target_id=e['id'],x=p['x'],y=p['y'],damage=5,color='#fff',attack_class='Archer')
        self.assertEqual(len(self.events(r,'projectile_launch')),1)
        self.assertFalse(self.events(r,'projectile_impact'))

    def test_accepted_chapter_changes_have_one_outcome(self):
        w,r,ps=start();p=ps[0];runner(w,r,p)
        w.action(r['code'],p['id'],dict(action='chapterAccept',quest='hunter'))
        self.assertEqual(len(self.events(r,'quest_accept')),1)
        before=feedback.stream(r)['cursor']
        w.action(r['code'],p['id'],dict(action='chapterAccept',quest='hunter'))
        self.assertEqual(feedback.stream(r)['cursor'],before)
