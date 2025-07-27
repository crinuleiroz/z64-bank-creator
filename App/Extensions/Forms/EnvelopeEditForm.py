# App/Extensions/Forms/EnvelopeEditForm.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import ComboBox, ToolTipFilter, ToolTipPosition

# App/Common
from App.Common.Presets import builtinPresetStore, userPresetStore
from App.Common.Helpers import populate_combo_box

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup


class EnvelopeEditForm(QWidget):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.userPresets = userPresetStore
        self.builtinPresets = builtinPresetStore

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createEnvelopeGroup()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.envelopeGroup)

    def _createEnvelopeGroup(self):
        self.envelopeGroup = CardGroup('Envelope', 14, self)

        # Envelope
        self.envelopeCombo = ComboBox(self.envelopeGroup)
        self.envelopeCombo.setMaxVisibleItems(8)
        self.envelopeCombo.installEventFilter(ToolTipFilter(self.envelopeCombo, showDelay=300, position=ToolTipPosition.TOP))
        self.envelopeCombo.currentIndexChanged.connect(self._updateEnvelopeTooltip)

        self._updateEnvelopeTooltip(self.envelopeCombo.currentIndex())
        self._populateEnvelopeCombo()

        self.envelopeGroup.addCard(self.envelopeCombo)

    def _populateEnvelopeCombo(self):
        populate_combo_box(
            self.envelopeCombo,
            self.builtinPresets.envelopes.values(),
            self.userPresets.envelopes.values(),
            target_obj=self.preset.envelope,
            add_none=True
        )

    def _updateEnvelopeTooltip(self, index: int):
        env = self.envelopeCombo.itemData(index)
        if env and hasattr(env, 'array'):
            try:
                tooltipText = ', '.join(str(item) for item in env.array)
            except Exception as e:
                tooltipText = f'Error reading array: {e}'
        else:
            tooltipText = 'No envelope selected or no array available.'

        self.envelopeCombo.setToolTip(tooltipText)

    def applyChanges(self):
        envelopeObject = self.envelopeCombo.currentData()
        self.preset.envelope = envelopeObject if envelopeObject else None
