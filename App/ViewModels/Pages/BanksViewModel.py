# App/ViewModels/Pages/BanksViewModel.py

from functools import partial
from pathlib import Path
import yaml

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QUndoStack, QUndoCommand, QKeySequence
from PySide6.QtWidgets import QWidget, QListWidgetItem, QFileDialog

from qfluentwidgets import (
    SubtitleLabel, Action, MessageBoxBase, RoundMenu, MenuAnimationType,
    ListWidget, CommandBar, InfoBar
)
from qfluentwidgets import FluentIcon as FIF

# App/Common
from App.Common.Config import cfg
from App.Common.Presets import builtinPresetStore, userPresetStore, presetRegistry
from App.Common.Helpers import make_dot_icon, clone_bank, generate_copy_name
from App.Common.Serialization import serialize_to_yaml
from App.Common.Audiobank import Audiobank

# App/Extensions
from App.Extensions.Components.MSFluentIcons import MSFluentIcon as FICO
from App.Extensions.Forms.BankCreationForm import BankCreationForm
from App.Extensions.Forms.BankTemplateForm import BankTemplateForm
from App.Extensions.Forms.TableEntryEditForm import TableEntryEditForm
from App.Extensions.Dialogs.BankListEditorDialog import BankListEditorDialog

#region Commands
# Need to move to components
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

#region Dialogs
# Will refactor into dialogs and forms later
class EditBankMessageBox(MessageBoxBase):
    def __init__(self, parent=None, bank=None, formType='metadata'):
        super().__init__(parent)
        self.bank = bank
        self.formType = formType

        titleLabel = None
        match formType:
            case 'empty':
                titleLabel = SubtitleLabel(f'Create bank', self)
            case 'template':
                titleLabel = SubtitleLabel(f'Choose template', self)
            case 'metadata':
                titleLabel = SubtitleLabel('Edit table entry', self)
            case _:
                titleLabel = SubtitleLabel(f'Edit {self.formType.title()}', self)

        self.form = self._createForm()

        self.viewLayout.addWidget(titleLabel)
        if self.form:
            self.viewLayout.addWidget(self.form)

        self.widget.setFixedWidth(550)

    def applyChanges(self):
        if self.form:
            self.form.applyChanges()

    def _createForm(self) -> QWidget | None:
        match self.formType.lower():
            case 'empty':
                self.yesButton.setText('Create bank')
                self.cancelButton.setText('Cancel')
                return BankCreationForm()
            case 'template':
                self.yesButton.setText('Create bank')
                self.cancelButton.setText('Cancel')
                return BankTemplateForm()
            case 'metadata':
                self.yesButton.setText('Apply changes')
                self.cancelButton.setText('Cancel')
                return TableEntryEditForm(self.bank)
            case _:
                return None
#endregion


