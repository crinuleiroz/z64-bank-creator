# App/Extensions/Dialogs/EditSampleDialog.py

from qfluentwidgets import MessageBoxBase, SubtitleLabel

# App/Extensions
from App.Extensions.Forms.TableEntryEditForm import TableEntryEditForm
from App.Extensions.Forms.BankListEditForm import BankListEditForm


class EditBankDialog(MessageBoxBase):
    def __init__(self, mode: str, bank = None, listType: str = '', currentList: list = None, presets=None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.bank = bank
        self.listType = listType
        self.currentList = currentList or []
        self.presets = presets or []

        self.titleLabel = SubtitleLabel(self._getTitle(), self)
        self.form = self._getForm()

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.form)
        self.yesButton.setText('Create')
        self.widget.setMinimumWidth(540)
        self.widget.setMinimumHeight(540) # Bank lists dialog is too small if not set

    def _getTitle(self):
        match self.mode:
            case 'tableEntry':
                return 'Edit table entry'
            case 'bankList':
                return {
                    'instruments': 'Assign instruments',
                    'drums': 'Assign drums',
                    'effects': 'Assign effects'
                }.get(self.listType)

    def _getForm(self):
        match self.mode:
            case 'tableEntry':
                return TableEntryEditForm(self.bank)
            case 'bankList':
                return BankListEditForm(
                    count=len(self.currentList),
                    listType=self.listType,
                    presets=self.presets,
                    currentList=self.currentList
                )

    def applyChanges(self):
        if self.form:
            self.form.applyChanges()

    def getSelection(self):
        if self.form:
            self.form.getSelection()
