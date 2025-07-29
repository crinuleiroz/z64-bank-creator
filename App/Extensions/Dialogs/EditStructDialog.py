# App/Extensions/Dialogs/EditStructDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.ParameterEditForm import InstrumentParameterForm, DrumParameterForm
from App.Extensions.Forms.SampleEditForm import MultiSampleForm, SingleSampleForm
from App.Extensions.Forms.EnvelopeEditForm import EnvelopeEditForm


class EditStructDialog(MessageBoxBase):
    def __init__(self, preset, mode: str, presetType: str = '', parent=None):
        super().__init__(parent)
        self.preset = preset
        self.mode = mode
        self.presetType = presetType

        self.form = None
        self._buildLayout()

    def _buildLayout(self):
        formClass, title = self._getForm()
        if not formClass:
            return

        self.titleLabel = SubtitleLabel(title, self)
        self.form = formClass(self.preset)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.widget.setMinimumWidth(540)

        self.yesButton.setText('Apply')

    def _getForm(self):
        parameterTitle = 'Edit parameters'
        multiSample = (MultiSampleForm, 'Assign samples')
        singleSample = (SingleSampleForm, 'Assign sample')

        match self.mode:
            case 'parameters':
                return self._resolveByType({
                    'instruments': (InstrumentParameterForm, parameterTitle),
                    'drums': (DrumParameterForm, parameterTitle)
                })
            case 'samples':
                return self._resolveByType({
                    'instruments': multiSample,
                    'drums': singleSample,
                    'effects': singleSample
                })
            case 'envelopes':
                return EnvelopeEditForm, 'Assign envelope'

    def _resolveByType(self, mapping):
        return mapping.get(self.presetType, (None, None))

    def applyChanges(self):
        if self.form:
            self.form.applyChanges()