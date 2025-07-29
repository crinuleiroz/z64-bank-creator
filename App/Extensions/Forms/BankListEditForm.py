# App/Extensions/Forms/BankListEditForm.py

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout, QSizePolicy

from qfluentwidgets import ProgressRing, IndeterminateProgressRing, ScrollArea

# App/Extensions
from App.Extensions.Widgets.ComboBoxCard import ComboBoxCard


MAX_ROWS: int = 128


class BankListEditForm(QWidget):
    def __init__(self, count: int, listType: str, presets: list, currentList: list, parent=None):
        super().__init__(parent)
        self.count = count
        self.listType = listType
        self.presets = presets
        self.currentList = currentList or [None] * count

        self.comboBoxes = []
        self.rowWidgets = []
        self._rowCreationIndex = 0

        self._initForm()
        self._initLayout()

        QTimer.singleShot(0, self._createRowsIncrementally)

    def _initForm(self):
        ...

    def _initLayout(self):
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(8)

        self.stack = QStackedLayout()
        self.mainLayout.addLayout(self.stack)

        # Spinner
        self.spinnerContainer = QWidget(self)
        spinnerLayout = QVBoxLayout(self.spinnerContainer)
        spinnerLayout.setContentsMargins(0, 0, 0, 0)
        spinnerLayout.addStretch()
        # self.spinner = IndeterminateProgressRing(self.spinnerContainer)
        # self.spinner.setFixedSize(96, 96)
        self.progressRing = ProgressRing(self.spinnerContainer)
        self.progressRing.setFixedSize(132, 132)
        self.progressRing.setMaximum(MAX_ROWS)
        self.progressRing.setValue(0)
        spinnerLayout.addWidget(self.progressRing, alignment=Qt.AlignmentFlag.AlignHCenter)
        spinnerLayout.addStretch()
        self.stack.addWidget(self.spinnerContainer)

        # Scroll area
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setStyleSheet('background-color: transparent; border: none;')
        self.scrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.contentWidget = QWidget(self)
        self.formLayout = QVBoxLayout(self.contentWidget)
        self.formLayout.setContentsMargins(8, 8, 8, 8)
        self.formLayout.setSpacing(4)
        self.formLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.contentWidget)
        self.stack.addWidget(self.scrollArea)

        # Show spinner initially
        self.stack.setCurrentIndex(0)

    def _createRowsIncrementally(self):
        if self._rowCreationIndex >= MAX_ROWS:
            self._onRowsCreated()
            return

        i = self._rowCreationIndex
        labelPrefix = 'Program' if self.listType == 'instruments' else 'Key'
        labelIndex = i if self.listType == 'instruments' else (21 + i) % 128

        rowWidget = QWidget()
        rowLayout = QHBoxLayout(rowWidget)
        rowLayout.setContentsMargins(8, 0, 12, 0)

        comboCard = ComboBoxCard(
            title=f'{labelPrefix} {labelIndex}',
            texts=['None'] + [p.name for p in self.presets],
            defaultIndex=0
        )

        combo = comboCard.comboBox
        combo.setItemData(0, None)
        combo.setFixedWidth(260)
        comboCard.setFixedHeight(56)

        for j, preset in enumerate(self.presets, start=1):
            combo.setItemData(j, preset)

        # if i < len(self.currentList):
        #     selected = self.currentList[i]
        #     for j in range(combo.count()):
        #         if combo.itemData(j) == selected:
        #             combo.setCurrentIndex(j)
        #             break

        self.comboBoxes.append(combo)
        self.rowWidgets.append(rowWidget)

        rowLayout.addWidget(comboCard)
        self.formLayout.addWidget(rowWidget)

        self._rowCreationIndex += 1
        self.progressRing.setValue(self._rowCreationIndex)
        QTimer.singleShot(0, self._createRowsIncrementally)

    def _onRowsCreated(self):
        self.updateVisibleRows(self.count)
        self.stack.setCurrentIndex(1)

    def updateVisibleRows(self, count: int):
        self.count = count

        self.contentWidget.setUpdatesEnabled(False)
        self.contentWidget.setVisible(False)

        for i, row in enumerate(self.rowWidgets):
            if i < count:
                selected = self.currentList[i] if i < len(self.currentList) else None

                combo = self.comboBoxes[i]
                combo.setCurrentIndex(0)

                for j in range(combo.count()):
                    # Need to figure out a more consistent way to set these...
                    # ID works most of the time, but sometimes fails, and get_hash()
                    # can point to a completely different object... and I do not
                    # want to store hashes or UUIDs in the files...
                    if combo.itemData(j) == selected:
                        combo.setCurrentIndex(j)
                        break

                row.setVisible(True)
            else:
                row.setVisible(False)

        self.contentWidget.setUpdatesEnabled(True)
        self.contentWidget.setVisible(True)

    def showEvent(self, event):
        super().showEvent(event)
        self.stack.setCurrentIndex(0)

        self.comboBoxes.clear()
        self.rowWidgets.clear()
        while self.formLayout.count():
            item = self.formLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._rowCreationIndex = 0
        QTimer.singleShot(0, self._createRowsIncrementally)

    def getSelection(self):
        return [cb.currentData() for i, cb in enumerate(self.comboBoxes) if i < self.count]
