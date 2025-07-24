import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme

# App Imports
import App.Common.Resources
from App.Common.Config import cfg
from App.MainWindow import MainWindow


# Application Attributes
QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

# For now, always set dark theme
if cfg.get(cfg.themeMode.value) != "Dark":
    cfg.set(cfg.themeMode, Theme.DARK)

# DPI Scaling
if cfg.get(cfg.dpiscale) == 'Auto':
    passthrough = Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    QApplication.setHighDpiScaleFactorRoundingPolicy(passthrough)
else:
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    os.environ['QT_SCALE_FACTOR'] = str(cfg.get(cfg.dpiscale))

app = QApplication(sys.argv)
win = MainWindow()

app.exec()