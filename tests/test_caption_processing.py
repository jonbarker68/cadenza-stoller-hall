"""Exercise the real bridge process without microphone/network access."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

LIVE = Path('/Users/jon/projects/live-caption')
PROJECT = Path(__file__).resolve().parents[1]


@unittest.skipUnless((LIVE / 'src/live_caption/processor.py').exists(), 'Requires shared live-caption checkout')
class CaptionProcessingIntegrationTests(unittest.TestCase):
    def bridge(self, config, raw, vocabulary=None):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            settings = folder / 'config.yaml'
            settings.write_text(config)
            recording = folder / 'recording.jsonl'
            events = [('final', 'Welcome'), ('partial', 'fucking everyone'),
                      ('partial', 'temporary'), ('partial', 'shit'),
                      ('final', 'fuck'), ('final', 'everyone.')]
            recording.write_text(''.join(json.dumps(dict(type='asr', t=0, kind=kind, text=text)) + '\n'
                                         for kind, text in events))
            command = [sys.executable, str(PROJECT / 'src/cadenza/bridge.py'),
                       str(LIVE), str(settings), str(recording)]
            if vocabulary is not None:
                vocabulary_path = folder / 'vocabulary with spaces.yaml'
                vocabulary_path.write_text(vocabulary)
                command.extend(['--vocabulary', str(vocabulary_path)])
            if raw:
                command.append('--raw')
            result = subprocess.run(command, capture_output=True, text=True, timeout=10,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(result.returncode, 0, result.stderr)
            return [json.loads(line) for line in result.stdout.splitlines()]

    def test_default_omit_in_processed_hypothesis_protocol(self):
        events = [e for e in self.bridge('{}', True) if e['kind'] in ('partial', 'final')]
        self.assertEqual([(e['kind'], e['text']) for e in events],
            [('final', 'Welcome'), ('partial', 'everyone'), ('partial', 'temporary'),
             ('partial', ''), ('final', ''), ('final', 'everyone.')])

    def test_legacy_rendered_protocol_all_layouts(self):
        for layout in ('rolling', 'bbc', 'bbc_live'):
            with self.subTest(layout=layout):
                events = [e['text'] for e in self.bridge('overlay: {layout: ' + layout + '}', False)
                          if e['kind'] == 'caption']
                self.assertEqual(events, ['Welcome', 'Welcome everyone', 'Welcome temporary',
                                          'Welcome', 'Welcome', 'Welcome everyone.'])

    def test_off_and_legacy_opt_out(self):
        for config in ('processing: {profanity: {mode: off}}',
                       'processing: {profanity_filter: false}'):
            with self.subTest(config=config):
                texts = [e['text'] for e in self.bridge(config, True) if e['kind'] in ('partial', 'final')]
                self.assertIn('fucking everyone', texts)
                self.assertIn('fuck', texts)

    def test_bridge_cli_overrides_missing_configured_dictionary(self):
        events = self.bridge('vocabulary_file: missing.yaml', True, '- Cadenza\n')
        self.assertTrue(any(event['text'] == 'Welcome' for event in events))

    def test_cadenza_cli_validates_shared_vocabulary_and_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'config.yaml'
            config.write_text('vocabulary_file: missing.yaml\n')
            vocabulary = root / 'words.yaml'
            vocabulary.write_text('- Cadenza\n')
            env = dict(os.environ, PYTHONPATH=str(PROJECT / 'src'), QT_QPA_PLATFORM='offscreen',
                       QT_QUICK_BACKEND='software', PYTHONDONTWRITEBYTECODE='1')
            command = [sys.executable, '-m', 'cadenza.app', '--caption-config', str(config),
                       '--log-dir', str(root / 'logs'), '--smoke-test']
            bad = subprocess.run(command, cwd=PROJECT, env=env, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('missing.yaml', bad.stderr)
            good = subprocess.run(command + ['--vocabulary-file', str(vocabulary)], cwd=PROJECT,
                                  env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
