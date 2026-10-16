"""Exercise the export switch through the CLI and inspect rendered PDF pages."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class PdfSubtitleTests(unittest.TestCase):
    def test_optional_overlay_on_every_page_and_configured_width(self):
        project = Path(__file__).resolve().parents[1]
        env = dict(os.environ, PYTHONPATH=str(project / 'src'), QT_QPA_PLATFORM='offscreen')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            show = root / 'show.yaml'
            show.write_text('slides:\n- {id: welcome, kind: mc, title: Welcome, captions: false}\n'
                            '- {id: response, kind: response, title: Complete your responses, duration: 60, captions: false}\n')
            config = root / 'captions.yaml'
            config.write_text('overlay: {width_fraction: 0.50, max_width: 900}\n')
            for preview in (False, True):
                output = root / ('preview.pdf' if preview else 'plain.pdf')
                command = [sys.executable, '-m', 'cadenza.app', '--show', str(show),
                           '--caption-config', str(config), '--export-pdf', str(output),
                           '--log-dir', str(root / 'logs')]
                if preview:
                    command.append('--pdf-subtitles')
                result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            inspect = '''
import sys
from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication
from PySide6.QtPdf import QPdfDocument
app = QGuiApplication([])
for path, preview in [(sys.argv[1], False), (sys.argv[2], True)]:
    doc = QPdfDocument()
    assert doc.load(path) == QPdfDocument.Error.None_
    assert doc.pageCount() == 2
    for page in range(2):
        image = doc.render(page, QSize(1280,720))
        assert not image.isNull()
        pink = []
        white = 0
        for y in range(565,700):
            for x in range(1280):
                c = image.pixelColor(x,y)
                if c.red() > 180 and c.blue() > 150 and c.green() < 170:
                    pink.append((x,y))
                if 340 < x < 940 and c.red() > 210 and c.green() > 210 and c.blue() > 210:
                    white += 1
        if preview:
            assert len(pink) > 1000, len(pink)
            assert 317 <= min(x for x,y in pink) <= 325
            assert 955 <= max(x for x,y in pink) <= 963
            assert white > 500, white
        else:
            assert not pink
            assert white == 0
print('PASS: subtitle outline and sample text on both pages; configured half-width; plain export unchanged')
'''
            result = subprocess.run([sys.executable, '-c', inspect, str(root/'plain.pdf'), str(root/'preview.pdf')],
                env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_preview_requires_pdf_export(self):
        project = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, '-m', 'cadenza.app', '--pdf-subtitles'],
            cwd=project, env=dict(os.environ, PYTHONPATH=str(project/'src')),
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--pdf-subtitles requires --export-pdf', result.stderr)
