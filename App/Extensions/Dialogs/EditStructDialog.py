# App/Extensions/Dialogs/EditStructDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.ParameterEditForm import InstrumentParameterForm, DrumParameterForm
from App.Extensions.Forms.SampleAssignForm import MultiSampleAssignForm, SingleSampleAssignForm
from App.Extensions.Forms.EnvelopeAssignForm import EnvelopeAssignForm
from App.Extensions.Forms.EnvelopeArrayEditForm import EnvelopeArrayEditForm


class EditStructDialog(MessageBoxBase):
    def __init__(self, preset, mode: str, presetType: str = '', parent=None):
        super().__init__(parent)
        self.preset = preset
        self.mode = mode
        self.presetType = presetType

        self.form = None
        self._initLayout()

    def _initLayout(self):
        formClass, title = self._getForm()
        if not formClass:
            return

        self.titleLabel = SubtitleLabel(title, self)
        self.form = formClass(self.preset)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.widget.setMinimumWidth(540)
        self.widget.setMinimumHeight(540)

        self.yesButton.setText('Apply')

    def _getForm(self):
        multiSample = (MultiSampleAssignForm, 'Assign samples')
        singleSample = (SingleSampleAssignForm, 'Assign sample')

        match self.mode:
            case 'parameters':
                return self._resolveByType({
                    'instruments': (InstrumentParameterForm, 'Edit instrument parameters'),
                    'drums': (DrumParameterForm, 'Edit drum parameters'),
                    'envelopes': (EnvelopeArrayEditForm, 'Edit envelope')
                })
            case 'samples':
                return self._resolveByType({
                    'instruments': multiSample,
                    'drums': singleSample,
                    'effects': singleSample
                })
            case 'envelopes':
                return EnvelopeAssignForm, 'Assign envelope'

    def _resolveByType(self, mapping):
        return mapping.get(self.presetType, (None, None))

    def applyChanges(self):
        if self.form:
            self.form.applyChanges()