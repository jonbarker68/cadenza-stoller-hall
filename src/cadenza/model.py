"""Validated show definitions and monotonic presentation timing."""
import math
import time
import yaml

KINDS = {'arrivals', 'intro', 'mc', 'experiment', 'music', 'response', 'countup', 'closing'}


def validate_slide_style(style):
    """Validate the optional standard-slide presentation controls."""
    if not isinstance(style, dict):
        raise ValueError('style must be a mapping')
    allowed = {'alignment', 'content_y', 'side_margin', 'spacing', 'title', 'body', 'subtitle'}
    if set(style) - allowed:
        raise ValueError('Unknown style option: ' + ', '.join(sorted(set(style) - allowed)))
    if 'alignment' in style and style['alignment'] not in ('left', 'center', 'right'):
        raise ValueError('style.alignment must be left, center or right')
    def number(value, name, positive=False):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (value <= 0 if positive else value < 0):
            raise ValueError(f'{name} must be a finite ' + ('positive' if positive else 'non-negative') + ' number')
    for key in ('content_y', 'side_margin', 'spacing'):
        if key in style:
            number(style[key], 'style.' + key)
    if style.get('side_margin', 0) >= 640:
        raise ValueError('style.side_margin must be less than 640 reference pixels')
    for role in ('title', 'body', 'subtitle'):
        if role not in style:
            continue
        values = style[role]
        if not isinstance(values, dict):
            raise ValueError(f'style.{role} must be a mapping')
        if set(values) - {'font_size', 'bold', 'italic', 'font_family'}:
            raise ValueError(f'Unknown style.{role} font option')
        if 'font_size' in values:
            number(values['font_size'], f'style.{role}.font_size', positive=True)
        for key in ('bold', 'italic'):
            if key in values and not isinstance(values[key], bool):
                raise ValueError(f'style.{role}.{key} must be true or false')
        if 'font_family' in values and (not isinstance(values['font_family'], str) or not values['font_family'].strip()):
            raise ValueError(f'style.{role}.font_family must be non-empty text')


def load_show(path):
    with open(path, encoding='utf-8') as stream:
        show = yaml.safe_load(stream)
    if not isinstance(show, dict) or not isinstance(show.get('slides'), list) or not show['slides']:
        raise ValueError('Show must contain a non-empty slides list')
    ids = set()
    for index, slide in enumerate(show['slides']):
        if not isinstance(slide, dict):
            raise ValueError(f'Slide {index + 1} must be a mapping')
        if not isinstance(slide.get('id'), str) or not slide['id'] or slide['id'] in ids:
            raise ValueError(f'Slide {index + 1} needs a unique string id')
        ids.add(slide['id'])
        if slide.get('kind') not in KINDS:
            raise ValueError(f"Unknown slide kind: {slide.get('kind')}")
        if not isinstance(slide.get('title'), str):
            raise ValueError('Every slide needs a title')
        if not isinstance(slide.get('captions', False), bool):
            raise ValueError('captions must be true or false')
        for key in ('body', 'subtitle', 'notes', 'movement'):
            if key in slide and not isinstance(slide[key], str):
                raise ValueError(f'{key} must be text')
        if 'style' in slide:
            validate_slide_style(slide['style'])
        if slide['kind'] == 'response':
            duration = slide.get('duration')
            if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
                raise ValueError('Response duration must be a positive finite number')
    return show


def timer_text(seconds):
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    return f'{minutes:02}:{seconds:02}'


class Timeline:
    """One manually cued timer for the current slide."""
    def __init__(self, slides, now=time.monotonic):
        self.slides, self.now = slides, now
        self.index = 0
        self.reset_timer()

    @property
    def slide(self):
        return self.slides[self.index]

    @property
    def has_timer(self):
        return self.slide['kind'] in ('response', 'countup')

    def reset_timer(self):
        self.saved = 0
        self.started = None
        self.phase = 'ready'

    def move(self, delta):
        target = min(len(self.slides) - 1, max(0, self.index + delta))
        if target == self.index:
            return False
        self.index = target
        self.reset_timer()
        return True

    def elapsed(self):
        return self.saved + (self.now() - self.started if self.started is not None else 0)

    def update(self):
        if self.slide['kind'] == 'response' and self.phase == 'running' and self.elapsed() >= self.slide['duration']:
            self.saved = self.slide['duration']
            self.started = None
            self.phase = 'finished'

    def value(self):
        self.update()
        if self.slide['kind'] == 'response':
            return max(0, self.slide['duration'] - self.elapsed())
        return self.elapsed()

    def toggle_timer(self):
        self.update()
        if not self.has_timer or self.phase in ('stopped', 'finished'):
            return
        if self.phase == 'running':
            self.saved = self.elapsed()
            self.started = None
            self.phase = 'paused'
        else:
            self.started = self.now()
            self.phase = 'running'

    def stop_restart(self):
        self.update()
        if not self.has_timer or self.phase == 'ready':
            return
        if self.phase in ('running', 'paused'):
            self.saved = self.elapsed()
            self.started = None
            self.phase = 'stopped'
        else:
            self.reset_timer()
            self.toggle_timer()
