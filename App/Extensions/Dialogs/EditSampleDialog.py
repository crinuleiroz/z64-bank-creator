# App/Extensions/Dialogs/EditSampleDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.SampleEditForm import MultiSampleForm, SingleSampleForm


class EditSampleDialog(MessageBoxBase):
    def __init__(self, preset, presetType, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.presetType = presetType
        self.form = None

        match presetType:
            case 'instruments':
                self.titleLabel = SubtitleLabel('Edit samples', self)
                self.form = MultiSampleForm(self.preset)
            case _:
                self.titleLabel = SubtitleLabel('Edit sample', self)
                self.form = SingleSampleForm(self.preset)

        self.viewLayout.addWidget(self.titleLabel)
        if self.form:
            self.viewLayout.addWidget(self.form)
        self.yesButton.setText('Apply')
        self.widget.setMinimumWidth(540)

    def applyChanges(self):
        self.form.applyChanges()
