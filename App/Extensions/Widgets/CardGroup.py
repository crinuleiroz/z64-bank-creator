# App/Extensions/Widgets/CardGroup.py

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from qfluentwidgets import FluentStyleSheet, setFont, ExpandLayout


class CardGroup(QWidget):
    """ Setting card group """

    def __init__(self, title: str, fontSize: int=20, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = QLabel(title, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.cardLayout = ExpandLayout()

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.setSpacing(0)
        self.cardLayout.setContentsMargins(0, 0, 0, 0)
        self.cardLayout.setSpacing(2)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addLayout(self.cardLayout, 1)

        FluentStyleSheet.SETTING_CARD_GROUP.apply(self)
        setFont(self.titleLabel, fontSize, QFont.Weight.DemiBold)
        self.titleLabel.adjustSize()

    def addCard(self, card: QWidget):
        """ add setting card to group """
        card.setParent(self)
        self.cardLayout.addWidget(card)
        self.adjustSize()

    def addCards(self, cards: List[QWidget]):
        """ add setting cards to group """
        for card in cards:
            self.addCard(card)

    def adjustSize(self):
        h = self.cardLayout.heightForWidth(self.width()) + 46
        return self.resize(self.width(), h)
