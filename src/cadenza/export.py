"""Render the real audience QML into a static, one-slide-per-page PDF."""
import argparse
import os
from pathlib import Path
import tempfile


def export_pdf(show, destination):
    # Select the headless software renderer before creating any Qt application.
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['QT_QUICK_BACKEND'] = 'software'
    from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, QMarginsF, QSizeF, QTimer, QUrl
    from PySide6.QtGui import QGuiApplication, QPageLayout, QPageSize, QPainter, QPdfWriter
    from PySide6.QtQuick import QQuickView
    from .app import Controller

    app = QGuiApplication([])
    controller = Controller(show, argparse.Namespace(demo=True))
    controller.timer.stop()  # No synthetic captions or advancing timers in the PDF.
    view = QQuickView()
    warnings = []
    view.engine().warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
    view.rootContext().setContextProperty('controller', controller)
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(1920, 1080)
    view.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / 'qml/Slide.qml')))
    destination = Path(destination).expanduser().resolve()
    temporary = None
    painter = QPainter()
    writer = None
    try:
        if view.status() == QQuickView.Error:
            raise RuntimeError('Could not load slide QML: ' + '\n'.join(e.toString() for e in view.errors()))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.pdf', delete=False) as stream:
            temporary = Path(stream.name)
        writer = QPdfWriter(str(temporary))
        writer.setTitle(show.get('title', 'Cadenza slide review'))
        writer.setCreator('Cadenza slide export')
        writer.setResolution(144)
        writer.setPageLayout(QPageLayout(
            QPageSize(QSizeF(960, 540), QPageSize.Point, 'Audience slide'),
            QPageLayout.Portrait, QMarginsF(0, 0, 0, 0), QPageLayout.Point))
        if not painter.begin(writer):
            raise RuntimeError('Could not initialise PDF output')
        view.show()
        for index in range(len(show['slides'])):
            controller.move(index - controller.timeline.index)
            # Let bindings, image loading, layouts and Canvas painting settle.
            loop = QEventLoop()
            QTimer.singleShot(100, loop.quit)
            loop.exec()
            image = view.grabWindow()
            if image.isNull():
                raise RuntimeError(f'Could not render slide {index + 1}')
            if warnings:
                raise RuntimeError('QML rendering errors: ' + '\n'.join(warnings))
            if index and not writer.newPage():
                raise RuntimeError('Could not add PDF page')
            painter.drawImage(painter.viewport(), image)
        painter.end()
        writer = None  # Close the PDF before atomically replacing the output.
        temporary.replace(destination)
        return destination
    finally:
        if painter.isActive():
            painter.end()
        writer = None
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        view.close()
        view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        controller.close()
