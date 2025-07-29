# App/Extensions/Forms/StructEmptyForm.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QButtonGroup

from qfluentwidgets import LineEdit, RadioButton

# App/Common
from App.Common.Presets import builtinPresetStore

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup

# App/Common
from App.Common.Enums import EnvelopeOpcode
from App.Common.Structs import Instrument, Drum, Effect, Envelope


class StructEmptyForm(QWidget):
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

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.typeGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Preset name', 14, self)
        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setPlaceholderText("Enter preset name")
        self.nameGroup.addCard(self.nameEdit)

    def _createTypeGroup(self):
        self.typeGroup = CardGroup('Preset type', 14, self)
        self._createTypeButtons()

    def _createTypeButtons(self):
        self.buttonGroup = QButtonGroup(self)

        self.typeButtons = {
            'instruments' : RadioButton('Instrument'),
            'drums' : RadioButton('Drum'),
            'effects' : RadioButton('Effect'),
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
                break

    def isValidName(self) -> bool:
        name = self.nameEdit.text().strip()
        return bool(name)

    def _createInstrument(self):
        return Instrument(
            name=self.nameEdit.text().strip(),
            is_relocated=False,
            key_region_low=0,
            key_region_high=127,
            decay_index=255,
            envelope=None,
            low_sample=None,
            prim_sample=None,
            high_sample=None
        )

    def _createDrum(self):
        return Drum(
            name=self.nameEdit.text().strip(),
            decay_index=255,
            pan=64,
            is_relocated=False,
            drum_sample=None,
            envelope=None
        )

    def _createEffect(self):
        return Effect(
            name=self.nameEdit.text().strip(),
            effect_sample=None
        )

    def _createEnvelope(self):
        return Envelope(
            name=self.nameEdit.text().strip(),
            array=[1, 0, 1, 0, 1, 0, EnvelopeOpcode.HANG, 0]
        )

    def applyChanges(self) -> bool:
        if not self.isValidName():
            return False

        match self.selectedType:
            case 'instruments':
                self.preset = self._createInstrument()
            case 'drums':
                self.preset = self._createDrum()
            case 'effects':
                self.preset = self._createEffect()
            case 'envelopes':
                self.preset = self._createEnvelope()
            case _:
                return False

        return True
