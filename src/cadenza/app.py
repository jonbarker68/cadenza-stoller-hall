import argparse
import json
import math
from pathlib import Path
import sys
import time
import yaml

from PySide6.QtCore import QObject, Property, QProcess, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .model import Timeline, timer_text, load_show


class Controller(QObject):
    changed = Signal()

    def __init__(self, show, args):
        super().__init__()
        self.timeline = Timeline(show['slides'])
        self.show = show
        self.override = 'AUTO'
        self.caption = ''
        self.final_text = ''
        self.caption_at = 0
        self.status = (
            'Demo captions · no microphone'
            if args.demo
            else 'Captions disconnected'
        )
        self.error = False
        self.buffer = b''
        self.process = None
        self.demo = args.demo
        self.demo_index = 0
        self.last_demo = time.monotonic()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)

        if not args.demo:
            self.process = QProcess(self)
            self.process.readyReadStandardOutput.connect(self.read_caption)
            self.process.readyReadStandardError.connect(
                lambda: self.process.readAllStandardError()
            )
            self.process.errorOccurred.connect(self.process_error)
            self.process.finished.connect(self.finished)

            root = Path(args.live_caption).expanduser().resolve()
            interpreter = root / '.venv/bin/python'
            config = str(Path(args.caption_config).expanduser().resolve())

            if not interpreter.exists():
                self.status = (
                    'Caption interpreter missing: ' + str(interpreter)
                )
                self.error = True
            else:
                self.status = 'Starting caption source…'
                self.process.start(
                    str(interpreter),
                    [
                        str(Path(__file__).with_name('bridge.py')),
                        str(root),
                        config,
                        args.replay or '',
                    ],
                )

    @Property('QVariantMap', notify=changed)
    def state(self):
        t = self.timeline
        s = t.slide

        enabled = (
            self.override == 'ON'
            or (
                self.override == 'AUTO'
                and s.get('captions', False)
            )
        )

        value = t.value()
        display_time = timer_text(
            math.ceil(value)
            if s["kind"] == "response"
            else value
        )

        return dict(
            title=s['title'],
            body=s.get('body', ''),
            kind=s['kind'],
            notes=s.get('notes', ''),
            passage=str(s.get('passage', '')),
            movement=s.get('movement', ''),
            page=str(s.get('page', '')),
            index=t.index,
            count=len(t.slides),
            nextTitle=(
                t.slides[t.index + 1]['title']
                if t.index + 1 < len(t.slides)
                else 'End of programme'
            ),
            captions=enabled,
            caption=self.caption if enabled else '',
            override=self.override,
            status=self.status,
            timerTime=display_time,
            fraction=(
                value / s['duration']
                if s['kind'] == 'response'
                else 0
            ),
            hasTimer=t.has_timer,
            timerPhase=t.phase,
            timerAction=(
                'Pause'
                if t.phase == 'running'
                else 'Resume'
                if t.phase == 'paused'
                else 'Start'
            ),
            timerActionEnabled=t.phase in (
                'ready',
                'running',
                'paused',
            ),
            timerSecondary=(
                'Restart'
                if t.phase in ('stopped', 'finished')
                else 'Stop'
            ),
            timerSecondaryEnabled=t.phase != 'ready',
        )

    @Slot(int)
    def move(self, delta):
        if self.timeline.move(delta):
            self.caption = self.final_text = ''
        self.changed.emit()

    @Slot(str)
    def setOverride(self, value):
        if value in ('AUTO', 'ON', 'OFF'):
            self.override = value
            self.caption = self.final_text = ''
            self.changed.emit()

    @Slot()
    def timerToggle(self):
        self.timeline.toggle_timer()
        self.changed.emit()

    @Slot()
    def timerStopRestart(self):
        self.timeline.stop_restart()
        self.changed.emit()

    def ingest(self, kind, text):
        if kind == 'error':
            self.error = True
            self.status = text

        elif kind == 'status' and not self.error:
            self.status = text

        elif kind == 'caption' and self.state['captions']:
            # Already-rendered caption state from bridge.py.
            # Replace the current display verbatim; do not accumulate it.
            self.caption = text
            self.caption_at = time.monotonic()

        elif kind in ('partial', 'final') and self.state['captions']:
            # Legacy/raw caption path, retained for demo mode or any source
            # that still emits unrendered partial/final transcript events.
            if kind == 'final':
                self.final_text = (
                    self.final_text + ' ' + text
                ).strip()[-240:]
                self.caption = self.final_text
            else:
                self.caption = (
                    self.final_text + ' ' + text
                ).strip()[-240:]

            self.caption_at = time.monotonic()

        self.changed.emit()

    def read_caption(self):
        self.buffer += bytes(
            self.process.readAllStandardOutput()
        )

        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)

            try:
                message = json.loads(line)
                self.ingest(
                    message['kind'],
                    message['text'],
                )
            except (ValueError, KeyError, TypeError):
                self.ingest(
                    'error',
                    'Invalid caption-source message',
                )

    def process_error(self, error):
        self.ingest(
            'error',
            'Caption source failed: '
            + self.process.errorString(),
        )

    def finished(self, code, status):
        self.read_caption()

        if not self.error:
            self.status = (
                'Caption source ended'
                if code == 0
                else (
                    'Caption source failed — check configuration '
                    'and microphone access'
                )
            )

        self.changed.emit()

    def tick(self):
        now = time.monotonic()

        if self.demo and now - self.last_demo >= 5:
            lines = [
                'Welcome to this evening’s listening experiment.',
                'Listen to the music and reflect on what you hear.',
                'Thank you for being part of this shared experience.',
            ]

            self.final_text = ''
            self.ingest(
                'final',
                lines[self.demo_index % len(lines)],
            )
            self.demo_index += 1
            self.last_demo = now

        if self.caption and now - self.caption_at > 8:
            self.caption = self.final_text = ''

        self.changed.emit()

    def close(self):
        if (
            self.process
            and self.process.state() != QProcess.NotRunning
        ):
            self.process.terminate()

            if not self.process.waitForFinished(2500):
                self.process.kill()
                self.process.waitForFinished(1000)


