# App/Extensions/Widgets/ComboBoxCard.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

from qfluentwidgets import BodyLabel, SimpleCardWidget, CaptionLabel, SwitchButton
from qfluentwidgets import FluentIcon as FIF


class SwitchButtonCard(SimpleCardWidget):
    """ Simple card widget with a switch button. """

    def __init__(self, title, content=None, onText='On', offText='Off', parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel(title, self)
        self.contentLabel = CaptionLabel(content or '', self)
        self.switchButton = SwitchButton(self)
        self.switchButton.setOffText(offText)
        self.switchButton.setOnText(onText)

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
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)

        if not onText and not offText:
            self.hBoxLayout.setContentsMargins(20, 11, 0, 11)

    def setTitle(self, title: str):
        """ set the title of card """
        self.titleLabel.setText(title)

    def setContent(self, content: str):
        """ set the content of card """
        self.contentLabel.setText(content)
        self.contentLabel.setVisible(bool(content))

    def setChecked(self, isChecked):
        """ set the value of config item """
        self.switchButton.setChecked(isChecked)