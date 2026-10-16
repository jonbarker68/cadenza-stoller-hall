"""Check the actual welcome slide artwork and subtitle clearance."""
import os
from pathlib import Path
import subprocess
import sys
import unittest


class WelcomeLayoutTests(unittest.TestCase):
    def test_all_logos_load_and_leave_subtitle_space(self):
        project = Path(__file__).resolve().parents[1]
        script = '''
from pathlib import Path
import argparse
from PySide6.QtCore import QCoreApplication,QEvent,QEventLoop,QObject,QPointF,QTimer,QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlExpression
from PySide6.QtQuick import QQuickView
from cadenza.app import Controller
from cadenza.model import load_show
app=QGuiApplication([])
show=load_show('config/show.yaml')
c=Controller(show,argparse.Namespace(demo=True,pdf_subtitles=True))
c.timer.stop()
c.move(next(i for i,s in enumerate(show['slides']) if s['id']=='mc-introduction'))
c.setOverride('ON')
view=QQuickView()
view.setResizeMode(QQuickView.SizeRootObjectToView)
view.rootContext().setContextProperty('controller',c)
errors=[]
view.engine().warnings.connect(lambda warnings: errors.extend(e.toString() for e in warnings))
view.setSource(QUrl.fromLocalFile(str(Path('src/cadenza/qml/Slide.qml').resolve())))
view.show()
def wait():
    loop=QEventLoop();QTimer.singleShot(100,loop.quit);loop.exec()
for width,height in ((1280,720),(1920,1080),(1024,768)):
    view.resize(width,height);wait()
    c.ingest('final','Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 4)
    wait()
    root=view.rootObject()
    panel=root.findChild(QObject,'welcomeLogoPanel')
    caption=root.findChild(QObject,'captionBand')
    assert panel.mapToItem(root,QPointF(0,panel.height())).y() < caption.y()
    def visual_find(item,name):
        if item.objectName()==name:
            return item
        for child in item.childItems():
            found=visual_find(child,name)
            if found is not None:
                return found
        return None
    for name in ('logoCadenza','logoCamerata','logoEpsrc',*[f'logoUniversity{i}' for i in range(4)]):
        logo=visual_find(root,name)
        assert logo is not None,name
        expression=QQmlExpression(view.rootContext(),logo,'status === 1')
        result=expression.evaluate()
        assert result[0],(name,result,expression.error().toString())
        assert logo.x()>=0 and logo.y()>=0
assert not errors, errors
view.close();view.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
c.close()
print('PASS: seven original logos loaded; subtitle clearance checked at three resolutions')
'''
        result = subprocess.run([sys.executable, '-c', script], cwd=project,
            env=dict(os.environ,PYTHONPATH=str(project/'src'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software'),
            capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
