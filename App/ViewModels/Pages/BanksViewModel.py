# App/ViewModels/Pages/BanksViewModel.py

from functools import partial
from pathlib import Path
import yaml

from PySide6.QtCore import Qt, QItemSelectionModel, QModelIndex
from PySide6.QtGui import QShortcut, QUndoStack, QKeySequence
from PySide6.QtWidgets import QFileDialog

from qfluentwidgets import Action, RoundMenu, MenuAnimationType, TableView, CommandBar, InfoBar
from qfluentwidgets import FluentIcon as FIF

# App/Common
from App.Common.Config import cfg
from App.Common.Presets import builtinPresetStore, userPresetStore, presetRegistry
from App.Common.Helpers import make_dot_icon, clone_bank, generate_copy_name
from App.Common.Serialization import serialize_to_yaml
from App.Common.Audiobank import Audiobank

# App/Extensions
from App.Resources.Icons.MSFluentIcons import MSFluentIcon as FICO
from App.Extensions.Components.PresetCommands import (
    CreatePresetCommand, EditBankTableEntryCommand, EditBankListCommand,
    PastePresetCommand, DeletePresetCommand
)
from App.Extensions.Dialogs.CreatePresetDialog import CreatePresetDialog
from App.Extensions.Dialogs.EditBankDialog import EditBankDialog


