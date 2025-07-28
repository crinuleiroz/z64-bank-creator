# App/Extensions/Widgets/Frame.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout

from qfluentwidgets import ListWidget


class Frame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QVBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.setObjectName('frame')
        self.setStyleSheet('''
            QFrame#frame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        ''')

    def addWidget(self, widget):
        self.hBoxLayout.addWidget(widget)


class ListFrame(Frame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.listWidget = ListWidget(self)
        self.addWidget(self.listWidget)