def main():
    parser = argparse.ArgumentParser(
        description='Cadenza · Stoller Hall presentation controller'
    )

    parser.add_argument(
        '--show',
        type=Path,
        default=Path('config/show.yaml'),
        help=(
            'Show YAML '
            '(default: config/show.yaml, relative to the working directory)'
        ),
    )

    source = parser.add_mutually_exclusive_group()

    source.add_argument(
        '--live',
        action='store_true',
        help='Capture live audio through live-caption',
    )

    source.add_argument(
        '--replay',
        help='Replay a live-caption JSONL recording',
    )

    parser.add_argument(
        '--live-caption',
        default='/Users/jon/projects/live-caption',
    )

    parser.add_argument(
        '--caption-config',
        default='config/caption-config.yaml',
        help=(
            'Audio/Speechmatics YAML '
            '(default: config/caption-config.yaml, '
            'relative to the working directory)'
        ),
    )

    parser.add_argument(
        '--smoke-test',
        action='store_true',
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        '--export-pdf', type=Path, metavar='PATH',
        help='Export audience slides to a 16:9 PDF and exit (no audio or live captions)',
    )

    args = parser.parse_args()
    if args.export_pdf and (args.live or args.replay):
        parser.error('--export-pdf cannot be combined with --live or --replay')
    args.demo = not (args.live or args.replay)

    try:
        show = load_show(args.show)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.error(str(exc))

    if args.export_pdf:
        from .export import export_pdf
        try:
            output = export_pdf(show, args.export_pdf)
        except (OSError, RuntimeError) as exc:
            parser.exit(1, f'PDF export failed: {exc}\n')
        print(f"Exported {len(show['slides'])} slides to {output}")
        return 0

    # Native macOS controls can ignore palette overrides in dark mode.
    # Fusion keeps the operator controls consistent with our explicit palette.
    QQuickStyle.setStyle("Fusion")

    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName(
        'Cadenza · Stoller Hall'
    )

    controller = Controller(show, args)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty(
        'controller',
        controller,
    )

    engine.load(
        QUrl.fromLocalFile(
            str(Path(__file__).parent / 'qml/Main.qml')
        )
    )

    if not engine.rootObjects():
        controller.close()
        return 1

    app.aboutToQuit.connect(controller.close)

    if args.smoke_test:
        QTimer.singleShot(500, app.quit)

    result = app.exec()

    engine.deleteLater()

    from PySide6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(
        None,
        QEvent.DeferredDelete,
    )

    return result


if __name__ == '__main__':
    sys.exit(main())