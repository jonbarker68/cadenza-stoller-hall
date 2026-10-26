"""Move the native audience window before requesting full screen."""
import logging

from PySide6.QtCore import QObject, QRect, QTimer, Qt
from PySide6.QtGui import QGuiApplication

logger = logging.getLogger('cadenza')


class AudienceDisplay(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pending = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish)

    def present(self, window, index, fullscreen):
        screens = QGuiApplication.screens()
        if window is None or not 0 <= index < len(screens):
            return
        self.timer.stop()
        screen = screens[index]
        # setScreen alone does not move a window on a shared virtual desktop.
        # Hide/restore first to leave an existing macOS full-screen Space.
        window.hide()
        window.setWindowState(Qt.WindowNoState)
        window.setScreen(screen)
        area = screen.availableGeometry()
        width = min(1280, area.width())
        height = min(720, area.height())
        window.setGeometry(QRect(area.x() + (area.width() - width) // 2,
                                 area.y() + (area.height() - height) // 2,
                                 width, height))
        window.showNormal()
        self.pending = (window, screen, fullscreen)
        # Let the window manager commit the new position before full screen.
        self.timer.start(250)
        logger.info('Audience display selected: %s geometry=%s fullscreen=%s',
                    screen.name(), area, fullscreen)

    def finish(self):
        if self.pending is None:
            return
        window, screen, fullscreen = self.pending
        self.pending = None
        if screen not in QGuiApplication.screens():
            logger.warning('Audience display disconnected before presentation')
            return
        if fullscreen:
            window.showFullScreen()
        window.raise_()

    def cancel(self):
        self.timer.stop()
        self.pending = None
