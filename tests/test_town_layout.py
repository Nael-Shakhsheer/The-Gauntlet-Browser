import math
import unittest
from unittest.mock import patch

import town_layout


class TownLayoutTests(unittest.TestCase):
    def test_road_footprint_and_live_movement_agree(self):
        from game import GameWorld
        houses=[{'x':140,'y':240},{'x':320,'y':240}]
        self.assertTrue(town_layout.clear(houses,230,240))
        self.assertFalse(town_layout.clear(houses,230,240,town_layout.ROAD_MARGIN))
        self.assertFalse(town_layout._valid_positions([(h['x'],h['y']) for h in houses]))
        for x in range(80,400,7):
            for y in range(140,350,7):self.assertEqual(GameWorld._town_walkable({'townLayout':houses},x,y),town_layout.clear(houses,x,y))

    def test_exhausted_jitter_uses_same_validated_deterministic_fallback(self):
        original=town_layout._valid_positions
        def forced():
            count=0
            def check(positions):
                nonlocal count
                count+=1
                return original(positions) if count>160 else False
            return check
        for seed in (0,7,19,20261013,2147483647):
            with patch.object(town_layout,'_valid_positions',side_effect=forced()):v=town_layout.generate(seed)
            with patch.object(town_layout,'_valid_positions',side_effect=forced()):again=town_layout.generate(seed)
            self.assertEqual(v,again);self.assertTrue(v['townDecor']['fallback']);self.assertEqual(town_layout.validate(v),v)

    def test_seeded_layouts_vary_and_keep_every_service_and_spawn_accessible(self):
        kinds, styles = set(), set()
        for seed in range(80):
            village = town_layout.generate(seed)
            self.assertEqual(village, town_layout.generate(seed))
            houses = village['townLayout']
            kinds.add(village['townDecor']['layout'])
            styles.add(village['townDecor']['roadStyle'])
            self.assertEqual({h['id'] for h in houses}, {b[0] for b in town_layout.BUILDINGS})
            self.assertTrue(town_layout._valid_positions([(h['x'], h['y']) for h in houses]))
            for size in range(1, 5):
                for index in range(size):
                    self.assertTrue(town_layout.clear(houses, 480+(index-(size-1)/2)*42, 460, 23))
            ends = {tuple(path[-1]) for path in village['townPaths']}
            for house in houses:
                self.assertIn((house['x'], house['y']+47), ends)
            # Sample complete segments, including bends and the final door approach.
            for path in village['townPaths']:
                for a, b in zip(path, path[1:]):
                    samples = max(1, math.ceil(math.dist(a, b)/5))
                    for i in range(samples+1):
                        x, y = (a[j]+(b[j]-a[j])*i/samples for j in (0, 1))
                        self.assertTrue(town_layout.clear(houses, x, y), (seed, a, b))
        self.assertEqual(kinds, set(town_layout.LAYOUTS))
        self.assertEqual(styles, {'loop', 'lanes', 'branching'})

    def test_consecutive_visits_do_not_repeat_the_previous_shape(self):
        for previous in town_layout.LAYOUTS:
            for seed in range(7):
                village = town_layout.generate(seed, previous_layout=previous)
                self.assertNotEqual(village['townDecor']['layout'], previous)


if __name__ == '__main__':
    unittest.main()
