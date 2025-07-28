# App/Extensions/Forms/BankCreationForm.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup

from qfluentwidgets import ComboBox, LineEdit, RadioButton

# App/Common
from App.Common.Presets import builtinPresetStore, userPresetStore
from App.Common.Audiobank import Audiobank, TableEntry, AudioStorageMedium, AudioCacheLoadType, SampleBankId
from App.Common.Helpers import patch_combo_setCurrentIndex

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup
from App.Extensions.Widgets.ComboBoxCard import ComboBoxCard
from App.Extensions.Widgets.SpinBoxCard import SpinBoxCard


class BankCreationForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bank = None

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createGameGroup()
        self._createMetadataGroup()
        self._createDrumkitGroup()

        self.numDrumsCard.spinBox.valueChanged.connect(self._handleDrumCountChange)

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.gameGroup)
        layout.addWidget(self.metadataGroup)
        layout.addWidget(self.drumkitGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Bank Name', 14, self)
        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setPlaceholderText('Enter bank name')
        self.nameGroup.addCard(self.nameEdit)

    def _createGameGroup(self):
        self.gameGroup = CardGroup('Game', 14, self)
        self.gameButtonGroup = QButtonGroup(self)

        self.ootButton = RadioButton('Ocarina of Time')
        self.mmButton = RadioButton('Majora\'s Mask')

        self.gameButtonGroup.addButton(self.ootButton, id=0)
        self.gameButtonGroup.addButton(self.mmButton, id=1)

        self.ootButton.setChecked(True)

        self.gameGroup.addCard(self.ootButton)

        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.gameGroup.addCard(spacer)

        self.gameGroup.addCard(self.mmButton)
        self.gameButtonGroup.buttonToggled.connect(self._onGameChanged)

    def _onGameChanged(self, button, checked):
        if checked:
            self._populateDrumkitCombobox(self.drumkitCombo)

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

    def _createDrumkitGroup(self):
        self.drumkitGroup = CardGroup('Drum kit', 14, self)

        self.drumkitCombo = ComboBox()
        self.drumkitCombo.setMaxVisibleItems(8)
        self.drumkitCombo.setEnabled(False)
        self._populateDrumkitCombobox(self.drumkitCombo)
        self.drumkitCombo.setFixedHeight(32)

        self.drumkitGroup.addCard(self.drumkitCombo)

    def _populateCombobox(self, combobox, enum, *, skip_values=None, default_index=0, min_width=160):
        skip_values = skip_values or []
        combobox.clear()
        for item in enum:
            if item in skip_values:
                continue
            combobox.addItem(item.name, userData=item)
        combobox.setCurrentIndex(default_index)
        combobox.setMinimumWidth(min_width)

    def _populateDrumkitCombobox(self, comboBox):
        comboBox.clear()
        comboBox.addItem('None', userData=None)

        selected_game = self._getSelectedGame()

        for id, kit in builtinPresetStore.drumkits.items():
            if not kit:
                continue
            if kit.game in ('SHARED', selected_game):
                comboBox.addItem(kit.name, userData=kit)

        patch_combo_setCurrentIndex(comboBox)

    def _handleDrumCountChange(self, value):
        if value > 0:
            self._populateDrumkitCombobox(self.drumkitCombo)
            self.drumkitCombo.setEnabled(True)
        else:
            self.drumkitCombo.setEnabled(False)
            self.drumkitCombo.setCurrentIndex(0)

    def isValidName(self) -> bool:
        name = self.nameEdit.text().strip()
        return bool(name)

    def applyChanges(self):
        if not self.isValidName():
            return False

        numInstruments = self.numInstrumentsCard.spinBox.value()
        numDrums = self.numDrumsCard.spinBox.value()
        numEffects = self.numEffectsCard.spinBox.value()

        self.bank = Audiobank(
            name=self.nameEdit.text(),
            game=self._getSelectedGame(),
            tableEntry=TableEntry(
                storageMedium=AudioStorageMedium.CART,
                cacheLoadType=self.bgmFanfareCard.comboBox.currentData(),
                sampleBankId_1=SampleBankId.BANK_1,
                sampleBankId_2=SampleBankId.NO_BANK,
                numInstruments=numInstruments,
                numDrums=numDrums,
                numEffects=numEffects
            ),
        )

        if self.drumkitCombo.isEnabled():
            selected_kit = self.drumkitCombo.currentData()
            if selected_kit:
                self.bank.drums = selected_kit.drums[:numDrums]
        return True
