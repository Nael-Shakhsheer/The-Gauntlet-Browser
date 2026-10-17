import unittest
from tools.chapter_probe import probe


class OrdinaryProbeTests(unittest.TestCase):
    def test_repeatable_normal_stats_gear_resources_and_cooldowns(self):
        a=probe('cave_entry',('Knight','Druid'),seed=41,limit=30)
        b=probe('cave_entry',('Knight','Druid'),seed=41,limit=30)
        self.assertEqual(a,b)
        self.assertEqual([p['maxHp'] for p in a['entry']],[150,80])
        self.assertEqual(a['entry'][0]['gear'],['iron_sword','oakguard_vest'])
        self.assertEqual(a['entry'][0]['cooldowns']['guardian_cry'],15)
        self.assertNotIn('name',str(a));self.assertNotIn('recoveryProof',str(a));self.assertNotIn('worldId',str(a))
        self.assertGreater(a['damage'],0)

    def test_four_slots_companion_and_abandonment_are_explicit(self):
        r=probe('tower_3',('Knight','Archer','Healer'),companion=True,limit=1)
        self.assertEqual(r['partySize'],4);self.assertTrue(r['companion'])
        self.assertEqual(r['outcome'],'timeout/abandoned');self.assertEqual(r['events'][-1]['kind'],'abandoned')


if __name__=='__main__':unittest.main()
