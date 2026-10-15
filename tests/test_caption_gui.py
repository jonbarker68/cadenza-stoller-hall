import os
from pathlib import Path
import subprocess
import sys
import unittest


class CaptionGuiTests(unittest.TestCase):
    @unittest.skipUnless(Path('/Users/jon/projects/live-caption/src/live_caption/renderers/live.py').exists(),
                         'Requires the local shared live-caption renderer')
    def test_measured_layout_animation_and_raw_replay(self):
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                   PYTHONPATH=str(project / 'src'))
        result = subprocess.run([sys.executable, str(project / 'tests/helpers/caption_gui_check.py')],
            cwd=project, env=env, capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS:', result.stdout)