class BanksViewModel(object):
    #region Initialization
    def initPage(self, listView: ListWidget, commandBar: CommandBar, parentPage):
        self.listView = listView
        self.commandBar = commandBar
        self.page = parentPage

        self.userPresets = userPresetStore
        self.builtinPresets = builtinPresetStore
        self.undoStack = QUndoStack()

        self.selectedItem = None
        self.bankObject = None
        self.copiedBank = None

        # Menu setup
        self._setupCommandBarActions()
        self._setupNewBankMenu()
        self._setupEditBankMenu()
        self._setupExportBankMenu()

        # Shortcuts
        self._setupPageShortcuts()

        # Signals
        self._connectSignals()

        # Load user banks and refresh list
        # self._loadAllBanks()
        # self._refreshListView()

    def _setupCommandBarActions(self):
        self.createBank = Action(icon=FICO.ADD, text='Add', triggered=self._showNewBankMenu)
        self.undoAction = Action(icon=FICO.ARROW_UNDO, text='Undo (Ctrl+Z)', triggered=self.undoStack.undo)
        self.redoAction = Action(icon=FICO.ARROW_REDO, text='Redo (Ctrl+Y)', triggered=self.undoStack.redo)
        self.editAction = Action(icon=FICO.EDIT, text='Edit', triggered=self._showEditBankMenu)
        self.exportAction = Action(icon=FICO.SHARE_IOS, text='Export', triggered=self._showExportBankMenu)
        self.deleteAction = Action(icon=FICO.DELETE, text='Delete (Del)', triggered=self._onDeleteBank)

        # Set shortcuts (disabled to avoid ambiguous overload)
        # self.undoAction.setShortcut(QKeySequence('Ctrl+Z'))
        # self.redoAction.setShortcut(QKeySequence('Ctrl+Y'))
        # self.deleteAction.setShortcut(QKeySequence('Del'))

        # Set intial button states
        self.undoAction.setEnabled(self.undoStack.canUndo())
        self.redoAction.setEnabled(self.undoStack.canRedo())
        self.editAction.setEnabled(False)
        self.exportAction.setEnabled(False)
        self.deleteAction.setEnabled(False)

        # Add actions to command bar
        createBankButton = self.commandBar.addAction(self.createBank)
        self.commandBar.addSeparator()
        self.commandBar.addActions([
            self.undoAction,
            self.redoAction,
            self.editAction,
            self.exportAction,
            self.deleteAction
        ])
        createBankButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

    def _setupNewBankMenu(self):
        self.newBankMenu = RoundMenu()
        self.emptyBankAction = Action(icon=FICO.ADD_SQUARE, text='Empty bank', triggered=partial(self._onAddBank, 'empty'))
        self.templateBankAction = Action(icon=FICO.COLLECTIONS, text='Template bank', triggered=partial(self._onAddBank, 'template'))

        # These are here so they show up in the menu
        self.emptyBankAction.setShortcut(QKeySequence('Ctrl+N'))
        self.templateBankAction.setShortcut(QKeySequence('Ctrl+Shift+N'))

        self.newBankMenu.addActions([
            self.emptyBankAction,
            self.templateBankAction
        ])

    def _setupEditBankMenu(self):
        self.editBankMenu = RoundMenu()
        self.editMetadataAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit metadata', triggered=self._onEditMetadata)
        self.editInstrumentsAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit instruments', triggered=self._onEditInstruments)
        self.editDrumsAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit drums', triggered=self._onEditDrums)
        self.editEffectsAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit effects', triggered=self._onEditEffects)

        # These are here so they show up in the menu
        self.editMetadataAction.setShortcut(QKeySequence('Ctrl+E, M'))
        self.editInstrumentsAction.setShortcut(QKeySequence('Ctrl+E, I'))
        self.editDrumsAction.setShortcut(QKeySequence('Ctrl+E, D'))
        self.editEffectsAction.setShortcut(QKeySequence('Ctrl+E, E'))

        self.editBankMenu.addAction(self.editMetadataAction)

        if self.bankObject and self.bankObject.tableEntry.numInstruments > 0:
            self.editBankMenu.addAction(self.editInstrumentsAction)

        if self.bankObject and self.bankObject.tableEntry.numDrums > 0:
            self.editBankMenu.addAction(self.editDrumsAction)

        if self.bankObject and self.bankObject.tableEntry.numEffects > 0:
            self.editBankMenu.addAction(self.editEffectsAction)

    def _setupExportBankMenu(self):
        self.exportBankMenu = RoundMenu()
        self.saveBankAction = Action(icon=FICO.SAVE, text='Save to YAML', triggered=self._onExportBank)
        self.compileBankAction = Action(icon=FICO.CODE_BLOCK, text='Compile to binary', triggered=self._onCompileBank)

        # These are here so they show up in the menu
        self.saveBankAction.setShortcut(QKeySequence('Ctrl+S'))
        self.compileBankAction.setShortcut(QKeySequence('Ctrl+B'))

        self.exportBankMenu.addActions([
            self.saveBankAction,
            self.compileBankAction
        ])

    def _connectSignals(self):
        cfg.themeChanged.connect(self.onThemeChanged)
        self.undoStack.canUndoChanged.connect(self.undoAction.setEnabled)
        self.undoStack.canRedoChanged.connect(self.redoAction.setEnabled)

        self.listView.currentItemChanged.connect(self._onItemSelected)
        self.listView.customContextMenuRequested.connect(self._onListContextMenu)

    def _setupPageShortcuts(self):
        shortcut_map = {
            'Ctrl+N': partial(self._onAddBank, 'empty'),
            'Ctrl+Shift+N': partial(self._onAddBank, 'template'),
            'Ctrl+E, M': self._onEditMetadata,
            'Ctrl+E, I': self._onEditInstruments,
            'Ctrl+E, D': self._onEditDrums,
            'Ctrl+E, E': self._onEditEffects,
            'Ctrl+C': self._onCopyBank,
            'Ctrl+V': self._onPasteBank,
            'Ctrl+S': self._onExportBank,
            'Ctrl+B': self._onCompileBank,
            'Ctrl+Z': self.undoStack.undo,
            'Ctrl+Y': self.undoStack.redo,
            'Ctrl+D': self._clearListSelection,
            'Del': self._onDeleteBank,
        }

        for seq, func in shortcut_map.items():
            shortcut = QShortcut(QKeySequence(seq), self.page)
            shortcut.activated.connect(func)
    #endregion

    #region List Handling
    def _clearListSelection(self):
        self.bankObject = None
        self.selectedItem = None

        self.listView.clearSelection()
        self.listView.setCurrentItem(None)
        self.listView.clearFocus()

    def _onItemSelected(self, current, previous):
        if current is None:
            self.selectedItem = None
            self.preset_obj = None
            self.editAction.setEnabled(False)
            self.exportAction.setEnabled(False)
            self.deleteAction.setEnabled(False)
            return

        self.selectedItem = current
        hasSelection = current is not None

        self.editAction.setEnabled(hasSelection)
        self.exportAction.setEnabled(hasSelection)
        self.deleteAction.setEnabled(hasSelection)

        if hasSelection:
            self.bankObject = current.data(Qt.ItemDataRole.UserRole)
            self._setupEditBankMenu()

    def _loadAllBanks(self):
        # Not implemented
        return

    def _refreshListView(self):
        # Not implemented
        return
    #endregion

    #region Bank Handling
    def _onAddBank(self, formType='empty', boolean=False):
        dialog = EditBankMessageBox(parent=self.page, bank=None, formType=formType)

        if dialog.exec():
            if not dialog.form.applyChanges():
                return

            new_bank = dialog.form.bank
            new_bank = presetRegistry.get_or_register(new_bank)

            cmd = CreateBankCommand(self, new_bank)
            self.undoStack.push(cmd)

    def _onEditMetadata(self):
        if not self.selectedItem:
            return
        self._editTableEntry()

    def _onEditInstruments(self):
        if not self.selectedItem:
            return
        self._editBankList('instruments')

    def _onEditDrums(self):
        if not self.selectedItem:
            return
        self._editBankList('drums')

    def _onEditEffects(self):
        if not self.selectedItem:
            return
        self._editBankList('effects')

    def _editTableEntry(self):
        from copy import deepcopy
        if not self.selectedItem:
            return

        bank = self.selectedItem.data(Qt.ItemDataRole.UserRole)
        oldEntry = deepcopy(bank.tableEntry)

        dialog = EditBankMessageBox(parent=self.page, bank=bank, formType='metadata')

        if dialog.exec():
            dialog.applyChanges()
            newEntry = deepcopy(bank.tableEntry)
            cmd = EditTableEntryCommand(
                bank=bank,
                oldEntry=oldEntry,
                newEntry=newEntry,
                viewModel=self
            )
            self.undoStack.push(cmd)
            self._clearListSelection()
        else:
            return

    def _editBankList(self, listType: str):
        if not self.selectedItem:
            return

        bank = self.selectedItem.data(Qt.ItemDataRole.UserRole)

        match listType.lower():
            case 'instruments':
                currentList = bank.instruments
                presets = self.userPresets.instruments
            case 'drums':
                currentList = bank.drums
                presets = self.userPresets.drums
            case 'effects':
                currentList = bank.effects
                presets = self.userPresets.effects
            case _:
                return

        count = len(currentList)
        if count <= 0:
            return

        presets = self._getCombinedPresets(listType)

        dialog = BankListEditorDialog(
            title=f'Edit {listType.title()}',
            count=count,
            presets=presets,
            presetType=listType,
            existingList=currentList,
            parent=self.page
        )

        for cb, item in zip(dialog.comboBoxes, currentList):
            index = cb.findData(item)
            if index != -1:
                cb.setCurrentIndex(index)

        if dialog.exec():
            updatedList = dialog.get_selection()

            oldList = currentList.copy()
            cmd = EditBankListCommand(
                bank=bank,
                listType=listType,
                oldList=oldList,
                newList=updatedList,
                viewModel=self
            )
            self.undoStack.push(cmd)

    def _getCombinedPresets(self, listType: str):
        from App.Common.Addresses import AUDIO_SAMPLE_ADDRESSES

        SAMPLE_FIELDS = {
            'drums': ['drum_sample'],
            'effects': ['effect_sample'],
            'instruments': ['low_sample', 'prim_sample', 'high_sample']
        }

        def has_valid_address(preset, gameId: str) -> bool:
            sample_fields = SAMPLE_FIELDS.get(listType, [])
            for field in sample_fields:
                sample_obj = getattr(preset, field, None)
                if not sample_obj or not sample_obj.sample:
                    continue
                sample_name = sample_obj.sample.name
                sample_entry = AUDIO_SAMPLE_ADDRESSES.get(sample_name.upper())
                if not sample_entry or sample_entry.get(gameId, -1) == -1:
                    return False
            return True # All samples valid

        builtin_dict = getattr(self.builtinPresets, listType, {})
        user_dict = getattr(self.userPresets, listType, {})

        # Convert builtin dict values to list
        gameId = self.bankObject.game if self.bankObject else 'OOT'
        builtin_list = [
            p for p in builtin_dict.values()
            if has_valid_address(p, gameId) # Ensure only objects for the bank's game are added
        ]
        user_list = list(user_dict.values())

        # Combine builtin presets with user-defined presets
        # Duplicates are allowed for user-defined presets, but builtin presets do not have duplicates
        builtin_names = {p.name for p in builtin_list}

        return builtin_list + [p for p in user_list if p.name not in builtin_names]

    def _onExportBank(self):
        if not self.selectedItem:
            return

        bank = self.selectedItem.data(Qt.ItemDataRole.UserRole)
        dict = serialize_to_yaml(bank, 'banks')

        openDir = Path(cfg.presetsfolder.value) / 'banks'
        openDir.mkdir(parents=True, exist_ok=True)

        defaultFilename = f'{bank.name}.yaml'
        defaultFilePath = str(openDir / defaultFilename)

        filePath, _ = QFileDialog.getSaveFileName(
            self.page,
            'Export Bank as YAML',
            defaultFilePath,
            'YAML Files (*.yaml *.yml)'
        )

        if not filePath:
            return

        try:
            with open(filePath, 'w', encoding='utf-8') as f:
                yaml.safe_dump(dict, f, sort_keys=False, allow_unicode=True)
            self._showExportSuccess(filePath)
        except Exception as ex:
            self._showExportFailure(ex)
            return

        self.userPresets.remove_preset(bank)
        self.userPresets.add_preset(bank, filePath)

    def _onCompileBank(self):
        if not self.selectedItem and not self.bankObject:
            return

        success, error = self.bankObject.compile(cfg.get(cfg.outputfolder))
        if success:
            self._showCompileSuccess()
        else:
            self._showCompileFailure(error)

    def _onDeleteBank(self):
        if not self.selectedItem:
            return

        item = self.selectedItem
        cmd = DeleteBankCommand(self, item)
        self.undoStack.push(cmd)

        self._clearListSelection()

    def _onCopyBank(self):
        if not self.selectedItem:
            return
        self.copiedBank: Audiobank = self.selectedItem.data(Qt.ItemDataRole.UserRole)

    def _onPasteBank(self):
        if not self.copiedBank:
            return

        existingNames = {
            self.listView.item(i).text()
            for i in range(self.listView.count())
        }

        newName = generate_copy_name(self.copiedBank.name, existingNames)

        newBank = clone_bank(
            original=self.copiedBank,
            new_name=newName,
            game=self.copiedBank.game
        )
        newBank = presetRegistry.get_or_register(newBank)

        cmd = CreateBankCommand(self, newBank)
        self.undoStack.push(cmd)
    #endregion

    #region Menus
    def _onListContextMenu(self, pos):
        item = self.listView.itemAt(pos)
        if item:
            self.listView.setCurrentItem(item)

        if not self.selectedItem:
            return

        bank = self.selectedItem.data(Qt.ItemDataRole.UserRole)
        menu = RoundMenu(parent=self.page)

        # Actions
        copyBankAction = Action(icon=FIF.COPY, text='Copy', triggered=self._onCopyBank)
        pasteBankAction = Action(icon=FICO.CLIPBOARD_PASTE, text='Paste', triggered=self._onPasteBank)
        exportBankAction = Action(icon=FICO.SHARE_IOS, text='Export', triggered=self._onExportBank)
        deleteBankAction = Action(icon=FIF.DELETE, text='Delete', triggered=self._onDeleteBank)

        # Shortcuts
        # These are here so they show up in the menu
        copyBankAction.setShortcut(QKeySequence('Ctrl+C'))
        pasteBankAction.setShortcut(QKeySequence('Ctrl+V'))
        exportBankAction.setShortcut(QKeySequence('Ctrl+S'))
        deleteBankAction.setShortcut(QKeySequence('Del'))

        menu.addActions([copyBankAction, pasteBankAction, exportBankAction, deleteBankAction])

        globalPos = self.listView.mapToGlobal(pos)
        menu.exec(globalPos, True, MenuAnimationType.DROP_DOWN)

    def _showNewBankMenu(self):
        self._showMenuBelowAction(self.createBank, self.newBankMenu)

    def _showEditBankMenu(self):
        self._showMenuBelowAction(self.editAction, self.editBankMenu)

    def _showExportBankMenu(self):
        self._showMenuBelowAction(self.exportAction, self.exportBankMenu)

    def _showMenuBelowAction(self, targetAction: Action, menu: RoundMenu):
        for button in self.commandBar.commandButtons:
            if button.action() is targetAction:
                pos = button.mapToGlobal(button.rect().bottomLeft())
                menu.exec(pos, True, MenuAnimationType.DROP_DOWN)
                return
    #endregion

    #region Tooltips
    def _showExportSuccess(self, filePath):
        InfoBar.success(
            title='Success',
            content=f'YAML file has been saved to the following folder: \n{filePath}',
            duration=5000,
            parent=self.page
        )

    def _showExportFailure(self, error):
        InfoBar.error(
            title='Error',
            content=f'YAML file could not be saved: \n{error}',
            duration=-1,
            parent=self.page
        )

    def _showCompileSuccess(self):
        InfoBar.success(
            title='Success',
            content=f'The instrument bank has been compiled to the output folder: \n{cfg.outputfolder.value}',
            duration=5000,
            parent=self.page
        )

    def _showCompileFailure(self, error):
        InfoBar.error(
            title='Error',
            content=f'Instrument bank could not be compiled: \n{error}',
            duration=-1,
            parent=self.page
        )
    #endregion

    def onThemeChanged(self):
        hasSelection = self.selectedItem is not None
        self.editAction.setEnabled(hasSelection)
        self.exportAction.setEnabled(hasSelection)
        self.deleteAction.setEnabled(hasSelection)
