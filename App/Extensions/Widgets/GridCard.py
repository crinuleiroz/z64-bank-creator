# App/Extensions/Widgets/GridCard.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QWidget

from qfluentwidgets import SimpleCardWidget, BodyLabel


class GridCard(SimpleCardWidget):
    def __init__(self, title='Grid card', parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)

        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(20, 11, 11, 11)
        self.gridLayout.setSpacing(8)

        self._hasTitle = bool(title.strip())
        self._nextColumn = 0

        if self._hasTitle:
            self.titleLabel = BodyLabel(title, self)
            self.gridLayout.addWidget(self.titleLabel, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            self._nextColumn = 1

    def addWidget(self, widget: QWidget):
        self.gridLayout.addWidget(widget, 0, self._nextColumn)
        self._nextColumn += 1

    def addWidgets(self, widgets: list[QWidget]):
        for widget in widgets:
            self.gridLayout.addWidget(widget, 0, self._nextColumn)
            self._nextColumn += 1
