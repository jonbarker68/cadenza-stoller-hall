"""Atomic event checkpoints, with no caption text or credentials."""
import json
import math
import os
from pathlib import Path
import tempfile


class EventCheckpoint:
    def __init__(self, path, show_path):
        self.path = Path(path).expanduser().resolve()
        self.show_path = str(Path(show_path).expanduser().resolve())
        self.last = None
        self.preferences = {}

    def restore(self, timeline):
        if not self.path.exists():
            return ''
        state = json.loads(self.path.read_text())
        if not isinstance(state, dict):
            raise ValueError('Invalid checkpoint format')
        if state.get('version') != 1 or state.get('show') != self.show_path:
            raise ValueError('Saved position belongs to another show')
        index = next((i for i, s in enumerate(timeline.slides) if s.get('id') == state.get('slide')), None)
        if index is None:
            raise ValueError('Saved slide is no longer in this programme')
        elapsed = state.get('elapsed', 0)
        phase = state.get('phase', 'ready')
        if (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
                or not math.isfinite(elapsed) or elapsed < 0
                or phase not in ('ready', 'running', 'paused', 'stopped', 'finished')):
            raise ValueError('Invalid saved timer')
        self.preferences = {
            'override': state.get('override', 'AUTO') if state.get('override') in ('AUTO', 'ON', 'OFF') else 'AUTO',
            'speaker_override': state.get('speaker_override', 'AUTO') if state.get('speaker_override') in ('AUTO', 'WHITE', 'SPEAKERS') else 'AUTO',
        }
        timeline.move(index - timeline.index)
        if (timeline.has_timer and timeline.slide['kind'] == state.get('kind')
                and timeline.slide.get('duration') == state.get('duration')):
            timeline.saved = min(elapsed, timeline.slide['duration']) if timeline.slide['kind'] == 'response' else elapsed
            timeline.phase = 'paused' if phase == 'running' else phase
            timeline.started = None
        return f'Resumed slide {index + 1}: {timeline.slide["title"]}. Check the audience display and timer before continuing.'

    def save(self, timeline, override='AUTO', speaker_override='AUTO'):
        timeline.update()
        state = dict(version=1, show=self.show_path, slide=timeline.slide.get('id'),
                     kind=timeline.slide['kind'], duration=timeline.slide.get('duration'),
                     elapsed=int(timeline.elapsed()) if timeline.has_timer else 0,
                     phase=timeline.phase, override=override, speaker_override=speaker_override)
        if state == self.last:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=self.path.parent, suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(state, stream)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)
            self.last = state
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
