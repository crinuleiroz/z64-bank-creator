# App/Views/Pages/HomePage.py

from PySide6.QtCore import Qt, QEasingCurve, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy


class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('homePage')