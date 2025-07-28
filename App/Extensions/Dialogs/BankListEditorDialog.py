# App/Extensions/Dialogs/BankListEditorDialog.py

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout, QSizePolicy

from qfluentwidgets import MessageBoxBase, SubtitleLabel, IndeterminateProgressRing, ScrollArea

# App/Extensions
from App.Extensions.Widgets.ComboBoxCard import ComboBoxCard


MAX_ROWS = 128


class BankListEditorDialog(MessageBoxBase):
    # REFACTOR LATER
    def __init__(self, title: str, count: int, presets: list, presetType='instruments', existingList=None, parent=None):
        super().__init__(parent)

        self.count = count
        self.presets = presets
        self.presetType = presetType.lower()
        self.existingList = existingList or [None] * count

        self.comboBoxes = []
        self.rowWidgets = []
        self._rowCreationIndex = 0

        # Container
        containerWidget = QWidget(self)
        containerLayout = QVBoxLayout(containerWidget)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSpacing(12)

        # Title
        titleLabel = SubtitleLabel(title, containerWidget)
        containerLayout.addWidget(titleLabel, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Spinner and Scroll container
        self.stack = QStackedLayout()
        containerLayout.addLayout(self.stack)

        # Spinner container with centering layout
        self.spinnerContainer = QWidget(containerWidget)
        spinnerLayout = QVBoxLayout(self.spinnerContainer)
        spinnerLayout.setContentsMargins(0, 0, 0, 0)
        spinnerLayout.addStretch(1)
        self.spinner = IndeterminateProgressRing(self.spinnerContainer)
        self.spinner.setFixedSize(128, 128)
        self.spinner.setStrokeWidth(8)
        spinnerLayout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignHCenter)
        spinnerLayout.addStretch(1)

        # Scroll area setup
        self.scrollArea = ScrollArea(containerWidget)
        self.scrollArea.setStyleSheet('background-color: transparent; border: none;')
        self.scrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.contentWidget = QWidget()
        self.contentWidget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.formLayout = QVBoxLayout(self.contentWidget)
        self.formLayout.setSpacing(4)
        self.formLayout.setContentsMargins(8, 8, 8, 8)
        self.formLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.contentWidget)

        # Add spinner container and scroll area to the stack
        self.stack.addWidget(self.spinnerContainer)  # index 0
        self.stack.addWidget(self.scrollArea)        # index 1

        self.stack.setCurrentIndex(0)  # Show spinner initially

        self.viewLayout.addWidget(containerWidget)

        # Fix dialog size
        self.widget.setFixedWidth(550)
        self.widget.setFixedHeight(550)

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

    def _createRowsIncrementally(self):
        if self._rowCreationIndex >= MAX_ROWS:
            self._onRowsCreated()
            return

        i = self._rowCreationIndex
        labelPrefix = 'Program' if self.presetType == 'instruments' else 'Key'
        labelIndex = i if self.presetType == 'instruments' else (21 + i) % 128

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

        for i, preset in enumerate(self.presets, start=1):
            combo.setItemData(i, preset)

        self.comboBoxes.append(combo)
        self.rowWidgets.append(rowWidget)

        rowLayout.addWidget(comboCard)

        rowWidget.setVisible(False)
        self.formLayout.addWidget(rowWidget)

        self._rowCreationIndex += 1
        QTimer.singleShot(0, self._createRowsIncrementally)

    def _onRowsCreated(self):
        self.stack.setCurrentIndex(1)
        self.updateVisibleRows(self.count)

    def updateVisibleRows(self, count: int):
        self.count = count

        self.contentWidget.setUpdatesEnabled(False)
        self.contentWidget.setVisible(False)

        for i, row in enumerate(self.rowWidgets):
            if i < count:
                selected = self.existingList[i] if i < len(self.existingList) else None

                combo = self.comboBoxes[i]
                combo.setCurrentIndex(0)

                for j in range(combo.count()):
                    if combo.itemData(j) == selected:
                        combo.setCurrentIndex(j)
                        break

                row.setVisible(True)
            else:
                row.setVisible(False)

        self.contentWidget.setUpdatesEnabled(True)
        self.contentWidget.setVisible(True)

    def get_selection(self):
        return [cb.currentData() for i, cb in enumerate(self.comboBoxes) if i < self.count]
