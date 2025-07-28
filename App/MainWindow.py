# App/MainWindow.py

import os
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QLabel

from qfluentwidgets import NavigationItemPosition, FluentWindow, SystemThemeListener, SplashScreen

# App/Common
from App.Common.Config import cfg, isWin11, APP_VERSION
from App.Common.SignalBus import signalBus
from App.Common.Helpers import load_image_and_resize_image, apply_opacity_to_pixmap
from App.Common.Presets import builtinPresetStore, userPresetStore

# App/Extensions
from App.Extensions.Components.MSFluentIcons import MSFluentIcon as FICO

# App/Views/Pages
from App.Views.Pages.HomePage import HomePage
from App.Views.Pages.BanksPage import BanksPage
from App.Views.Pages.PresetsPage import PresetsPage
from App.Views.Pages.SettingsPage import SettingsPage


class MainWindow(FluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._isMicaEnabled = False
        self._originalPixmap = None
        self._lastScaledSize = QSize()
        self._scaledPixmapCache = None

        # Splash Screen
        self.splashScreen = SplashScreen(':/assets/images/clef_icon.png', self)
        self.splashScreen.setIconSize(QSize(112, 112))

        # Init Window
        self.setObjectName('mainWindow')
        self._initWindow()
        self._centerWindowOnScreen()

        # Init Background
        self._initBackground()
        self._onBackgroundChanged(cfg.get(cfg.bgimage))
        self.show()

        # Init presets
        self.builtinPresets = builtinPresetStore
        self.userPresets = userPresetStore
        self._loadAllPresets()

        # Set up Pages
        self._initPages()
        self._initNavigation()

        # Theme Listener
        self._themeListener = SystemThemeListener(self)
        self._themeListener.start()
        self._connectSlots()

        QTimer.singleShot(1200, self.splashScreen.finish)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.onUpdate)
        self.updateTimer.start(16)

    #region Initialization
    def _initWindow(self):
        #self.resize(960, 1000)
        self.resize(1096, 1096)
        self.setResizeEnabled(False)
        self.setMinimumWidth(740)
        self.setMinimumHeight(540)
        self.setWindowTitle(f'Zelda64 Bank Editor {APP_VERSION}')
        self.setWindowIcon(QIcon(':/assets/images/clef_icon.png'))

        if isWin11():
            self.setMicaEffectEnabled(True)

    def _initBackground(self):
        self.bgLabel = QLabel(self)
        self.bgLabel.setObjectName("backgroundLabel")
        self.bgLabel.lower()

    def _initPages(self):
        self.homePage = HomePage(self)
        self.banksPage = BanksPage(self)
        self.presetsPage = PresetsPage(self)
        self.settingsPage = SettingsPage(self)

    def _initNavigation(self):
        # Home Page
        self.addSubInterface(
            interface=self.homePage,
            icon=FICO.HOME,
            text='Home',
            isTransparent=False
        )

        # Banks Page
        self.addSubInterface(
            interface=self.banksPage,
            icon=FICO.LIBRARY,
            text='Banks',
            isTransparent=False
        )

        # Presets Page
        self.addSubInterface(
            interface=self.presetsPage,
            icon=FICO.DOCUMENT,
            text='Presets',
            isTransparent=False
        )

        # Settings Page
        self.addSubInterface(
            interface=self.settingsPage,
            icon=FICO.SETTINGS,
            text='Settings',
            position=NavigationItemPosition.BOTTOM,
            isTransparent=False
        )

    def _connectSlots(self):
        cfg.backgroundChanged.connect(self._onBackgroundChanged)
        cfg.bgopacity.valueChanged.connect(self._updateBackgroundOpacity)
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
    #endregion

    #region Window and Background
    def _onBackgroundChanged(self, imgPath):
        if imgPath and os.path.exists(imgPath):
            screenSize = QApplication.primaryScreen().size()
            pixmap = load_image_and_resize_image(
                imgPath,
                target_size=(screenSize.width(), screenSize.height()),
                keep_aspect=True
            )
            if not pixmap.isNull():
                self._originalPixmap = pixmap
            else:
                self._originalPixmap = None
        else:
            self._originalPixmap = None

        self._scaledPixmapCache = None
        self._applyBackground()

    def _updateBackgroundOpacity(self, _: int):
        self._applyBackground()

    def _applyBackground(self):
        if self._originalPixmap is None:
            # Try to load fallback
            imgPath = cfg.get(cfg.bgimage)
            if not imgPath or not os.path.exists(imgPath):
                self.bgLabel.clear()
                return

            pixmap = QPixmap(imgPath)
            if pixmap.isNull():
                self.bgLabel.clear()
                return

            self._originalPixmap = pixmap

        targetSize = self.size()
        if self._scaledPixmapCache is None or targetSize != self._lastScaledSize:
            self._scaledPixmapCache = self._originalPixmap.scaled(
                targetSize,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.FastTransformation
            )
            self._lastScaledSize = targetSize

        self.bgLabel.setPixmap(self._scaledPixmapCache)

        # Position image
        x = (targetSize.width() - self._scaledPixmapCache.width()) // 2
        y = (targetSize.height() - self._scaledPixmapCache.height()) // 2
        self.bgLabel.setGeometry(x, y, self._scaledPixmapCache.width(), self._scaledPixmapCache.height())

        # Apply opacity
        opacity = cfg.get(cfg.bgopacity) / 100.0
        pixmap_with_opacity = apply_opacity_to_pixmap(self._scaledPixmapCache, opacity)
        self.bgLabel.setPixmap(pixmap_with_opacity)

        self.bgLabel.lower()

    def _centerWindowOnScreen(self):
        desktop = QApplication.primaryScreen()
        w, h = (desktop.geometry().width(), desktop.geometry().height())
        self.move(
            w//2 - self.width()//2,
            h//2 - self.height()//2
        )
    #endregion

    #region Load Presets
    def _loadAllPresets(self):
        self.builtinPresets.load_builtin_presets()
        self.userPresets.load_user_presets(Path(cfg.get(cfg.presetsfolder)))
    #endregion

    def onUpdate(self):
        self.update()

    def closeEvent(self, e):
        self._themeListener.terminate()
        self._themeListener.deleteLater()
        super().closeEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._applyBackground()
