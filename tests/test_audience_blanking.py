"""Exercise the real audience output, leaving the operator preview available."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class AudienceBlankingTests(unittest.TestCase):
    def test_hide_blackout_restore_and_uninterrupted_timer(self):
        project = Path(__file__).resolve().parents[1]
        script = '''
import argparse
from pathlib import Path
from PySide6.QtCore import QObject,QUrl,QEventLoop,QTimer,QCoreApplication,QEvent,QPointF
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from cadenza.app import Controller
QQuickStyle.setStyle('Fusion');app=QGuiApplication([])
show={'slides':[dict(id='mc',kind='mc',title='Welcome',captions=True),dict(id='response',kind='response',title='Respond',duration=60,captions=True)]}
c=Controller(show,argparse.Namespace(demo=True));c.timer.stop()
e=QQmlApplicationEngine();errors=[]
e.warnings.connect(lambda ws:errors.extend(w.toString() for w in ws))
e.rootContext().setContextProperty('controller',c)
e.load(QUrl.fromLocalFile(str(Path('src/cadenza/qml/Main.qml').resolve())))
def wait():
    loop=QEventLoop();QTimer.singleShot(100,loop.quit);loop.exec()
wait();root=e.rootObjects()[0]
audience=next(w for w in app.allWindows() if w.title()=='Cadenza · Audience')
slide=audience.findChild(QObject,'audienceSlide')
preview=root.findChild(QObject,'operatorPreviewSlide')
mask=slide.findChild(QObject,'audienceOutputMask')
preview_mask=preview.findChild(QObject,'audienceOutputMask')
band=slide.findChild(QObject,'captionBand')
c.ingest('final','This caption stays visible when the slide is hidden.');wait()
caption=c.caption
root.findChild(QObject,'hideSlidesButton').clicked.emit();wait()
assert c.state['audienceMode']=='captions'
assert mask.property('visible') and not preview_mask.property('visible')
assert band.property('visible') and c.caption==caption
im=audience.grabWindow();assert im.pixelColor(100,100).name()=='#000000'
assert any(im.pixelColor(x,y).red()>220 for y in range(570,690,3) for x in range(50,1200,3))
root.findChild(QObject,'blackoutButton').clicked.emit();wait()
assert not band.property('visible') and c.caption==caption
im=audience.grabWindow()
assert all(im.pixelColor(x,y).name()=='#000000' for y in range(0,720,8) for x in range(0,1280,8))
c.move(1);c.timerToggle();started=c.timeline.started
assert c.audience_mode=='blackout'
root.findChild(QObject,'restoreAudienceButton').clicked.emit();wait()
assert c.audience_mode=='normal' and not mask.property('visible')
assert c.timeline.index==1 and c.timeline.started==started and c.timeline.phase=='running'
root.findChild(QObject,'hideSlidesButton').clicked.emit();wait()
root.findChild(QObject,'hideSlidesButton').clicked.emit();wait()
assert c.audience_mode=='normal'
c.setAudienceMode('invalid');assert c.audience_mode=='normal'
c.setOverride('OFF');c.setAudienceMode('captions');wait();assert not band.property('visible')
root.setWidth(800);root.setHeight(860);wait()
restore=root.findChild(QObject,'restoreAudienceButton')
assert restore.mapToItem(None,QPointF(restore.width(),restore.height())).x()<=root.width()
assert root.findChild(QObject,'backButton').mapToItem(None,QPointF(0,0)).y()<restore.mapToItem(None,QPointF(0,0)).y()
root.grabWindow().save('/tmp/cadenza-blanking-panel.png')
assert not errors,errors
print('PASS: audience hides correctly, captions survive, preview stays visible, timers keep running, restore and toggles work')
e.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);c.close()
'''
        result = subprocess.run([sys.executable, '-c', script], cwd=project,
            env=dict(os.environ, PYTHONPATH=str(project/'src'), QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software'),
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertIn('PASS:', result.stdout)
