# App/Extensions/Forms/BankListEditForm.py

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QStackedLayout, QVBoxLayout, QHBoxLayout, QSizePolicy, QButtonGroup

from qfluentwidgets import ProgressRing, ScrollArea, RadioButton

# App/Extensions
from App.Extensions.Widgets.ComboBoxCard import ComboBoxCard
from App.Extensions.Widgets.CardGroup import CardGroup


MAX_ROWS: int = 128


class BankListEditForm(QWidget):
    def __init__(self, count: int, listType: str, currentList: list, combinedPresets: list, builtinPresets=None, userPresets=None, parent=None):
        super().__init__(parent)
        self.count = count
        self.listType = listType
        self.combinedPresets = combinedPresets
        self.builtinPresets = builtinPresets or []
        self.userPresets = userPresets or []
        self.currentList = currentList or [None] * count

        self.presetMap = {id(p): p for p in self.combinedPresets}
        self.builtinMap = {id(p): p for p in self.builtinPresets}
        self.userMap = {id(p): p for p in self.userPresets}

        self.comboBoxes = []
        self.rowWidgets = []
        self._rowCreationIndex = 0

        self._initForm()
        self._initLayout()

        self.radioGroup.buttonClicked.connect(self._onFilterChanged)
        QTimer.singleShot(0, self._createRowsIncrementally)

    def _initForm(self):
        self._createSpinner()
        self._createFilterGroup()
        self._createListGroup()

    def _initLayout(self):
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(8)

        self.stack = QStackedLayout()

        self.stack.addWidget(self.spinnerContainer)

        self.contentGroup = QWidget()
        contentLayout = QVBoxLayout(self.contentGroup)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(16)

        contentLayout.addWidget(self.filterGroup)
        contentLayout.addWidget(self.listGroup)

        self.stack.addWidget(self.contentGroup)

        self.mainLayout.addLayout(self.stack)

        # Show spinner initially
        self.stack.setCurrentIndex(0)

    def _createSpinner(self):
        self.spinnerContainer = QWidget(self)
        spinnerLayout = QVBoxLayout(self.spinnerContainer)
        spinnerLayout.setContentsMargins(0, 0, 0, 0)
        spinnerLayout.addStretch()

        self.progressRing = ProgressRing(self.spinnerContainer)
        self.progressRing.setFixedSize(132, 132)
        self.progressRing.setMaximum(MAX_ROWS)
        self.progressRing.setValue(0)

        spinnerLayout.addWidget(self.progressRing, alignment=Qt.AlignmentFlag.AlignHCenter)
        spinnerLayout.addStretch()

    def _createFilterGroup(self):
        self.filterGroup = CardGroup('Preset filter', 14, self)

        self.radioGroup = QButtonGroup(self)
        filterLayout = QHBoxLayout()
        filterLayout.setContentsMargins(20, 0, 20, 0)

        self.radioAll = RadioButton('All presets')
        self.radioBuiltin = RadioButton('Built-in presets')
        self.radioUser = RadioButton('User-defined presets')

        self.radioAll.setChecked(True)

        self.radioGroup.addButton(self.radioAll, 0)
        self.radioGroup.addButton(self.radioBuiltin, 1)
        self.radioGroup.addButton(self.radioUser, 2)

        filterLayout.addWidget(self.radioAll)
        filterLayout.addWidget(self.radioBuiltin)
        filterLayout.addWidget(self.radioUser)

        self.radioWidget = QWidget(self.filterGroup)
        self.radioWidget.setLayout(filterLayout)

        self.filterGroup.addCard(self.radioWidget)

    def _createListGroup(self):
        self.listGroup = CardGroup(f'{self.listType[:-1].title()} list', 14, self)
        self.listGroup.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.scrollArea = ScrollArea(self.listGroup)
        self.scrollArea.setStyleSheet('background-color: transparent; border: none;')
        self.scrollArea.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.contentWidget = QWidget(self)
        self.formLayout = QVBoxLayout(self.contentWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setSpacing(4)
        self.formLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.contentWidget)
        self.scrollArea.setMinimumHeight(280)

        self.listGroup.addCard(self.scrollArea)

    def _onFilterChanged(self):
        filterId = self.radioGroup.checkedId()

        match filterId:
            case 0:
                filtered = self.combinedPresets
            case 1:
                filtered = self.builtinPresets
            case 2:
                filtered = self.userPresets
            case _:
                filtered = self.combinedPresets

        self._applyPresetFilter(filtered)

    def _applyPresetFilter(self, filteredPresets):
        newPresetMap = {id(p): p for p in filteredPresets}

        for combo in self.comboBoxes:
            current_preset = combo.currentData()
            combo.blockSignals(True)

            combo.clear()
            combo.addItem("None", userData=None)

            # If current selection is filtered out, add it explicitly
            if current_preset is not None and id(current_preset) not in newPresetMap:
                combo.addItem(current_preset.name, userData=current_preset)

            for p in filteredPresets:
                combo.addItem(p.name, userData=p)

            # Now set selection back to current preset (the item we just added or existing)
            for j in range(combo.count()):
                if combo.itemData(j) == current_preset:
                    combo.setCurrentIndex(j)
                    break
            else:
                combo.setCurrentIndex(0)

            combo.blockSignals(False)

        self.presetMap = newPresetMap

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
            texts=['None'] + [p.name for p in self.combinedPresets],
            defaultIndex=0
        )

        combo = comboCard.comboBox
        combo.setFixedWidth(260)
        comboCard.setFixedHeight(56)

        combo.setItemData(0, None)
        for j, preset in enumerate(self.combinedPresets, start=1):
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
        self._onFilterChanged()
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
        # return [cb.currentData() for i, cb in enumerate(self.comboBoxes) if i < self.count]
        return [self.presetMap.get(cb.currentData()) for i, cb in enumerate(self.comboBoxes) if i < self.count]
