"""Diagnose caption startup failures without microphone or network access."""
import argparse
import logging
from pathlib import Path
import tempfile
import unittest
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from cadenza.app import Controller
from cadenza.diagnostics import configure_logging, RedactingFormatter


class DiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_redaction_includes_tracebacks(self):
        formatter = RedactingFormatter(['known-credential'])
        try:
            raise ValueError('known-credential api_key=other-key Authorization: Bearer third-key')
        except ValueError:
            import sys
            record = logging.LogRecord('test', logging.ERROR, '', 0, 'Failure', (), sys.exc_info())
        text = formatter.format(record)
        self.assertIn('ValueError', text)
        for secret in ('known-credential', 'other-key', 'third-key'):
            self.assertNotIn(secret, text)

    def test_real_child_startup_traceback_is_saved_and_displayed(self):
        import sys
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'src/live_caption'
            package.mkdir(parents=True)
            (package / '__init__.py').write_text('')
            (package / 'config.py').write_text("raise RuntimeError('Synthetic caption startup failure')\n")
            interpreter = root / '.venv/bin/python'
            interpreter.parent.mkdir(parents=True)
            interpreter.symlink_to(sys.executable)
            log = configure_logging(root / 'logs')
            controller = Controller({'slides': [{'id': 'mc', 'title': 'MC', 'kind': 'mc', 'captions': True}]},
                argparse.Namespace(demo=False, live_caption=str(root), caption_config=str(root/'config.yaml'), replay=None, log_path=log))
            loop = QEventLoop()
            controller.process.finished.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
            try:
                self.assertTrue(controller.error)
                self.assertIn('Synthetic caption startup failure', controller.state['status'])
                self.assertIn('exit 1', controller.state['status'])
                controller.ingest('caption', 'PRIVATE TRANSCRIPT CONTENT')
                text = log.read_text()
                self.assertIn('Traceback (most recent call last)', text)
                self.assertIn('RuntimeError: Synthetic caption startup failure', text)
                self.assertIn('code=1', text)
                self.assertNotIn('PRIVATE TRANSCRIPT CONTENT', text)
                self.assertEqual(controller.state['logPath'], str(log))
            finally:
                controller.timer.stop()
                controller.close()
                logger = logging.getLogger('cadenza')
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                    handler.close()
