# App/Extensions/Dialogs/EditSampleDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.BankEmptyForm import BankEmptyForm
from App.Extensions.Forms.BankTemplateForm import BankTemplateForm
from App.Extensions.Forms.StructEmptyForm import StructEmptyForm
from App.Extensions.Forms.StructTemplateForm import StructTemplateForm


class CreatePresetDialog(MessageBoxBase):
    def __init__(self, presetType, formType, parent=None):
        super().__init__(parent)
        self.presetType = presetType
        self.formType = formType

        self.titleLabel = SubtitleLabel(self._getTitle(), self)
        self.form = self._getForm()

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.yesButton.setText('Create')
        self.widget.setMinimumWidth(540)

    def _getTitle(self):
        match self.formType:
            case 'empty':
                return f'Create {self.presetType}'
            case 'template':
                return f'Choose template'
            case _:
                return f'New {self.presetType}'

    def _getForm(self):
        match self.presetType:
            case 'bank':
                return {
                    'empty': BankEmptyForm,
                    'template': BankTemplateForm
                }.get(self.formType, lambda: None)()
            case 'struct':
                return {
                    'empty': StructEmptyForm,
                    'template': StructTemplateForm
                }.get(self.formType, lambda: None)()
            case _:
                return

    def applyChanges(self):
        if self.form:
            self.form.applyChanges()
