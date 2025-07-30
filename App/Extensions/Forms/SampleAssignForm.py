# App/Extensions/Forms/SampleEditForm.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from qfluentwidgets import DoubleSpinBox, ComboBox

# App/Common
from App.Common.Structs import TunedSample
from App.Common.Presets import builtinPresetStore, userPresetStore
from App.Common.Helpers import populate_combo_box

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup


class MultiSampleAssignForm(QWidget):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        self.preset = preset

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self.lowSampleGroup, self.lowSampleCombo, self.lowSampleTuningSpin = createSampleGroup('Low sample', 'low_sample', self.preset, self)
        self.primSampleGroup, self.primSampleCombo, self.primSampleTuningSpin = createSampleGroup('Prim sample', 'prim_sample', self.preset, self)
        self.highSampleGroup, self.highSampleCombo, self.highSampleTuningSpin = createSampleGroup('High sample', 'high_sample', self.preset, self)

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(self.lowSampleGroup)
        layout.addWidget(self.primSampleGroup)
        layout.addWidget(self.highSampleGroup)

    def applyChanges(self):
        lowSample = self.lowSampleCombo.currentData()
        lowTuning = self.lowSampleTuningSpin.value()

        primSample = self.primSampleCombo.currentData()
        primTuning = self.primSampleTuningSpin.value()

        highSample = self.highSampleCombo.currentData()
        highTuning = self.highSampleTuningSpin.value()

        self.preset.low_sample = TunedSample(lowSample, lowTuning) if lowSample else None
        self.preset.prim_sample = TunedSample(primSample, primTuning) if primSample else None
        self.preset.high_sample = TunedSample(highSample, highTuning) if highSample else None


class SingleSampleAssignForm(QWidget):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        self.preset = preset

        if hasattr(self.preset, 'drum_sample'):
            self.attrName = 'drum_sample'
            self.label = 'Drum sample'
        elif hasattr(self.preset, 'effect_sample'):
            self.attrName = 'effect_sample'
            self.label = 'Effect sample'
        else:
            return

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self.sampleGroup, self.sampleCombo, self.tuningSpin = createSampleGroup(self.label, self.attrName, self.preset, self)

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.addWidget(self.sampleGroup)

    def applyChanges(self):
        sample = self.sampleCombo.currentData()
        tuning = self.tuningSpin.value()
        setattr(self.preset, self.attrName, TunedSample(sample=sample, tuning=tuning))


def createSampleGroup(label: str, attrName: str, preset, parent):
    sampleGroup = CardGroup(label, 14, parent)
    sampleWidget = QWidget(sampleGroup)
    sampleWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    sampleLayout = QHBoxLayout(sampleWidget)
    sampleLayout.setContentsMargins(0, 0, 0, 0)
    sampleLayout.setSpacing(8)
    sampleLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    # Sample
    sampleCombo = ComboBox()
    sampleCombo.setMaxVisibleItems(8)
    sampleCombo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    tunedSample = getattr(preset, attrName)
    sample = tunedSample.sample if tunedSample else None
    populate_combo_box(
        sampleCombo,
        builtinPresetStore.samples.values(),
        userPresetStore.samples.values(),
        target_obj=sample,
        add_none=True
    )

    # Tuning
    tuningSpin = DoubleSpinBox()
    tuningSpin.setRange(0.0, 4.0)
    tuningSpin.setSingleStep(0.01)
    tuningSpin.setValue(tunedSample.tuning if tunedSample else 0.0)
    tuningSpin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

    sampleLayout.addWidget(sampleCombo)
    sampleLayout.addWidget(tuningSpin)
    sampleWidget.setMinimumHeight(tuningSpin.sizeHint().height() + 8)

    sampleGroup.addCard(sampleWidget)

    return sampleGroup, sampleCombo, tuningSpin