"""Subprocess-only checks: QGuiApplication must not share QCoreApplication tests."""
import argparse
import json
from pathlib import Path
import tempfile

from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QObject, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from cadenza.app import Controller


def wait(ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


QQuickStyle.setStyle('Fusion')
app = QGuiApplication([])
project = Path(__file__).resolve().parents[2]
show = {'slides': [{'id': 'mc', 'kind': 'mc', 'title': 'Welcome', 'captions': True},
                   {'id': 'next', 'kind': 'mc', 'title': 'Next', 'captions': True}]}
c = Controller(show, argparse.Namespace(demo=True))
c.timer.stop()
engine = QQmlApplicationEngine()
errors = []
engine.warnings.connect(lambda warnings: errors.extend(e.toString() for e in warnings))
engine.rootContext().setContextProperty('controller', c)
engine.load(QUrl.fromLocalFile(str(project / 'src/cadenza/qml/Main.qml')))
assert engine.rootObjects()
wait(50)
audience = next(w for w in app.allWindows() if w.title() == 'Cadenza · Audience')
band = audience.findChild(QObject, 'captionBand')
text = band.findChild(QObject, 'captionText')
animation = band.findChild(QObject, 'captionScrollAnimation')
assert c.caption_renderer is not None
assert c.caption_layout_name == 'bbc_live'

# Fill the viewport, then open the third line.
for _ in range(100):
    c.ingest('final', 'orchestra')
    if c.caption_scroll:
        break
    wait(1)
assert c.caption_scroll == 1
wait(60)
assert animation.property('running')
assert text.y() < 0
assert len(band.property('displayText').splitlines()) == 3
wait(180)
assert not animation.property('running')
assert text.y() == 0
assert band.property('displayText') == c.caption
assert len(c.caption.splitlines()) == 2
for line in c.caption.splitlines():
    assert c.caption_renderer.layout.fits(line)
assert text.property('font').pixelSize() == 31

# OFF and slide changes reset renderer history as well as visible text.
c.setOverride('OFF')
c.ingest('final', 'HIDDEN MUSIC WORDS')
assert c.caption == ''
c.setOverride('AUTO')
c.ingest('final', 'New introduction')
assert c.caption == 'New introduction'
c.move(1)
c.ingest('final', 'Fresh slide')
assert c.caption == 'Fresh slide'
c.caption_at -= 9
c.tick()
assert c.caption_renderer.current_text() == ''
c.ingest('final', 'After silence')
assert c.caption == 'After silence'

# Disabled animation remains immediate, including after a preceding run.
c.caption_scroll_ms = 0
c.reset_captions()
for _ in range(100):
    c.ingest('final', 'orchestra')
    if c.caption_scroll:
        break
wait(30)
assert not animation.property('running')
assert text.y() == 0
assert band.property('displayText') == c.caption

# Scaling changes presentation size without changing reference wrapping.
for width, height in ((1280, 720), (1920, 1080), (1024, 768)):
    audience.resize(width, height)
    wait(40)
    assert c.caption_renderer.layout.width == band.property('textWidthRef') - 2
    assert text.property('contentWidth') <= text.width() + 2
    assert band.y() >= 0
if __import__('os').environ.get('CADENZA_CAPTION_PREVIEW'):
    audience.resize(1280, 720)
    c.reset_captions()
    c.ingest('final', 'Welcome to the Cadenza concert. Please turn to the page shown on screen. We will listen to the orchestra together.')
    wait(40)
    audience.grabWindow().save('/tmp/cadenza-new-captions.png')
assert not errors, errors
engine.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
c.close()

# End-to-end raw bridge replay through the controller and measured renderer.
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    config = root / 'config.yaml'
    config.write_text('overlay: {scroll_duration_ms: 0}\n')
    recording = root / 'replay.jsonl'
    recording.write_text(''.join(json.dumps(dict(type='asr', t=t, kind=kind, text=words)) + '\n'
        for t, kind, words in [(0, 'partial', 'Test fucking phrase'), (.05, 'final', 'Test phrase'),
                              (.06, 'partial', 'temporary'), (.07, 'partial', 'shit'),
                              (.08, 'final', 'fuck'), (.1, 'final', 'from the bridge.')]))
    c2 = Controller(show, argparse.Namespace(demo=False, live_caption='/Users/jon/projects/live-caption',
        caption_config=str(config), replay=str(recording), caption_layout='bbc_live'))
    c2.configureCaptionLayout('Arial', 31, 1144)
    loop = QEventLoop()
    c2.process.finished.connect(loop.quit)
    QTimer.singleShot(8000, loop.quit)
    loop.exec()
    assert not c2.error, c2.status
    assert c2.caption == 'Test phrase from the bridge.', c2.caption
    # User-supplied region width must reach the actual QML band and metrics.
    c2.caption_width_fraction = .20
    c2.caption_max_width = 900
    engine2 = QQmlApplicationEngine()
    engine2.rootContext().setContextProperty('controller', c2)
    engine2.load(QUrl.fromLocalFile(str(project / 'src/cadenza/qml/Main.qml')))
    wait(50)
    root2 = engine2.rootObjects()[0]
    narrow_band = root2.findChild(QObject, 'captionBand')
    assert narrow_band.property('regionWidthRef') == 256
    assert narrow_band.property('textWidthRef') == 220
    assert c2.caption_renderer.layout.width == 218
    c2.reset_captions()
    c2.ingest('final', 'A narrow caption region wraps text at the configured width.')
    for line in c2.caption.splitlines():
        assert c2.caption_renderer.layout.fits(line)
    engine2.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    c2.timer.stop()
    c2.close()
print('PASS: measured Qt layout, scrolling, off switch, resets, 3 resolutions and raw bridge replay')
