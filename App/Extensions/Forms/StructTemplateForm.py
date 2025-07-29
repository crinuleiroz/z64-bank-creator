# App/Extensions/Forms/StructTemplateForm.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup

from qfluentwidgets import ComboBox, LineEdit, RadioButton

# App/Common
from App.Common.Presets import builtinPresetStore
from App.Common.Helpers import patch_combo_setCurrentIndex, clone_struct

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup


class StructTemplateForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.selectedType = 'instruments'
        self.selectedPreset = None
        self.preset = None

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createTypeGroup()
        self._createPresetGroup()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.typeGroup)
        layout.addWidget(self.presetGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Preset name', 14, self)

        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setPlaceholderText("Enter preset name (optional)")

        self.nameGroup.addCard(self.nameEdit)

    def _createTypeGroup(self):
        self.typeGroup = CardGroup('Struct type', 14, self)
        self._createTypeButtons()

    def _createPresetGroup(self):
        self.presetGroup = CardGroup('Preset template', 14, self)

        self.presetSelectCombo = ComboBox(self.presetGroup)
        self.presetSelectCombo.setMaxVisibleItems(8)
        self.presetSelectCombo.currentIndexChanged.connect(self._onPresetSelected)
        self.presetGroup.addCard(self.presetSelectCombo)

        self._populatePresetList('instruments')

    def _createTypeButtons(self):
        self.buttonGroup = QButtonGroup(self)

        self.typeButtons = {
            'instruments' : RadioButton('Instrument'),
            'drums' : RadioButton('Drum'),
            'effects' : RadioButton('Effect'),
            'samples' : RadioButton('Sample'),
            'envelopes' : RadioButton('Envelope')
        }

        for i, (key, button) in enumerate(self.typeButtons.items()):
            self.buttonGroup.addButton(button, id=i)
            self.typeGroup.addCard(button)

            if i < len(self.typeButtons) - 1:
                spacer = QWidget()
                spacer.setFixedHeight(4)
                self.typeGroup.addCard(spacer)

        self.typeButtons['instruments'].setChecked(True)
        self.buttonGroup.buttonToggled.connect(self._onTypeChanged)

    def _onTypeChanged(self, checked: bool):
        if not checked:
            return

        for key, button in self.typeButtons.items():
            if button.isChecked():
                self.selectedType = key
                self._populatePresetList(key)
                break

    def _populatePresetList(self, type: str):
        self.presetSelectCombo.clear()
        presetDict = getattr(builtinPresetStore, type, {})

        for id, preset in presetDict.items():
            self.presetSelectCombo.addItem(preset.name, userData=preset)

        count = self.presetSelectCombo.count()
        self.presetSelectCombo.setEnabled(count > 0)

        if count > 0:
            patch_combo_setCurrentIndex(self.presetSelectCombo)
            self.presetSelectCombo.setCurrentIndex(0)
            self._onPresetSelected(0)
        else:
            self.selectedPreset = None

    def _onPresetSelected(self, index: int):
        self.selectedPreset = self.presetSelectCombo.currentData()

    def applyChanges(self) -> bool:
        if not self.selectedPreset:
            return False

        name = self.nameEdit.text().strip()
        cloned = clone_struct(self.selectedPreset, name)

        self.preset = cloned
        return True
