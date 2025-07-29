# App/Extensions/Forms/BankTemplateForm.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup

from qfluentwidgets import ComboBox, LineEdit, RadioButton

# App/Common
from App.Common.Presets import builtinPresetStore
from App.Common.Audiobank import Audiobank
from App.Common.Helpers import patch_combo_setCurrentIndex, clone_bank

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup


class BankTemplateForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selectedPreset: Audiobank = None
        self.bank: Audiobank = None

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createGameGroup()
        self._createPresetGroup()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.gameGroup)
        layout.addWidget(self.presetGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Preset name', 14, self)

        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setPlaceholderText("Enter preset name (optional)")

        self.nameGroup.addCard(self.nameEdit)

    def _createGameGroup(self):
        self.gameGroup = CardGroup('Game', 14, self)
        self._createGameButtons()

    def _createPresetGroup(self):
        self.presetGroup = CardGroup('Preset template', 14, self)

        self.presetSelectCombo = ComboBox(self.presetGroup)
        self.presetSelectCombo.setMaxVisibleItems(8)
        self.presetSelectCombo.currentIndexChanged.connect(self._onPresetSelected)
        self._populateBankList()

        self.presetGroup.addCard(self.presetSelectCombo)

    def _createGameButtons(self):
        self.buttonGroup = QButtonGroup(self)

        self.ootButton = RadioButton('Ocarina of Time')
        self.mmButton = RadioButton('Majora\'s Mask')

        self.buttonGroup.addButton(self.ootButton, id=0)
        self.buttonGroup.addButton(self.mmButton, id=1)

        self.ootButton.setChecked(True)
        self.buttonGroup.buttonToggled.connect(self._onGameChanged)

        self.gameGroup.addCard(self.ootButton)

        spacer = QWidget()
        spacer.setFixedHeight(8)
        self.gameGroup.addCard(spacer)

        self.gameGroup.addCard(self.mmButton)

    def _onGameChanged(self, button, checked):
        self._populatePresetList()

    def _getSelectedGame(self) -> str:
        selected_id = self.buttonGroup.checkedId()
        return {0: 'OOT', 1: 'MM'}.get(selected_id, 'SHARED')

    def _populatePresetList(self):
        self.presetSelectCombo.clear()
        selectedGame = self._getSelectedGame()

        for name, bank in builtinPresetStore.banks.items():
            if bank.game == 'SHARED' or bank.game == selectedGame:
                self.presetSelectCombo.addItem(name, userData=bank)

        patch_combo_setCurrentIndex(self.presetSelectCombo)

        if self.presetSelectCombo.count() > 0:
            self.presetSelectCombo.setCurrentIndex(0)
            self._onPresetSelected(0)

    def _onPresetSelected(self, index: int):
        self.selectedPreset = self.presetSelectCombo.currentData()

    def _cloneBank(self, original: Audiobank, new_name: str = "") -> Audiobank:
        cloned = clone_bank(
            original=original,
            new_name=new_name,
            game=self._getSelectedGame()
        )

        return cloned

    def applyChanges(self) -> bool:
        if not self.selectedPreset:
            return False

        name_override = self.nameEdit.text().strip()
        cloned_bank = self._cloneBank(self.selectedPreset, name_override)

        self.bank = cloned_bank
        return True
