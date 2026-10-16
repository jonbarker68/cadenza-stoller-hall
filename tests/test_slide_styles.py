import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml
from cadenza.model import load_show


class SlideStyleTests(unittest.TestCase):
    def test_invalid_style_and_subtitle_are_rejected(self):
        invalid = [dict(style=[]), dict(style={'aligmnent': 'center'}),
                   dict(style={'alignment': 'middle'}), dict(style={'spacing': -1}),
                   dict(style={'side_margin': 640}), dict(style={'body': {'font_size': True}}),
                   dict(style={'body': {'font_size': 0}}), dict(style={'title': {'font_size': float('nan')}}),
                   dict(style={'subtitle': {'italic': 'yes'}}), dict(style={'title': {'font_family': ''}}),
                   dict(subtitle=['not text'])]
        for options in invalid:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                p=Path(directory)/'show.yaml'
                p.write_text(yaml.safe_dump({'slides':[dict(id='test',kind='mc',title='Title',**options)]}))
                with self.assertRaises(ValueError):
                    load_show(p)

    def test_actual_slide_styles_and_default_fallback(self):
        project=Path(__file__).resolve().parents[1]
        script='''
import argparse
from pathlib import Path
from PySide6.QtCore import QCoreApplication,QEvent,QEventLoop,QObject,QPointF,QTimer,QUrl
from PySide6.QtGui import QGuiApplication,QFontInfo,QFontMetricsF,QFont
from PySide6.QtQml import QQmlExpression
from PySide6.QtQuick import QQuickView
from cadenza.app import Controller
from cadenza.model import load_show
app=QGuiApplication([])
show=load_show('config/show.yaml')
c=Controller(show,argparse.Namespace(demo=True))
c.timer.stop()
c.move(next(i for i,s in enumerate(show['slides']) if s['id']=='gabor-takacs-nagy'))
view=QQuickView();view.setResizeMode(QQuickView.SizeRootObjectToView)
view.rootContext().setContextProperty('controller',c)
errors=[]
view.engine().warnings.connect(lambda warnings: errors.extend(e.toString() for e in warnings))
view.setSource(QUrl.fromLocalFile(str(Path('src/cadenza/qml/Slide.qml').resolve())))
view.show()
def wait():
    loop=QEventLoop();QTimer.singleShot(80,loop.quit);loop.exec()
for width,height in ((1920,1080),(1024,768),(1280,720)):
    view.resize(width,height);wait()
    c.ingest('final','Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 4);wait()
    root=view.rootObject();scale=root.property('scaleUnit')
    body=root.findChild(QObject,'slideBody');subtitle=root.findChild(QObject,'slideSubtitle')
    assert body.property('font').pixelSize()==round(64*scale)
    assert body.property('font').bold()
    assert subtitle.property('font').italic()
    assert subtitle.property('font').pixelSize()==round(30*scale)
    assert subtitle.property('text')=='Conductor of the Manchester Camerata'
    assert subtitle.y() >= body.y()+body.height()
    assert subtitle.mapToItem(root,QPointF(0,subtitle.height())).y() < root.findChild(QObject,'captionBand').y()
    assert QQmlExpression(view.rootContext(),body,'horizontalAlignment === 4').evaluate()[0]
view.grabWindow().save('/tmp/cadenza-gabor-style.png')
# Omitted styles preserve the normal MC font sizes.
c.timeline.slides.append({'id':'default','kind':'mc','title':'Default','body':'Just sit back and enjoy!'})
c.move(len(c.timeline.slides));wait()
root=view.rootObject()
assert root.findChild(QObject,'slideTitle').property('font').pixelSize()==48
assert root.findChild(QObject,'slideBody').property('font').pixelSize()==29
body=root.findChild(QObject,'slideBody')
font=body.property('font')
assert font.family()==app.font().family(),repr(font.family())
assert 'emoji' not in QFontInfo(font).family().lower()
expected=QFont(app.font());expected.setPixelSize(29)
assert abs(body.property('contentWidth')-QFontMetricsF(expected).horizontalAdvance(body.property('text'))) < 1

assert not root.findChild(QObject,'slideSubtitle').isVisible()
assert not errors,errors
view.close();view.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);c.close()
'''
        result=subprocess.run([sys.executable,'-c',script],cwd=project,
            env=dict(os.environ,PYTHONPATH=str(project/'src'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software'),
            capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
