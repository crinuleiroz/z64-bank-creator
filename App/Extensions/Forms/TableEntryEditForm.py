# App/Extensions/BankCreationForm.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup

from qfluentwidgets import LineEdit, RadioButton

# App/Common
from App.Common.Audiobank import Audiobank, TableEntry, AudioStorageMedium, AudioCacheLoadType, SampleBankId

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup
from App.Extensions.Widgets.ComboBoxCard import ComboBoxCard
from App.Extensions.Widgets.SpinBoxCard import SpinBoxCard


class TableEntryEditForm(QWidget):
    def __init__(self, bank, parent=None):
        super().__init__(parent)
        self.bank = bank
        self.tableEntry = bank.tableEntry

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createGameGroup()
        self._createMetadataGroup()

        self._setupValues()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.gameGroup)
        layout.addWidget(self.metadataGroup)

    def _setupValues(self):
        # Set the name
        self.nameEdit.setText(self.bank.name)

        # Set the game
        gameMap = {'OOT': self.ootButton, 'MM': self.mmButton}
        selectedButton = gameMap.get(self.bank.game)
        if selectedButton:
            selectedButton.setChecked(True)
        self.ootButton.setEnabled(False)
        self.mmButton.setEnabled(False)

        # Set the audio type
        for i in range(self.bgmFanfareCard.comboBox.count()):
            data = self.bgmFanfareCard.comboBox.itemData(i)
            if data == self.tableEntry.cacheLoadType:
                self.bgmFanfareCard.comboBox.setCurrentIndex(i)
                break

        # Set the number of instruments, drums, and effects
        self.numInstrumentsCard.spinBox.setValue(self.tableEntry.numInstruments)
        self.numDrumsCard.spinBox.setValue(self.tableEntry.numDrums)
        self.numEffectsCard.spinBox.setValue(self.tableEntry.numEffects)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Bank Name', 14, self)
        self.nameEdit = LineEdit(self.nameGroup)
        self.nameGroup.addCard(self.nameEdit)

    def _createGameGroup(self):
        self.gameGroup = CardGroup('Game', 14, self)
        self.gameButtonGroup = QButtonGroup(self)

        self.ootButton = RadioButton('Ocarina of Time')
        self.mmButton = RadioButton('Majora\'s Mask')

        self.gameButtonGroup.addButton(self.ootButton, id=0)
        self.gameButtonGroup.addButton(self.mmButton, id=1)
        self.gameGroup.addCard(self.ootButton)

        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.gameGroup.addCard(spacer)

        self.gameGroup.addCard(self.mmButton)

    def _getSelectedGame(self) -> str:
        selected_id = self.gameButtonGroup.checkedId()
        return {0: 'OOT', 1: 'MM'}.get(selected_id, 'SHARED')

    def _createMetadataGroup(self):
        self.metadataGroup = CardGroup('Metadata', 14, self)

        # Cache Type
        self.bgmFanfareCard = ComboBoxCard(
            title='Bank type',
            parent=self.metadataGroup
        )
        self.bgmFanfareCard.setFixedHeight(48)
        self.bgmFanfareCard.comboBox.setFixedWidth(160)
        self.bgmFanfareCard.comboBox.addItem('BGM', userData=AudioCacheLoadType.TEMPORARY)
        self.bgmFanfareCard.comboBox.addItem('Fanfare', userData=AudioCacheLoadType.PERSISTENT)

        # Num Instruments
        self.numInstrumentsCard = SpinBoxCard(
            title='Number of instruments',
            minRange=0,
            maxRange=126,
            parent=self.metadataGroup
        )
        self.numInstrumentsCard.setFixedHeight(56)
        self.numInstrumentsCard.spinBox.setFixedWidth(160)

        # Num Drums
        self.numDrumsCard = SpinBoxCard(
            title='Number of drums',
            minRange=0,
            maxRange=128,
            parent=self.metadataGroup
        )
        self.numDrumsCard.setFixedHeight(56)
        self.numDrumsCard.spinBox.setFixedWidth(160)

        # Num Effects
        self.numEffectsCard = SpinBoxCard(
            title='Number of effects',
            minRange=0,
            maxRange=128,
            parent=self.metadataGroup
        )
        self.numEffectsCard.setFixedHeight(56)
        self.numEffectsCard.spinBox.setFixedWidth(160)

        self.metadataGroup.addCards([
            self.bgmFanfareCard,
            self.numInstrumentsCard,
            self.numDrumsCard,
            self.numEffectsCard
        ])

    def isValidName(self) -> bool:
        name = self.nameEdit.text().strip()
        return bool(name)

    def _resize_preserve(self, existingList, newSize):
        if len(existingList) > newSize:
            return existingList[:newSize]

        return existingList + [None] * (newSize - len(existingList))

    def applyChanges(self):
        if not self.isValidName():
            return False

        self.bank.name = self.nameEdit.text()
        self.bank.game = self._getSelectedGame()
        self.tableEntry.cacheLoadType = self.bgmFanfareCard.comboBox.currentData()

        numInstruments = self.numInstrumentsCard.spinBox.value()
        numDrums = self.numDrumsCard.spinBox.value()
        numEffects = self.numEffectsCard.spinBox.value()

        self.tableEntry.numInstruments = numInstruments
        self.tableEntry.numDrums = numDrums
        self.tableEntry.numEffects = numEffects

        # Resize lists while preserving objects
        self.bank.instruments = self._resize_preserve(self.bank.instruments, numInstruments)
        self.bank.drums = self._resize_preserve(self.bank.drums, numDrums)
        self.bank.effects = self._resize_preserve(self.bank.effects, numEffects)

        return True
