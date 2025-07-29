# App/Extensions/Components/BankCommands.py

from PySide6.QtCore import Qt
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import QListWidgetItem


#region Create Bank
class CreateBankCommand(QUndoCommand):
    def __init__(self, viewModel, bank, description='Create bank'):
        super().__init__(description)
        self.viewModel = viewModel
        self.bank = bank
        self.item = None

    def undo(self):
        if not self.item:
            return

        row = self.viewModel.listView.row(self.item)
        self.viewModel.listView.takeItem(row)

    def redo(self):
        if not self.item:
            self.item = QListWidgetItem(self.bank.name)
            self.item.setData(Qt.ItemDataRole.UserRole, self.bank)

        self.viewModel.listView.addItem(self.item)
        self.viewModel.listView.setCurrentItem(self.item)
#endregion


#region Edit Table Entry
class EditTableEntryCommand(QUndoCommand):
    def __init__(self, bank, oldEntry, newEntry, viewModel, description='Edit table entry'):
        super().__init__(description)
        self.bank = bank
        self.oldEntry = oldEntry
        self.newEntry = newEntry
        self.viewModel = viewModel

    def undo(self):
        self.bank.tableEntry = self.oldEntry
        self.viewModel._refreshListView()

    def redo(self):
        self.bank.tableEntry = self.newEntry
        self.viewModel._refreshListView()
#endregion


#region Edit Bank List
class EditBankListCommand(QUndoCommand):
    def __init__(self, viewModel, bank, listType, oldList, newList):
        super().__init__(f'Edit {listType}')
        self.bank = bank
        self.listType = listType
        self.oldList = oldList
        self.newList = newList
        self.viewModel = viewModel

    def undo(self):
        setattr(self.bank, self.listType, self.oldList)
        self.viewModel._refreshListView()

    def redo(self):
        setattr(self.bank, self.listType, self.newList)
        self.viewModel._refreshListView()
#endregion


#region Delete Bank
class DeleteBankCommand(QUndoCommand):
    def __init__(self, viewModel, item, description='Delete bank'):
        super().__init__(description)
        self.viewModel = viewModel
        self.item = item
        self.bank = item.data(Qt.ItemDataRole.UserRole)
        self.row = self.viewModel.listView.row(item)

    def undo(self):
        self.viewModel.listView.insertItem(self.row, self.item)
        self.viewModel.listView.setCurrentItem(self.item)

    def redo(self):
        self.viewModel.listView.takeItem(self.row)
#endregion
