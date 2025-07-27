# App/Extensions/Dialogs/EditSampleDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.PresetEmptyForm import PresetEmptyForm
from App.Extensions.Forms.PresetTemplateForm import PresetTemplateForm


class CreatePresetDialog(MessageBoxBase):
    def __init__(self, formType, parent=None):
        super().__init__(parent)
        self.formType = formType

        match formType:
            case 'empty':
                self.titleLabel = SubtitleLabel('Create preset', self)
                self.form = PresetEmptyForm()
            case 'template':
                self.titleLabel = SubtitleLabel('Choose template', self)
                self.form = PresetTemplateForm()
            case _:
                return

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.yesButton.setText('Create')
        self.widget.setMinimumWidth(540)

    def applyChanges(self):
        self.form.applyChanges()
