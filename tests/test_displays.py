"""Screen changes must move the window before requesting full screen."""
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QCoreApplication, QRect
from cadenza.displays import AudienceDisplay


class AudienceDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.presenter = AudienceDisplay()
        self.addCleanup(self.presenter.cancel)
        self.laptop, self.dell = Mock(), Mock()
        self.dell.availableGeometry.return_value = QRect(-1920, 0, 1920, 1080)
        self.screen_patch = patch('cadenza.displays.QGuiApplication.screens', return_value=[self.laptop, self.dell])
        self.screen_patch.start()
        self.addCleanup(self.screen_patch.stop)

    def test_dell_position_committed_before_fullscreen(self):
        window = Mock()
        self.presenter.present(window, 1, True)
        window.setScreen.assert_called_once_with(self.dell)
        window.setGeometry.assert_called_once_with(QRect(-1600, 180, 1280, 720))
        window.showNormal.assert_called_once()
        window.showFullScreen.assert_not_called()
        self.presenter.finish()
        window.showFullScreen.assert_called_once()
        calls = [call[0] for call in window.mock_calls]
        self.assertLess(calls.index('setWindowState'), calls.index('setGeometry'))
        self.assertLess(calls.index('setGeometry'), calls.index('showFullScreen'))

    def test_windowed_selection_moves_without_fullscreen(self):
        window = Mock()
        self.presenter.present(window, 1, False)
        self.presenter.finish()
        window.setScreen.assert_called_once_with(self.dell)
        window.showFullScreen.assert_not_called()

    def test_latest_selection_replaces_pending_request(self):
        window = Mock()
        self.laptop.availableGeometry.return_value = QRect(0, 0, 1440, 900)
        self.presenter.present(window, 1, True)
        self.presenter.present(window, 0, False)
        self.presenter.finish()
        window.showFullScreen.assert_not_called()
        self.assertEqual(window.setScreen.call_args.args, (self.laptop,))

    def test_cancel_and_disconnected_screen_do_not_enter_fullscreen(self):
        window = Mock()
        self.presenter.present(window, 1, True)
        self.presenter.cancel()
        self.presenter.finish()
        window.showFullScreen.assert_not_called()
        self.presenter.present(window, 1, True)
        with patch('cadenza.displays.QGuiApplication.screens', return_value=[self.laptop]):
            self.presenter.finish()
        window.showFullScreen.assert_not_called()
