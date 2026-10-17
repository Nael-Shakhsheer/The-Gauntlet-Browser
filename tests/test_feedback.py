import time
import unittest
from unittest.mock import patch
import feedback
from test_adventure import party, travel


class FeedbackTests(unittest.TestCase):
    def test_bounded_private_stable_and_expiring(self):
        r={'players': {}, 'enemies': []}
        with patch('feedback.time.monotonic', return_value=10):
            for i in range(200): feedback.emit(r, 'hit', privateTo='me')
            v=feedback.view(r, 'me')
            self.assertEqual(len(v['events']), 128)
            self.assertEqual(v['cursor'], 200)
            self.assertEqual(feedback.view(r, 'other')['events'], [])
            self.assertEqual(feedback.view(r, 'me')['epoch'], v['epoch'])
        with patch('feedback.time.monotonic', return_value=14):
            self.assertFalse(feedback.view(r, 'me')['events'])

    def test_real_acceptance_rejection_and_adventure_scenes(self):
        w,r,ps=party(('Knight','Wizard','Druid','Healer'))
        travel(w,r,'road');p=ps[0]
        initial=feedback.view(r,p['id'])
        w.action(r['code'],p['id'],{'action':'dash'})
        count=feedback.stream(r)['cursor']
        with self.assertRaises(ValueError):w.action(r['code'],p['id'],{'action':'dash'})
        self.assertEqual(feedback.stream(r)['cursor'],count)
        self.assertEqual(sum(e['kind']=='dash' for e in feedback.view(r,p['id'])['events']),1)
        travel(w,r,'cave_entry')
        current=feedback.view(r,p['id'])
        self.assertNotEqual(initial['epoch'],current['epoch'])
        self.assertIn('cave_entry',current['scene'])
        self.assertFalse(any(e['kind']=='dash' for e in current['events']))

    def test_windup_release_cancel_heal_and_ward(self):
        now=time.monotonic()
        p={'id':'p','hp':10,'status':'alive','wardUntil':0}
        e={'id':'e','boss':True,'bossPhase':1,'x':1,'y':2}
        r={'players':{'p':p},'enemies':[e],'phase':'combat','stageWave':1}
        feedback.sample(r)
        e['pendingAttack']={'kind':'slam','startedAt':now,'targetId':'p'}
        feedback.sample(r);feedback.sample(r)
        e.pop('pendingAttack');feedback.sample(r)
        self.assertEqual([e['kind'] for e in feedback.view(r,'p')['events']],['windup'])
        e['pendingAttack']={'kind':'slam','startedAt':now+1}
        feedback.sample(r);e.pop('pendingAttack');e['recoverUntil']=now+5
        p.update(hp=20,wardUntil=now+5);feedback.sample(r)
        kinds=[e['kind'] for e in feedback.view(r,'p')['events']]
        self.assertEqual(kinds.count('release'),1)
        self.assertIn('heal',kinds);self.assertIn('ward',kinds)

    def test_four_player_casts_are_authoritative(self):
        w,r,ps=party(('Knight','Wizard','Druid','Healer'));travel(w,r,'road')
        enemy=r['enemies'][0]
        for i,p in enumerate(ps):p.update(x=enemy['x']-20,y=enemy['y']+i*10)
        ps[0]['hp']-=15
        for p in ps:
            w.action(r['code'],p['id'],dict(action='ability',slot=2))
        events=feedback.view(r,ps[0]['id'])['events']
        casts=[e for e in events if e['kind']=='ability']
        self.assertEqual(len(casts),4)
        self.assertEqual(len({e['id'] for e in events}),len(events))
        self.assertIn('summon',[e['kind'] for e in events])
        before=feedback.stream(r)['cursor']
        with self.assertRaises(ValueError):w.action(r['code'],ps[0]['id'],dict(action='ability',slot=2))
        self.assertEqual(feedback.stream(r)['cursor'],before)

    def test_healing_between_damage_is_not_lost_or_duplicated(self):
        p={'id':'p','hp':10,'status':'alive','wardUntil':0}
        r={'players':{'p':p},'enemies':[]}
        feedback.sample(r);p['hp']=20;feedback.restored(r,p,'heal',amount=10)
        p['hp']=5;feedback.sample(r)
        self.assertEqual([e['kind'] for e in feedback.view(r,'p')['events']],['heal'])
