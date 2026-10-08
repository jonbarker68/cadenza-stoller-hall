"""Exercise the booklet programme through the real operator controller."""
import argparse
from pathlib import Path
import unittest
from PySide6.QtCore import QCoreApplication
from cadenza.app import Controller
from cadenza.model import load_show


class ProgrammeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_booklet_flow_and_manual_cues(self):
        show = load_show(Path(__file__).resolve().parents[1] / 'config/show.yaml')
        c = Controller(show, argparse.Namespace(demo=True))
        self.addCleanup(lambda: c.timer.stop())
        now = [0.0]
        c.timeline.now = lambda: now[0]
        self.assertEqual(c.state['count'], 26)
        self.assertEqual(c.state['kind'], 'arrivals')
        self.assertFalse(c.state['captions'])
        c.move(1)
        self.assertTrue(c.state['captions'])
        self.assertEqual(c.state['kind'], 'mc')
        for number, page in enumerate([7, 8, 9, 10, 12, 14, 15, 16, 18, 19], 1):
            c.move(1)
            self.assertEqual(c.state['kind'], 'experiment')
            self.assertEqual((c.state['passage'], c.state['page']), (str(number), str(page)))
            c.setOverride('AUTO')
            c.ingest('caption', 'MC introduction')
            self.assertEqual(c.state['caption'], 'MC introduction')
            index = c.state['index']
            c.setOverride('OFF')
            c.ingest('caption', 'Music must not appear')
            self.assertEqual(c.state['caption'], '')
            self.assertEqual(c.state['index'], index)
            c.move(1)
            self.assertEqual(c.state['override'], 'OFF')
            self.assertEqual(c.state['kind'], 'response')
            self.assertEqual((c.state['passage'], c.state['page']), (str(number), str(page)))
            self.assertEqual(c.state['timerTime'], '01:00')
            now[0] += 90
            self.assertEqual(c.state['timerTime'], '01:00')
            c.timerToggle()
            now[0] += 60
            self.assertEqual(c.state['timerTime'], '00:00')
            self.assertEqual(c.state['timerPhase'], 'finished')
            self.assertEqual(c.state['index'], index + 1)
        c.move(1)
        self.assertEqual(c.state['kind'], 'closing')
        c.move(1)
        self.assertEqual((c.state['kind'], c.state['page']), ('mc', '20'))
        c.move(1)
        self.assertEqual((c.state['kind'], c.state['page']), ('countup', '20'))
        self.assertEqual(c.state['timerTime'], '00:00')
        c.timerToggle()
        now[0] += 125
        self.assertEqual(c.state['timerTime'], '02:05')
        c.timerStopRestart()
        now[0] += 20
        self.assertEqual(c.state['timerTime'], '02:05')
        c.move(1)
        self.assertEqual(c.state['kind'], 'closing')
        c.setOverride('AUTO')
        self.assertTrue(c.state['captions'])
        c.move(1)
        self.assertEqual(c.state['index'], 25)
