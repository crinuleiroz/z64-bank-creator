# App/Extensions/Dialogs/EditEnvelopeDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.EnvelopeEditForm import EnvelopeEditForm


class EditEnvelopeDialog(MessageBoxBase):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.form = EnvelopeEditForm(self.preset)

        self.titleLabel = SubtitleLabel('Edit envelope', self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.yesButton.setText('Apply')
        self.widget.setMinimumWidth(540)

    def applyChanges(self):
        self.form.applyChanges()