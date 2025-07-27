# App/Extensions/Dialogs/EditParameterDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.ParameterEditForm import InstrumentParameterForm, DrumParameterForm


class EditParameterDialog(MessageBoxBase):
    def __init__(self, preset, type, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.type = type

        match type:
            case 'instruments':
                self.titleLabel = SubtitleLabel('Edit instrument', self)
                self.form = InstrumentParameterForm(self.preset)
            case 'drums':
                self.titleLabel = SubtitleLabel('Edit drum', self)
                self.form = DrumParameterForm(self.preset)
            case _:
                return

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.yesButton.setText('Apply')
        self.widget.setMinimumWidth(540)

    def applyChanges(self):
        self.form.applyChanges()
