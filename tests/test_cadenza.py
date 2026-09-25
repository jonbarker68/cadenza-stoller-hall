import argparse
import tempfile
import unittest
from pathlib import Path
from cadenza.model import Timeline, load_show, timer_text


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.timeline = Timeline([{'kind': 'intro'}, {'kind': 'response', 'duration': 30}], lambda: self.now)

    def test_shared_controls_for_both_timer_types(self):
        for kind in ('response', 'countup'):
            with self.subTest(kind=kind):
                t = Timeline([{'kind': kind, 'duration': 30}], lambda: self.now)
                initial = 30 if kind == 'response' else 0
                self.now += 90
                self.assertEqual(t.value(), initial)
                t.stop_restart()  # Disabled before starting.
                self.assertEqual(t.phase, 'ready')
                t.toggle_timer()
                self.now += 5
                expected = 25 if kind == 'response' else 5
                self.assertEqual(t.value(), expected)
                t.toggle_timer()
                self.now += 50
                self.assertEqual(t.value(), expected)
                self.assertEqual(t.phase, 'paused')
                t.toggle_timer()
                self.now += 2
                t.stop_restart()
                stopped = t.value()
                self.now += 50
                self.assertEqual(t.value(), stopped)
                self.assertEqual(t.phase, 'stopped')
                t.toggle_timer()
                self.assertEqual(t.phase, 'stopped')
                t.stop_restart()
                self.assertEqual(t.value(), initial)
                self.assertEqual(t.phase, 'running')

    def test_countdown_completion_and_restart(self):
        t = self.timeline
        self.assertFalse(t.move(-1))
        t.move(1)
        t.toggle_timer()
        self.now += 31
        self.assertEqual(t.value(), 0)
        self.assertEqual(t.phase, 'finished')
        self.assertFalse(t.move(1))
        t.stop_restart()
        self.assertEqual(t.value(), 30)
        self.assertEqual(t.phase, 'running')
        t.move(-1)
        self.assertFalse(t.has_timer)
        t.toggle_timer()
        self.assertEqual(t.phase, 'ready')
        t.move(1)
        self.now += 60
        self.assertEqual(t.value(), 30)
        self.assertEqual(t.phase, 'ready')

    def test_countup_unbounded_and_reentry_waits(self):
        t = Timeline([{'kind': 'countup'}, {'kind': 'closing'}], lambda: self.now)
        t.toggle_timer()
        self.now += 60000
        self.assertEqual(timer_text(t.value()), '1000:00')
        t.toggle_timer()
        t.stop_restart()  # Stop also works from paused.
        self.assertEqual(t.phase, 'stopped')
        t.move(1)
        t.move(-1)
        self.now += 90
        self.assertEqual(t.value(), 0)
        self.assertEqual(t.phase, 'ready')

    def test_rejects_invalid_show(self):
        for content in ['slides: []', 'slides: [{id: a, title: Test, kind: response, duration: -1}]', 'slides: [{id: a, title: Test, kind: music, captions: yesplease}]']:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
                f.write(content)
                f.flush()
                with self.assertRaises(ValueError):
                    load_show(f.name)


class CaptionTests(unittest.TestCase):
    def test_overrides_and_no_stale_caption_on_navigation(self):
        from PySide6.QtCore import QCoreApplication
        from cadenza.app import Controller
        app = QCoreApplication.instance() or QCoreApplication([])
        c = Controller({'slides': [{'title': 'MC', 'kind': 'mc', 'captions': True}, {'title': 'Music', 'kind': 'music', 'captions': False}]}, argparse.Namespace(demo=True))
        c.ingest('final', 'Hello')
        self.assertEqual(c.state['caption'], 'Hello')
        c.move(1)
        c.ingest('final', 'Hidden words')
        self.assertEqual(c.state['caption'], '')
        c.setOverride('ON')
        self.assertEqual(c.state['caption'], '')
        c.ingest('partial', 'New words')
        self.assertEqual(c.state['caption'], 'New words')
        c.setOverride('OFF')
        self.assertFalse(c.state['captions'])
        c.timer.stop()


if __name__ == '__main__':
    unittest.main()