class BanksViewModel(object):
    #region Initialization
    def initPage(self, tableWidget: TableView, commandBar: CommandBar, parentPage):
        self.tableWidget = tableWidget
        self.commandBar = commandBar
        self.page = parentPage

        self.userPresets = userPresetStore
        self.builtinPresets = builtinPresetStore
        self.undoStack = QUndoStack()

        self.bankObject = None

        self.selectedItems = []
        self.selectedPresets: list[Audiobank] = []
        self.copiedPresets: list[Audiobank] = []
        self.editedPresets = set()

        # Menu setup
        self._setupCommandBarActions()
        self._setupNewPresetMenu()
        self._setupEditPresetMenu()
        self._setupExportPresetMenu()

        # Shortcuts
        self._setupPageShortcuts()

        # Signals
        self._connectSignals()

        # Refresh presets
        self.refresh()

    def _setupCommandBarActions(self):
        self.createBank = Action(icon=FICO.ADD, text='Create', triggered=self._showNewPresetMenu)
        self.undoAction = Action(icon=FICO.ARROW_UNDO, text='Undo (Ctrl+Z)', triggered=self.undoStack.undo)
        self.redoAction = Action(icon=FICO.ARROW_REDO, text='Redo (Ctrl+Y)', triggered=self.undoStack.redo)
        self.editAction = Action(icon=FICO.EDIT, text='Edit', triggered=self._showEditPresetMenu)
        self.exportAction = Action(icon=FICO.SHARE_IOS, text='Export', triggered=self._showExportPresetMenu)
        self.deleteAction = Action(icon=FICO.DELETE, text='Delete (Del)', triggered=self._onDeletePreset)

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

    def _setupNewPresetMenu(self):
        self.newPresetMenu = RoundMenu()
        self.emptyPresetAction = Action(icon=FICO.ADD_SQUARE, text='Empty bank preset', triggered=partial(self._onCreatePreset, 'empty'))
        self.templatePresetAction = Action(icon=FICO.COLLECTIONS, text='Bank preset from template', triggered=partial(self._onCreatePreset, 'template'))

        # These are here so they show up in the menu
        self.emptyPresetAction.setShortcut(QKeySequence('Ctrl+N'))
        self.templatePresetAction.setShortcut(QKeySequence('Ctrl+Shift+N'))

        self.newPresetMenu.addActions([
            self.emptyPresetAction,
            self.templatePresetAction
        ])

    def _setupEditPresetMenu(self):
        self.editPresetMenu = RoundMenu()

        self.editTableEntryAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit table entry', triggered=self._editTableEntryDialog)
        self.editInstrumentListAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit instrument list', triggered=self._editInstrumentListDialog)
        self.editDrumListAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit drum list', triggered=self._editDrumListDialog)
        self.editEffectListAction = Action(icon=FICO.DOCUMENT_EDIT, text='Edit effect list', triggered=self._editEffectListDialog)

        # These are here so they show up in the menu
        self.editTableEntryAction.setShortcut(QKeySequence('Ctrl+E, M'))
        self.editInstrumentListAction.setShortcut(QKeySequence('Ctrl+E, I'))
        self.editDrumListAction.setShortcut(QKeySequence('Ctrl+E, D'))
        self.editEffectListAction.setShortcut(QKeySequence('Ctrl+E, E'))

        self.editPresetMenu.addAction(self.editTableEntryAction)

        if self.bankObject and self.bankObject.tableEntry.numInstruments > 0:
            self.editPresetMenu.addAction(self.editInstrumentListAction)

        if self.bankObject and self.bankObject.tableEntry.numDrums > 0:
            self.editPresetMenu.addAction(self.editDrumListAction)

        if self.bankObject and self.bankObject.tableEntry.numEffects > 0:
            self.editPresetMenu.addAction(self.editEffectListAction)

    def _setupExportPresetMenu(self):
        self.exportPresetMenu = RoundMenu()
        self.savePresetAction = Action(icon=FICO.SAVE, text='Save to YAML', triggered=self._onExportPreset)
        self.compilePresetAction = Action(icon=FICO.CODE_BLOCK, text='Compile to binary', triggered=self._onCompilePreset)

        # These are here so they show up in the menu
        self.savePresetAction.setShortcut(QKeySequence('Ctrl+S'))
        self.compilePresetAction.setShortcut(QKeySequence('Ctrl+B'))

        self.exportPresetMenu.addActions([
            self.savePresetAction,
            self.compilePresetAction
        ])

    def _connectSignals(self):
        cfg.themeChanged.connect(self.onThemeChanged)
        self.undoStack.canUndoChanged.connect(self.undoAction.setEnabled)
        self.undoStack.canRedoChanged.connect(self.redoAction.setEnabled)

        self.tableWidget.selectionModel().selectionChanged.connect(self._onTableSelectionChanged)
        self.tableWidget.horizontalHeader().sortIndicatorChanged.connect(self._onSortChanged)
        self.tableWidget.customContextMenuRequested.connect(self._onPresetContextMenu)

    def _setupPageShortcuts(self):
        shortcut_map = {
            'Ctrl+N': partial(self._onCreatePreset, 'empty'),
            'Ctrl+Shift+N': partial(self._onCreatePreset, 'template'),
            'Ctrl+E, M': self._editTableEntryDialog,
            'Ctrl+E, I': self._editInstrumentListDialog,
            'Ctrl+E, D': self._editDrumListDialog,
            'Ctrl+E, E': self._editEffectListDialog,
            'Ctrl+C': self._onCopyPreset,
            'Ctrl+V': self._onPastePreset,
            'Ctrl+S': self._onExportPreset,
            'Ctrl+B': self._onCompilePreset,
            'Ctrl+Z': self.undoStack.undo,
            'Ctrl+Y': self.undoStack.redo,
            'Ctrl+D': self._clearPresetSelection,
            'Del': self._onDeletePreset,
        }

        for seq, func in shortcut_map.items():
            shortcut = QShortcut(QKeySequence(seq), self.page)
            shortcut.activated.connect(func)
    #endregion

    #region List Handling
    def _clearPresetSelection(self):
        self.bankObject = None
        self.selectedItem = None

        self.selectedItems = []
        self.selectedPresets = []

        self.tableWidget.clearSelection()
        self.tableWidget.setCurrentIndex(QModelIndex())

    def _onTableSelectionChanged(self):
        selectionModel = self.tableWidget.selectionModel()
        selectedIndices = selectionModel.selectedRows()

        self.selectedItems = []
        self.selectedPresets = []

        for index in selectedIndices:
            sourceIndex = self.page.tableProxy.mapToSource(index)
            preset = self.page.tableModel.presets[sourceIndex.row()]

            if preset:
                self.selectedItems.append(sourceIndex)
                self.selectedPresets.append(preset)

        self._updateCommandBarButtonState()

    def _onSortChanged(self, column: int, order: Qt.SortOrder):
        self.sortColumn = column
        self.sortOrder = order

        self._clearPresetSelection()

    def _updateCommandBarButtonState(self):
        selectedCount: int = len(self.selectedItems)
        hasSelection: bool = selectedCount > 0
        hasSingleSelection: bool = selectedCount == 1

        self.editAction.setEnabled(hasSingleSelection)

        # Compiling allows multiple selections, and does not prompt where to save, it just saves
        # to the output folder set in config
        self.exportAction.setEnabled(hasSelection)
        if self.exportAction.isEnabled():
            self.savePresetAction.setEnabled(hasSingleSelection)

        self.deleteAction.setEnabled(hasSelection)

        if hasSingleSelection:
            self.bankObject = self.selectedPresets[0]
            self._setupEditPresetMenu()

    def _loadAllPresets(self):
        self.builtinPresets.load_builtin_presets()
        self.userPresets.load_user_presets(Path(cfg.get(cfg.presetsfolder)))

    def _refreshTableWidget(self):
        presetList = list(self._getPresetList())
        presetList.sort(key=lambda p: (p.game, p.name))

        self.page.tableModel.updatePresets(presetList)
        self.page.tableWidget.clearSelection()

    def _getPresetList(self):
        return self.userPresets.banks.values()
    #endregion

    #region Preset Handling
    def _onCreatePreset(self, formType='empty', boolean=False):
        dialog = CreatePresetDialog('bank', formType, self.page)

        if dialog.exec():
            if not dialog.form.applyChanges():
                return

            newPreset = dialog.form.preset
            newPreset = presetRegistry.get_or_register(newPreset)

            cmd = CreatePresetCommand(self, newPreset)
            self.undoStack.push(cmd)
            self._clearPresetSelection()

            # Select newly created item
            row_to_select = -1
            for row, preset in enumerate(self.page.tableModel.presets):
                if preset == newPreset:
                    row_to_select = row
                    break

            if row_to_select >= 0:
                index = self.page.tableModel.index(row_to_select, 1)
                proxy_index = self.page.tableProxy.mapFromSource(index)
                self.tableWidget.selectionModel().select(
                    proxy_index,
                    QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
                )
                self.tableWidget.setCurrentIndex(proxy_index)

    def _onExportPreset(self):
        if not self.selectedItems and not self.selectedPresets:
            return

        preset = self.selectedPresets[0]
        dict = serialize_to_yaml(preset, 'banks')

        openDir = Path(cfg.presetsfolder.value) / 'banks'
        openDir.mkdir(parents=True, exist_ok=True)

        defaultFilename = f'{preset.name}.yaml'
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
            self._showSuccessTooltip(f'Exported {preset.name} YAML to: {filePath}')
        except Exception as ex:
            self._showErrorTooltip(ex)
            return

        self.userPresets.remove_preset(preset)
        self.userPresets.add_preset(preset, filePath)

    def _onCompilePreset(self):
        if not self.selectedItems and not self.selectedPresets:
            return

        successMsgs = []
        errorMsgs = []

        for preset in self.selectedPresets:
            success, error = preset.compile(cfg.get(cfg.outputfolder))

            if success:
                successMsgs.append(f'Compiled {preset.name} to: {cfg.outputfolder.value}')
            else:
                errorMsgs.append(f'Error compiling {preset.name}: {error}')

        if successMsgs:
            self._showSuccessTooltip('\n'.join(successMsgs))

        if errorMsgs:
            self._showErrorTooltip('\n'.join(errorMsgs))

    def _onDeletePreset(self):
        if not self.selectedItems and not self.selectedPresets:
            return

        cmd = DeletePresetCommand(
            self,
            self.selectedPresets,
            f'Delete {len(self.selectedPresets)} instrument banks'
        )
        self.undoStack.push(cmd)
        self._clearPresetSelection()

    def _onCopyPreset(self):
        if not self.selectedItems and not self.selectedPresets:
            return
        self.copiedPresets = self.selectedPresets

    def _onPastePreset(self):
        if not self.copiedPresets:
            return

        existingNames = {p.name for p in self.page.tableModel.presets}

        pastedPresets = []
        for presetCopy in self.copiedPresets:
            newName = generate_copy_name(presetCopy.name, existingNames)
            newPreset = clone_bank(
                original=presetCopy,
                new_name=newName,
                game=presetCopy.game
            )

            existingNames.add(newName)
            newPreset = presetRegistry.get_or_register(newPreset)
            pastedPresets.append(newPreset)

        if pastedPresets:
            cmd = PastePresetCommand(self, pastedPresets, f'Paste {len(pastedPresets)} instrument banks')
            self.undoStack.push(cmd)
    #endregion

    #region Menus
    def _onPresetContextMenu(self, pos):
        index = self.tableWidget.indexAt(pos)
        if index.isValid():
            if not self.tableWidget.selectionModel().isSelected(index):
                self.tableWidget.clearSelection()
                self.tableWidget.selectRow(index.row())

        if not self.selectedPresets:
            return

        menu = RoundMenu(parent=self.page)

        # Actions
        copyPresetAction = Action(icon=FIF.COPY, text='Copy', triggered=self._onCopyPreset)
        pastePresetAction = Action(icon=FICO.CLIPBOARD_PASTE, text='Paste', triggered=self._onPastePreset)
        exportPresetAction = Action(icon=FICO.SHARE_IOS, text='Export', triggered=self._onExportPreset)
        deletePresetAction = Action(icon=FICO.DELETE, text='Delete', triggered=self._onDeletePreset)

        # Add shortcuts so they appear in the menu's UI
        copyPresetAction.setShortcut(QKeySequence('Ctrl+C'))
        pastePresetAction.setShortcut(QKeySequence('Ctrl+V'))
        exportPresetAction.setShortcut(QKeySequence('Ctrl+S'))
        deletePresetAction.setShortcut(QKeySequence('Del'))

        # Add actions to menu
        menu.addAction(copyPresetAction)
        if self.copiedPresets:
            menu.addAction(pastePresetAction)
        if len(self.selectedPresets) == 1:
            menu.addAction(exportPresetAction)
        menu.addAction(deletePresetAction)

        globalPos = self.tableWidget.viewport().mapToGlobal(pos)
        menu.exec(globalPos, True, MenuAnimationType.DROP_DOWN)

    def _showNewPresetMenu(self):
        self._showMenuBelowAction(self.createBank, self.newPresetMenu)

    def _showEditPresetMenu(self):
        self._showMenuBelowAction(self.editAction, self.editPresetMenu)

    def _showExportPresetMenu(self):
        self._showMenuBelowAction(self.exportAction, self.exportPresetMenu)

    def _showMenuBelowAction(self, targetAction: Action, menu: RoundMenu):
        for button in self.commandBar.commandButtons:
            if button.action() is targetAction:
                pos = button.mapToGlobal(button.rect().bottomLeft())
                menu.exec(pos, True, MenuAnimationType.DROP_DOWN)
                return
    #endregion

    #region Dialogs
    def _editTableEntryDialog(self):
        self._showEditDialog()

    def _editInstrumentListDialog(self):
        self._showEditDialog('instruments')

    def _editDrumListDialog(self):
        self._showEditDialog('drums')

    def _editEffectListDialog(self):
        self._showEditDialog('effects')

    def _showEditDialog(self, listType: str | None = None):
        if len(self.selectedItems) != 1 and len(self.selectedPresets) != 1:
            return

        from copy import deepcopy

        bank = self.selectedPresets[0]

        if listType is None:
            oldEntry = deepcopy(bank.tableEntry)
            dialog = EditBankDialog(
                mode='tableEntry',
                bank=bank,
                parent=self.page
            )

            if dialog.exec():
                dialog.applyChanges()
                newEntry = deepcopy(bank.tableEntry)
                cmd = EditBankTableEntryCommand(
                    preset=bank,
                    oldEntry=oldEntry,
                    newEntry=newEntry,
                    viewModel=self
                )
                self.undoStack.push(cmd)
        else:
            currentList = {
                'instruments': bank.instruments,
                'drums': bank.drums,
                'effects': bank.effects
            }.get(listType)

            if not currentList or len(currentList) == 0:
                return

            oldList = currentList.copy()
            presets = self._getCombinedPresets(listType)

            dialog = EditBankDialog(
                mode='bankList',
                listType=listType,
                currentList=currentList,
                presets=presets,
                parent=self.page
            )

            if dialog.exec():
                newList = dialog.getSelection()
                cmd = EditBankListCommand(
                    preset=bank,
                    listType=listType,
                    oldList=oldList,
                    newList=newList,
                    viewModel=self
                )
                self.undoStack.push(cmd)

            # self._clearPresetSelection()

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
    #endregion

    #region Tooltips
    def _showSuccessTooltip(self, content):
        InfoBar.success(
            title='Success',
            content=content,
            duration=5000,
            parent=self.page
        )

    def _showErrorTooltip(self, content):
        InfoBar.error(
            title='Error',
            content=content,
            duration=-1,
            parent=self.page
        )
    #endregion

    def onThemeChanged(self):
        self._updateCommandBarButtonState()

    def refresh(self):
        self._refreshTableWidget()
