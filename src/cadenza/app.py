import argparse
import json
import math
import logging
from pathlib import Path
import sys
import time
import yaml

from PySide6.QtCore import QObject, Property, QProcess, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QFont, QFontMetricsF
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from .model import Timeline, timer_text, load_show

logger = logging.getLogger("cadenza")


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
        self.caption_preview = bool(getattr(args, 'pdf_subtitles', False))
        self.caption_renderer = None
        self.caption_layout_key = None
        self.caption_serial = 0
        self.caption_scroll = 0
        self.caption_line_height = 40.0
        self.caption_settings = getattr(args, 'caption_settings', {})
        self.caption_layout_name = getattr(args, 'caption_layout', 'bbc_live')
        self.live_caption_root = Path(getattr(args, 'live_caption', '/Users/jon/projects/live-caption'))
        overlay_settings = self.caption_settings.get('overlay', {})
        self.caption_width_fraction = float(overlay_settings.get('width_fraction', 0))
        self.caption_max_width = float(overlay_settings.get('max_width', 0))
        for key, value in (('width_fraction', self.caption_width_fraction), ('max_width', self.caption_max_width)):
            if not math.isfinite(value) or value < 0 or (key in overlay_settings and value == 0):
                raise ValueError(f'overlay.{key} must be positive and finite')
        if self.caption_width_fraction > 1:
            raise ValueError('overlay.width_fraction must not exceed 1')
        self.caption_scroll_ms = float(self.caption_settings.get('overlay', {}).get('scroll_duration_ms', 180))
        if not math.isfinite(self.caption_scroll_ms) or not 0 <= self.caption_scroll_ms <= 1000:
            raise ValueError('overlay.scroll_duration_ms must be between 0 and 1000')
        self.status = (
            'Demo captions · no microphone'
            if args.demo
            else 'Captions disconnected'
        )
        self.error = False
        self.buffer = b''
        self.stderr_buffer = b''
        self.stderr_tail = ''
        self.closing = False
        self.received_caption = False
        self.log_path = str(getattr(args, 'log_path', ''))
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
            self.process.readyReadStandardError.connect(self.read_diagnostics)
            self.process.errorOccurred.connect(self.process_error)
            self.process.finished.connect(self.finished)

            root = Path(args.live_caption).expanduser().resolve()
            interpreter = root / '.venv/bin/python'
            config = str(Path(args.caption_config).expanduser().resolve())

            logger.info('Caption source: interpreter=%s config=%s mode=%s', interpreter, config, 'replay' if args.replay else 'live')
            if not interpreter.exists():
                self.status = (
                    'Caption interpreter missing: ' + str(interpreter)
                )
                self.error = True
                logger.error('%s', self.status)
            else:
                self.status = 'Starting caption source…'
                self.process.start(
                    str(interpreter),
                    [
                        str(Path(__file__).with_name('bridge.py')),
                        str(root),
                        config,
                        args.replay or '',
                        '--raw',
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
            layout=s.get('layout', ''),
            body=s.get('body', ''),
            subtitle=s.get('subtitle', ''),
            style=s.get('style', {}),
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
            captionSerial=self.caption_serial,
            captionPreview=self.caption_preview,
            captionMeasured=self.caption_layout_name == "bbc_live",
            captionWidthFraction=self.caption_width_fraction,
            captionMaxWidth=self.caption_max_width,
            captionScroll=self.caption_scroll,
            captionLineHeight=self.caption_line_height,
            captionScrollMs=self.caption_scroll_ms if self.caption_layout_name == 'bbc_live' else 0,
            override=self.override,
            status=self.status,
            logPath=self.log_path,
            error=self.error,
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

    def reset_captions(self):
        self.caption = self.final_text = ''
        self.caption_scroll = 0
        self.caption_serial += 1
        if self.caption_renderer is not None:
            self.caption_renderer.reset()

    @Slot(str, int, float)
    def configureCaptionLayout(self, family, pixel_size, width):
        key = (family, pixel_size, round(width, 3))
        if key == self.caption_layout_key or width <= 0 or pixel_size <= 0:
            return
        try:
            # Import only the shared pure-Python renderers, never ASR or the
            # native overlay. Qt measurements remain on the GUI thread.
            root = str(self.live_caption_root.expanduser().resolve() / 'src')
            if root not in sys.path:
                sys.path.insert(0, root)
            from live_caption.renderers import make_renderer, TextLayout
            font = QFont(family)
            font.setPixelSize(pixel_size)
            metrics = QFontMetricsF(font)
            config = dict(self.caption_settings)
            config.update(config.get('overlay', {}))
            # The audience component reserves exactly two line positions.
            config['bbc'] = dict(config.get('bbc', {}), lines=2)
            self.caption_renderer = make_renderer(self.caption_layout_name, config,
                layout=TextLayout(max(1, width - 2), metrics.horizontalAdvance))
            self.caption_line_height = math.ceil(metrics.lineSpacing())
            self.caption_layout_key = key
            self.reset_captions()
            logger.info('Caption layout=%s font=%s size=%s width=%s line_height=%s scroll_ms=%s',
                        self.caption_layout_name, family, pixel_size, width,
                        self.caption_line_height, self.caption_scroll_ms)
        except (ImportError, ValueError, TypeError, AttributeError, OSError) as exc:
            self.ingest('error', 'Caption layout failed: ' + str(exc))
        self.changed.emit()

    @Slot(int)
    def move(self, delta):
        if self.timeline.move(delta):
            logger.info('Slide %s/%s id=%s', self.timeline.index + 1, len(self.timeline.slides), self.timeline.slide.get('id', ''))
            self.reset_captions()
        self.changed.emit()

    @Slot(str)
    def setOverride(self, value):
        if value in ('AUTO', 'ON', 'OFF'):
            logger.info('Caption override: %s', value)
            self.override = value
            self.reset_captions()
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
        if kind in ('caption', 'partial', 'final') and text and not self.received_caption:
            self.received_caption = True
            logger.info('First caption received (transcript omitted)')
        if kind == 'error':
            logger.error('Caption source: %s', text)
            self.error = True
            self.status = text

        elif kind == 'status' and not self.error:
            if self.status != text:
                logger.info('Caption status: %s', text)
            self.status = text

        elif kind == 'caption' and self.state['captions']:
            # Already-rendered caption state from bridge.py.
            # Replace the current display verbatim; do not accumulate it.
            self.caption = text
            self.caption_scroll = 0
            self.caption_serial += 1
            self.caption_at = time.monotonic()

        elif kind in ('partial', 'final') and self.state['captions']:
            if self.caption_renderer is not None:
                try:
                    self.caption = (self.caption_renderer.add_final(text) if kind == 'final'
                                    else self.caption_renderer.update_partial(text))
                    self.caption_scroll = getattr(self.caption_renderer, 'scroll_lines', 0)
                except ValueError as exc:
                    self.ingest('error', 'Caption layout failed: ' + str(exc))
                    return
            else:
                # Retained for non-GUI consumers. The running QML presentation
                # configures measured rendering before caption events arrive.
                if kind == 'final':
                    self.final_text = (self.final_text + ' ' + text).strip()[-240:]
                    self.caption = self.final_text
                else:
                    self.caption = (self.final_text + ' ' + text).strip()[-240:]
                self.caption_scroll = 0
            self.caption_serial += 1
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

    def read_diagnostics(self, final=False):
        self.stderr_buffer += bytes(self.process.readAllStandardError())
        while b'\n' in self.stderr_buffer:
            line, self.stderr_buffer = self.stderr_buffer.split(b'\n', 1)
            self.log_diagnostic_line(line)
        if final and self.stderr_buffer:
            self.log_diagnostic_line(self.stderr_buffer)
            self.stderr_buffer = b''
        elif len(self.stderr_buffer) > 16384:
            self.log_diagnostic_line(self.stderr_buffer)
            self.stderr_buffer = b''

    def log_diagnostic_line(self, line):
        text = line.decode('utf-8', errors='replace').strip()
        if text:
            # Keep the complete traceback in the log; show only the last line.
            logger.warning('Caption stderr: %s', text)
            self.stderr_tail = text[-400:]

    def process_error(self, error):
        if self.closing:
            return
        self.read_diagnostics(final=True)
        detail = ': ' + self.stderr_tail if self.stderr_tail else ''
        self.ingest('error', 'Caption source failed: ' + self.process.errorString() + detail)

    def finished(self, code, status):
        self.read_caption()
        self.read_diagnostics(final=True)
        logger.info('Caption process exited: code=%s status=%s requested_shutdown=%s', code, status, self.closing)
        if not self.closing:
            if code != 0:
                detail = self.stderr_tail or 'No diagnostic output; see log for process details'
                if not self.error:
                    self.ingest('error', f'Caption source failed (exit {code}): {detail}')
            elif not self.error:
                self.status = 'Caption source ended'
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
            self.reset_captions()

        self.changed.emit()

    def close(self):
        self.closing = True
        logger.info('Presentation shutting down')
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

    parser.add_argument('--pdf-subtitles', action='store_true',
                        help='Include sample subtitles and a region outline in the PDF (requires --export-pdf)')

    parser.add_argument('--log-dir', type=Path, default=Path('logs'),
                        help='Diagnostic log directory (default: logs)')

    parser.add_argument('--caption-layout', choices=('bbc_live', 'bbc', 'rolling'), default='bbc_live',
                        help='Caption layout (default: bbc_live; bbc and rolling are legacy options)')

    args = parser.parse_args()
    if args.export_pdf and (args.live or args.replay):
        parser.error('--export-pdf cannot be combined with --live or --replay')
    if args.pdf_subtitles and not args.export_pdf:
        parser.error('--pdf-subtitles requires --export-pdf')
    args.demo = not (args.live or args.replay)
    args.caption_settings = {}
    if not args.demo or Path(args.caption_config).exists():
        try:
            root = str(Path(args.live_caption).expanduser().resolve() / 'src')
            if root not in sys.path:
                sys.path.insert(0, root)
            from live_caption.config import load_config
            settings = load_config(args.caption_config)
            # Keep credentials out of presentation state. Schema and processing
            # are owned by live-caption; the bridge applies processing once.
            args.caption_settings = {key: settings.get(key, {}) for key in ('overlay', 'bbc')}
        except (OSError, ValueError, TypeError, AttributeError, ImportError, yaml.YAMLError) as exc:
            parser.error('Invalid caption configuration: ' + str(exc))

    from .diagnostics import configure_logging, configured_secrets
    try:
        args.log_path = configure_logging(args.log_dir, configured_secrets(args.caption_config))
    except OSError as exc:
        parser.exit(1, f'Cannot open diagnostic log: {exc}. Use --log-dir with a writable directory.\n')
    logger.info('Starting Cadenza mode=%s show=%s log=%s',
                'export' if args.export_pdf else 'demo' if args.demo else 'replay' if args.replay else 'live',
                args.show.resolve(), args.log_path)
    def report_exception(exc_type, value, traceback):
        logger.critical('Unhandled application exception', exc_info=(exc_type, value, traceback))
    sys.excepthook = report_exception

    try:
        show = load_show(args.show)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        logger.exception('Show loading failed')
        parser.error(str(exc))

    if args.export_pdf:
        from .export import export_pdf
        try:
            output = export_pdf(show, args.export_pdf, args=args)
        except (OSError, RuntimeError) as exc:
            parser.exit(1, f'PDF export failed: {exc}\n')
        print(f"Exported {len(show['slides'])} slides to {output}")
        return 0

    # Native macOS controls can ignore palette overrides in dark mode.
    # Fusion keeps the operator controls consistent with our explicit palette.
    QQuickStyle.setStyle("Fusion")

    from PySide6.QtCore import qInstallMessageHandler, QtMsgType
    def qt_message(kind, context, message):
        level = logging.ERROR if kind in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg) else logging.WARNING
        logger.log(level, 'Qt: %s', message)
    qInstallMessageHandler(qt_message)
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