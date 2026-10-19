"""Smoke tests: run with python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from fetch_contributions import demo_calendar
from render_frames import (pick_targets, frames_schedule, render_frames,
                           MageAnimation, FramePlan)


class AnimationTests(unittest.TestCase):
    def test_schedule_uses_only_active_cells(self):
        grid = demo_calendar()
        targets = pick_targets(grid, 12)
        self.assertTrue(all(grid[x][y] > 0 for x, y in targets))
        self.assertEqual(len(set(targets)), len(targets))

    def test_one_projectile_phase_per_cell(self):
        targets = [(3, 2), (5, 6)]
        schedule = frames_schedule(targets)
        for shot in range(2):
            phases = [f.phase for f in schedule if f.shot == shot]
            self.assertEqual(phases.count('orb'), 5)
            self.assertEqual(phases.count('shatter'), 3)

    def test_can_draw_a_real_frame(self):
        frame = next(render_frames(demo_calendar(), 2))
        self.assertEqual(frame.size, (1640, 540))

    def test_supplied_cast_changes_pose_and_preserves_transparency(self):
        animation = MageAnimation()
        start = animation.sprite(FramePlan(0, 'charge', 0, 0, 0, (5, 2)), 0)
        charged = animation.sprite(FramePlan(0, 'charge', 15, 0, 0, (5, 2)), 15)
        self.assertEqual(start.mode, 'RGBA')
        self.assertEqual(start.getpixel((0, 0))[3], 0)
        self.assertNotEqual(start.tobytes(), charged.tobytes())
        # Original cast frame 27 contains a far-away missile. The body crop
        # must exclude it so that the scene contains only the controlled bolt.
        firing = animation.sprite(FramePlan(0, 'orb', 0, 0, 0, (5, 2)), 16)
        self.assertEqual(firing.size, (96, 96))
        self.assertLessEqual(firing.getbbox()[2], 29 * 3)

    def test_no_active_cells_never_casts(self):
        targets = pick_targets([[0] * 7 for _ in range(53)], 12)
        self.assertEqual(targets, [])
        self.assertTrue(all(plan.phase == 'idle' and plan.target is None
                            for plan in frames_schedule(targets)))


if __name__ == '__main__':
    unittest.main()
