"""Recover an event without replaying captions or silently running timers."""
import argparse
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from PySide6.QtCore import QCoreApplication, QEventLoop, QProcess, QTimer
from cadenza.app import Controller
from cadenza.model import Timeline
from cadenza.recovery import EventCheckpoint

SLIDES = [dict(id='welcome', title='Welcome', kind='mc', captions=True),
          dict(id='response', title='Respond', kind='response', duration=60, captions=False)]


class CheckpointTests(unittest.TestCase):
    def test_running_timer_restores_paused_by_id_after_reordering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            now = [100.0]
            t = Timeline(SLIDES, lambda: now[0]);t.move(1);t.toggle_timer();now[0] += 17.5
            EventCheckpoint(path, 'show.yaml').save(t, 'OFF', 'WHITE')
            recovered = Timeline(list(reversed(SLIDES)), lambda: 999999)
            checkpoint = EventCheckpoint(path, 'show.yaml');checkpoint.restore(recovered)
            self.assertEqual(recovered.slide['id'], 'response')
            self.assertEqual(recovered.phase, 'paused')
            self.assertEqual(recovered.value(), 43)
            self.assertEqual(checkpoint.preferences, dict(override='OFF', speaker_override='WHITE'))
            self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_corrupt_or_foreign_checkpoint_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json';t = Timeline(SLIDES)
            for contents in ('{', '[]', '{"version":1,"show":"another-show"}'):
                path.write_text(contents)
                with self.assertRaises(ValueError):
                    EventCheckpoint(path, 'show.yaml').restore(t)
                self.assertEqual(t.index, 0)

    def test_changed_duration_resets_timer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json';t = Timeline(SLIDES);t.move(1);t.toggle_timer()
            EventCheckpoint(path, 'show.yaml').save(t)
            updated = Timeline([SLIDES[0], dict(SLIDES[1], duration=90)])
            EventCheckpoint(path, 'show.yaml').restore(updated)
            self.assertEqual(updated.phase, 'ready');self.assertEqual(updated.value(), 90)


class ControllerRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def wait_for(self, predicate, timeout=6000):
        loop = QEventLoop();poll = QTimer();poll.setInterval(10)
        poll.timeout.connect(lambda: loop.quit() if predicate() else None)
        poll.start();QTimer.singleShot(timeout, loop.quit)
        if not predicate(): loop.exec()
        poll.stop();self.assertTrue(predicate(), 'Timed out waiting for worker state')

    def test_abrupt_exit_keeps_last_slide_without_shutdown_handler(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)/'state.json'
            script = """
import argparse,os,sys
from PySide6.QtCore import QCoreApplication
from cadenza.app import Controller
app=QCoreApplication([])
c=Controller({'slides':[{'id':'a','kind':'mc','title':'A'}, {'id':'b','kind':'response','title':'B','duration':60}]},
 argparse.Namespace(demo=True,resume=True,show='show.yaml',state_file=sys.argv[1]))
c.move(1);c.timerToggle();c.setOverride('OFF')
os._exit(23)
"""
            result = subprocess.run([sys.executable, '-c', script, str(state)])
            self.assertEqual(result.returncode, 23)
            recovered=Timeline([dict(id='a',kind='mc',title='A'),dict(id='b',kind='response',title='B',duration=60)])
            checkpoint=EventCheckpoint(state, 'show.yaml');checkpoint.restore(recovered)
            self.assertEqual(recovered.index, 1);self.assertEqual(recovered.phase, 'paused')
            self.assertEqual(checkpoint.preferences['override'], 'OFF')

    def test_caption_worker_exits_when_gui_parent_dies(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);package=root/'src/live_caption';package.mkdir(parents=True)
            (package/'__init__.py').write_text('')
            marker=root/'started'
            (package/'config.py').write_text('from pathlib import Path\nimport time\nPath('+repr(str(marker))+').touch()\ntime.sleep(60)\n')
            bridge=Path(__file__).resolve().parents[1]/'src/cadenza/bridge.py'
            parent_script="import os,subprocess,sys,time;subprocess.Popen([sys.executable,sys.argv[1],sys.argv[2],'unused','', '--parent-pid',str(os.getpid())]);time.sleep(60)"
            parent=subprocess.Popen([sys.executable,'-c',parent_script,str(bridge),str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                import time
                deadline=time.monotonic()+5
                while not marker.exists() and time.monotonic()<deadline:time.sleep(.02)
                self.assertTrue(marker.exists())
                parent.terminate()
                # Pipes remain open in the child until the watchdog exits it.
                parent.communicate(timeout=4)
            finally:
                if parent.poll() is None:
                    parent.kill();parent.wait()

    def test_controller_resume_and_fresh_start(self):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(demo=True, resume=True, show='show.yaml', state_file=Path(directory)/'state.json')
            c = Controller(dict(slides=SLIDES), args);c.timer.stop()
            c.move(1);c.setOverride('OFF');c.setSpeakerOverride('WHITE');c.close()
            d = Controller(dict(slides=SLIDES), args);d.timer.stop()
            self.assertEqual(d.timeline.index, 1);self.assertEqual(d.override, 'OFF')
            self.assertEqual(d.speaker_override, 'WHITE');d.close()
            args.fresh_start=True
            e = Controller(dict(slides=SLIDES), args);e.timer.stop()
            self.assertEqual(e.timeline.index, 0);e.close()

    def test_real_caption_crash_restart_and_stuck_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            c = Controller(dict(slides=SLIDES), argparse.Namespace(demo=False, live_caption=str(root), caption_config=str(root/'missing.yaml'), replay=None))
            c.timer.stop()
            try:
                # First worker crashes, then replace it with a healthy long-running source.
                c.caption_command = (sys.executable, ['-u', '-c', 'import sys;sys.exit(7)'])
                c.restartCaptions();self.wait_for(lambda: c.process.state()==QProcess.NotRunning and 'exit 7' in c.status)
                self.assertTrue(c.error)
                c.move(1);c.timerToggle();c.setOverride('ON');start = c.timeline.started
                code = ('import json,signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);'
                        'print(json.dumps(dict(kind="caption",text="Recovered speech")),flush=True);time.sleep(60)')
                c.caption_command = (sys.executable, ['-u', '-c', code])
                c.restartCaptions();self.wait_for(lambda: c.caption=='Recovered speech')
                self.assertFalse(c.error);self.assertEqual(c.timeline.index, 1)
                self.assertEqual(c.timeline.started, start);self.assertEqual(c.override, 'ON')
                old_pid=c.process.processId()
                c.restartCaptions()  # Ignores SIGTERM; forced stop must unblock restart.
                self.wait_for(lambda: c.process.processId()!=old_pid and c.caption=='Recovered speech')
                self.assertEqual(c.timeline.started, start)
                c.clearCaptions();self.assertEqual(c.caption, '')
                self.assertTrue(c.process.state()==QProcess.Running)
            finally:
                c.close()
