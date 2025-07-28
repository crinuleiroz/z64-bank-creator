# App/Extensions/Widgets/WidgetCard.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

from qfluentwidgets import BodyLabel, SimpleCardWidget, CaptionLabel


class WidgetCard(SimpleCardWidget):
    """ Simple card widget with a combo box. """

    def __init__(self, title, content=None, widget=None, parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content or '', self)
        self.widget = widget

        if not content:
            self.contentLabel.hide()

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedHeight(72)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")

        self.hBoxLayout.setContentsMargins(20, 11, 11, 11)
        self.hBoxLayout.setSpacing(15)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        self.vBoxLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.widget, 0, Qt.AlignmentFlag.AlignRight)

    def setTitle(self, title: str):
        """ set the title of card """
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        """ set the content of card """
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def addWidget(self, widget):
        self.hBoxLayout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)