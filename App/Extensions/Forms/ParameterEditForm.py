# App/Extensions/Forms/ParameterEditForm.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import LineEdit

# App/Common
from App.Common.Presets import builtinPresetStore, userPresetStore

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup
from App.Extensions.Widgets.SwitchButtonCard import SwitchButtonCard
from App.Extensions.Widgets.SpinBoxCard import SpinBoxCard


class InstrumentParameterForm(QWidget):
    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.userPresets = userPresetStore
        self.builtinPresets = builtinPresetStore

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createParameterGroup()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.parameterGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Instrument name', 14, self)

        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setText(self.instrument.name)

        self.nameGroup.addCard(self.nameEdit)

    def _createParameterGroup(self):
        self.parameterGroup = CardGroup('Parameters', 14, self)

        # Relocated
        self.isRelocatedCard = SwitchButtonCard(
            title='Relocated',
            onText='',
            offText='',
            parent=self.parameterGroup
        )
        self.isRelocatedCard.setFixedHeight(48)
        self.isRelocatedCard.setChecked(self.instrument.is_relocated)

        # Key Region Low
        self.keyLowCard = SpinBoxCard(
            title='Key region low',
            minRange=0,
            maxRange=127,
            parent=self.parameterGroup
        )
        self.keyLowCard.spinBox.setValue(self.instrument.key_region_low)
        self.keyLowCard.setFixedHeight(56)

        # Key Region High
        self.keyHighCard = SpinBoxCard(
            title='Key region high',
            minRange=0,
            maxRange=127,
            parent=self.parameterGroup
        )
        self.keyHighCard.spinBox.setValue(self.instrument.key_region_high)
        self.keyHighCard.setFixedHeight(56)

        # Decay Index
        self.decayIndexCard = SpinBoxCard(
            title='Decay index',
            minRange=0,
            maxRange=255,
            parent=self.parameterGroup
        )
        self.decayIndexCard.spinBox.setValue(self.instrument.decay_index)
        self.decayIndexCard.setFixedHeight(56)

        self.parameterGroup.addCards([
            self.isRelocatedCard,
            self.keyLowCard,
            self.keyHighCard,
            self.decayIndexCard
        ])

    def applyChanges(self):
        self.instrument.name = self.nameEdit.text()
        self.instrument.is_relocated = self.isRelocatedCard.switchButton.isChecked()
        self.instrument.key_region_low = self.keyLowCard.spinBox.value()
        self.instrument.key_region_high = self.keyHighCard.spinBox.value()
        self.instrument.decay_index = self.decayIndexCard.spinBox.value()


class DrumParameterForm(QWidget):
    def __init__(self, drum, parent=None):
        super().__init__(parent)
        self.drum = drum
        self.userPresets = userPresetStore
        self.builtinPresets = builtinPresetStore

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createParameterGroup()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.parameterGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Drum name', 14, self)

        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setText(self.drum.name)

        self.nameGroup.addCard(self.nameEdit)

    def _createParameterGroup(self):
        self.parameterGroup = CardGroup('Parameters', 14, self)

        # Decay Index
        self.decayIndexCard = SpinBoxCard(
            title='Decay index',
            minRange=0,
            maxRange=255,
            parent=self.parameterGroup
        )
        self.decayIndexCard.spinBox.setValue(self.drum.decay_index)
        self.decayIndexCard.setFixedHeight(56)

        # Pan
        self.panCard = SpinBoxCard(
            title='Pan',
            minRange=0,
            maxRange=255,
            parent=self.parameterGroup
        )
        self.panCard.spinBox.setValue(self.drum.pan)
        self.panCard.setFixedHeight(56)

        # Relocated
        self.isRelocatedCard = SwitchButtonCard(
            title='Relocated',
            onText='',
            offText='',
            parent=self.parameterGroup
        )
        self.isRelocatedCard.setFixedHeight(48)
        self.isRelocatedCard.setChecked(self.drum.is_relocated)

        self.parameterGroup.addCards([
            self.decayIndexCard,
            self.panCard,
            self.isRelocatedCard
        ])

    def applyChanges(self):
        self.drum.name = self.nameEdit.text()
        self.drum.is_relocated = self.isRelocatedCard.switchButton.isChecked()
        self.drum.pan = self.panCard.spinBox.value()
        self.drum.decay_index = self.decayIndexCard.spinBox.value()
