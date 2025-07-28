# App/ViewModels/Pages/PresetsViewModel.py

import yaml
from collections import defaultdict
from pathlib import Path
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QUndoStack, QUndoCommand, QKeySequence
from PySide6.QtWidgets import QWidget, QListWidgetItem, QFileDialog

from qfluentwidgets import Action, RoundMenu, MenuAnimationType, ListWidget, CommandBar, InfoBar, SegmentedWidget
from qfluentwidgets import FluentIcon as FIF

# App/Common
from App.Common.Config import cfg
from App.Common.Presets import builtinPresetStore, userPresetStore, presetRegistry
from App.Common.Helpers import make_dot_icon, apply_group_box_style, generate_copy_name, clone_preset
from App.Common.Serialization import serialize_to_yaml
from App.Common.Structs import Instrument, Drum, Effect, TunedSample, Sample, Envelope

# App/Extensions
from App.Extensions.Components.MSFluentIcons import MSFluentIcon as FICO
from App.Extensions.Dialogs.CreatePresetDialog import CreatePresetDialog
from App.Extensions.Dialogs.EditParameterDialog import EditParameterDialog
from App.Extensions.Dialogs.EditSampleDialog import EditSampleDialog
from App.Extensions.Dialogs.EditEnvelopeDialog import EditEnvelopeDialog


#region Commands
# Need to move to components
class CreatePresetCommand(QUndoCommand):
    def __init__(self, viewModel, obj, description='Create structure preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.obj = obj
        self.item = None
        self.presetType = viewModel.currentPresetType

    def undo(self):
        self.viewModel.userPresets.remove_preset(self.obj)
        self.viewModel._refreshListView()

    def redo(self):
        self.viewModel.userPresets.add_preset(self.obj)
        self.viewModel._refreshListView()


class EditPresetCommand(QUndoCommand):
    def __init__(self, viewModel, originalPreset, editedPreset, description='Edit structure preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.originalPreset = originalPreset
        self.editedPreset = editedPreset
        self.item = None

    def undo(self):
        self.viewModel.userPresets.replace_preset(self.editedPreset, self.originalPreset)
        self.viewModel._refreshListView()
        self.viewModel._clearListSelection()

    def redo(self):
        self.viewModel.userPresets.replace_preset(self.originalPreset, self.editedPreset)
        self.viewModel._refreshListView()
        self.viewModel._clearListSelection()
#endregion


class PresetsViewModel(object):
    #region Initialization
    def initPage(self, listView: ListWidget, commandBar: CommandBar, pivot: SegmentedWidget, parentPage):
        self.listView = listView
        self.commandBar = commandBar
        self.pivot = pivot
        self.page = parentPage

        self.userPresets = userPresetStore
        self.builtinPresets = builtinPresetStore
        self.undoStack = QUndoStack()

        self.selectedItem = None
        self.presetObject = None
        self.copiedPreset: Instrument | Drum | Effect | Sample | Envelope = None
        self.currentPresetType = 'instruments'
        self.editedPresets = set()

        # Menu setup
        self._setupCommandBarActions()
        self._setupPivotActions()
        self._setupNewPresetMenu()
        self._setupEditPresetMenu()

        # Shortcuts
        self._setupPageShortcuts()

        # Signals
        self._connectSignals()

        # Load user presets and refresh list
        self._loadAllPresets()
        self._refreshListView()

    def _setupCommandBarActions(self):
        self.createPreset = Action(icon=FICO.ADD, text='Add', triggered=self._showNewPresetMenu)
        self.undoAction = Action(icon=FICO.ARROW_UNDO, text='Undo (Ctrl+Z)', triggered=self.undoStack.undo)
        self.redoAction = Action(icon=FICO.ARROW_REDO, text='Redo (Ctrl+Y)', triggered=self.undoStack.redo)
        self.editAction = Action(icon=FICO.EDIT, text='Edit', triggered=self._showEditPresetMenu)
        self.exportAction = Action(icon=FICO.SHARE_IOS, text='Export (Ctrl+S)', triggered=self._onExportPreset)
        self.deleteAction = Action(icon=FICO.DELETE, text='Delete (Del)', triggered=self._onDeletePreset)

        # Set initial button states
        self.undoAction.setEnabled(self.undoStack.canUndo())
        self.redoAction.setEnabled(self.undoStack.canRedo())
        self.editAction.setEnabled(False)
        self.exportAction.setEnabled(False)
        self.deleteAction.setEnabled(False)

        # Add actions to command bar
        createPresetButton = self.commandBar.addAction(self.createPreset)
        self.commandBar.addSeparator()
        self.commandBar.addActions([
            self.undoAction,
            self.redoAction,
            self.editAction,
            self.exportAction,
            self.deleteAction
        ])
        createPresetButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

    def _setupNewPresetMenu(self):
        self.newPresetMenu = RoundMenu()
        self.emptyPresetAction = Action(icon=FICO.ADD_SQUARE, text='Empty preset', triggered=partial(self._onAddPreset, 'empty'))
        self.templatePresetAction = Action(icon=FICO.COLLECTIONS, text='Template preset', triggered=partial(self._onAddPreset, 'template'))

        # These are here so they show up in the menu
        self.emptyPresetAction.setShortcut(QKeySequence('Ctrl+N'))
        self.templatePresetAction.setShortcut(QKeySequence('Ctrl+Shift+N'))

        self.newPresetMenu.addActions([
            self.emptyPresetAction,
            self.templatePresetAction
        ])

    def _setupEditPresetMenu(self):
        self.editPresetMenu = RoundMenu()

        sampleText = 'Edit samples' if self.currentPresetType == 'instruments' else 'Edit sample'

        self.editParameterAction = Action(icon=FICO.NOTE_EDIT, text='Edit parameters', triggered=self._editParameterDialog)
        self.editSampleAction = Action(icon=FICO.NOTE_EDIT, text=sampleText, triggered=self._editSampleDialog)
        self.editEnvelopeAction = Action(icon=FICO.NOTE_EDIT, text='Edit envelope', triggered=self._editEnvelopeDialog)

        # Shortcuts
        # These are here so they show up in the menu
        self.editParameterAction.setShortcut('Ctrl+E, P')
        self.editSampleAction.setShortcut('Ctrl+E, S')
        self.editEnvelopeAction.setShortcut('Ctrl+E, E')

        if self.currentPresetType in ('instruments', 'drums', 'samples', 'envelopes'):
            self.editPresetMenu.addAction(self.editParameterAction)

        if self.currentPresetType in ('instruments', 'drums', 'effects'):
            self.editPresetMenu.addAction(self.editSampleAction)

        if self.currentPresetType in ('instruments', 'drums'):
            self.editPresetMenu.addAction(self.editEnvelopeAction)

    def _setupPivotActions(self):
        self.pivotItems = [
            ('instrumentsInterface', 'Instruments', self._clearListSelection),
            ('drumsInterface', 'Drums', self._clearListSelection),
            ('effectsInterface', 'Effects', self._clearListSelection),
            ('samplesInterface', 'Samples', self._clearListSelection),
            ('envelopesInterface', 'Envelopes', self._clearListSelection),
        ]

        for routeKey, text, callback in self.pivotItems:
            self.pivot.addItem(
                routeKey=routeKey,
                text=text,
                onClick=callback
            )

        self.pivot.setCurrentItem('instrumentsInterface')

    def _setupPageShortcuts(self):
        shortcut_map = {
            'Ctrl+N': partial(self._onAddPreset, 'empty'),
            'Ctrl+Shift+N': partial(self._onAddPreset, 'template'),
            'Ctrl+E, P': self._editParameterDialog,
            'Ctrl+E, S': self._editSampleDialog,
            'Ctrl+E, E': self._editEnvelopeDialog,
            'Ctrl+C': self._onCopyPreset,
            'Ctrl+V': self._onPastePreset,
            'Ctrl+S': self._onExportPreset,
            'Ctrl+Z': self.undoStack.undo,
            'Ctrl+Y': self.undoStack.redo,
            'Ctrl+D': self._clearListSelection,
            'Del': self._onDeletePreset,
        }

        for seq, func in shortcut_map.items():
            shortcut = QShortcut(QKeySequence(seq), self.page)
            shortcut.activated.connect(func)

    def _connectSignals(self):
        cfg.themeChanged.connect(self.onThemeChanged)
        cfg.presetsFolderChanged.connect(self._loadAllPresets)

        self.undoStack.canUndoChanged.connect(self.undoAction.setEnabled)
        self.undoStack.canRedoChanged.connect(self.redoAction.setEnabled)

        self.pivot.currentItemChanged.connect(self._onTabChanged)
        self.listView.currentItemChanged.connect(self._onItemSelected)
        self.listView.customContextMenuRequested.connect(self._onListContextMenu)
    #endregion

    #region List Handling
    def _clearListSelection(self):
        self.presetObject = None
        self.selectedItem = None

        self.listView.clearSelection()
        self.listView.setCurrentItem(None)
        self.listView.clearFocus()

    def _onItemSelected(self, current, previous):
        if current is None:
            self.selectedItem = None
            self.presetObject = None
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
            self.presetObject = current.data(Qt.ItemDataRole.UserRole)

    def _onTabChanged(self, value):
        types = {
            'instrumentsInterface': 'instruments',
            'drumsInterface': 'drums',
            'effectsInterface': 'effects',
            'samplesInterface': 'samples',
            'envelopesInterface': 'envelopes'
        }
        self.currentPresetType = types.get(value)
        self._refreshListView()
        self._clearListSelection()

        # Recreate edit menu
        self._setupEditPresetMenu()

    def _loadAllPresets(self):
        self.builtinPresets.load_builtin_presets()
        self.userPresets.load_user_presets(Path(cfg.get(cfg.presetsfolder)))

    def _refreshListView(self):
        self.listView.clear()

        presetList = self._getPresetList(self.currentPresetType)
        name_counts = defaultdict(int)

        for obj in presetList:
            name_counts[obj.name] += 1

        for obj in presetList:
            displayName = obj.name
            if name_counts[obj.name] > 1:
                path = self.userPresets.get_path(obj)
                if path:
                    import os
                    filename = os.path.basename(path)
                    displayName = f'{obj.name} ({filename})'
                else:
                    displayName = f'{obj.name}'

            item = QListWidgetItem(displayName)
            item.setData(Qt.ItemDataRole.UserRole, obj)

            if id(obj) in self.editedPresets:
                # item.setIcon(make_dot_icon())
                pass

            self.listView.addItem(item)

    def _getPresetList(self, presetType: str):
        return {
            'instruments': self.userPresets.instruments.values(),
            'drums': self.userPresets.drums.values(),
            'effects': self.userPresets.effects.values(),
            'samples': self.userPresets.samples.values(),
            'envelopes': self.userPresets.envelopes.values()
        }.get(presetType, [])
    #endregion

    #region Preset Handling
    def _onAddPreset(self, formType='empty', boolean=False):
        dialog = CreatePresetDialog(formType, self.page)

        if dialog.exec():
            if not dialog.form.applyChanges():
                return

            newPreset = dialog.form.preset
            self.currentPresetType = dialog.form.selectedType
            self.pivot.setCurrentItem(f'{self.currentPresetType}Interface')

            newPreset = presetRegistry.get_or_register(newPreset)
            cmd = CreatePresetCommand(self, newPreset, f'Create {self.currentPresetType[:-1]}')
            self.undoStack.push(cmd)
            self._clearListSelection()

    def _onExportPreset(self):
        if not self.selectedItem:
            return

        preset = self.selectedItem.data(Qt.ItemDataRole.UserRole)
        dict = serialize_to_yaml(preset, self.currentPresetType)

        openDir = Path(cfg.presetsfolder.value) / self.currentPresetType
        openDir.mkdir(parents=True, exist_ok=True)

        defaultFilename = f'{preset.name}.yaml'
        defaultFilePath = str(openDir / defaultFilename)

        filePath, _ = QFileDialog.getSaveFileName(
            self.page,
            'Export Preset as YAML',
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

        self.userPresets.remove_preset(preset)
        self.userPresets.add_preset(preset, filePath)

    def _onDeletePreset(self):
        if not self.selectedItem:
            return
        # Not Implemented
        return

    def _onCopyPreset(self):
        if not self.selectedItem:
            return
        self.copiedPreset = self.selectedItem.data(Qt.ItemDataRole.UserRole)

    def _onPastePreset(self):
        if not self.copiedPreset:
            return

        existingNames = {
            self.listView.item(i).text()
            for i in range(self.listView.count())
        }

        newName = generate_copy_name(self.copiedPreset.name, existingNames)
        newPreset = clone_preset(
            original=self.copiedPreset,
            new_name=newName
        )

        newPreset = presetRegistry.get_or_register(newPreset)
        cmd = CreatePresetCommand(self, newPreset)
        self.undoStack.push(cmd)
    #endregion

    #region Menus
    def _onListContextMenu(self, pos):
        item = self.listView.itemAt(pos)
        if item:
            self.listView.setCurrentItem(item)

        if not self.selectedItem:
            return

        preset = self.selectedItem.data(Qt.ItemDataRole.UserRole)
        menu = RoundMenu(parent=self.page)

        # Actions
        copyPresetAction = Action(icon=FIF.COPY, text='Copy', triggered=self._onCopyPreset)
        pastePresetAction = Action(icon=FICO.CLIPBOARD_PASTE, text='Paste', triggered=self._onPastePreset)
        exportPresetAction = Action(icon=FICO.SHARE_IOS, text='Export', triggered=self._onExportPreset)
        deletePresetAction = Action(icon=FIF.DELETE, text='Delete', triggered=self._onDeletePreset)

        # Shortcuts
        # These are here so they show up in the menu
        copyPresetAction.setShortcut(QKeySequence('Ctrl+C'))
        pastePresetAction.setShortcut(QKeySequence('Ctrl+V'))
        exportPresetAction.setShortcut(QKeySequence('Ctrl+S'))
        deletePresetAction.setShortcut(QKeySequence('Del'))

        menu.addActions([copyPresetAction, pastePresetAction, exportPresetAction, deletePresetAction])

        globalPos = self.listView.mapToGlobal(pos)
        menu.exec(globalPos, True, MenuAnimationType.DROP_DOWN)

    def _showNewPresetMenu(self):
        self._showMenuBelowAction(self.createPreset, self.newPresetMenu)

    def _showEditPresetMenu(self):
        self._showMenuBelowAction(self.editAction, self.editPresetMenu)

    def _showMenuBelowAction(self, targetAction: Action, menu: RoundMenu):
        for button in self.commandBar.commandButtons:
            if button.action() is targetAction:
                pos = button.mapToGlobal(button.rect().bottomLeft())
                menu.exec(pos, True, MenuAnimationType.DROP_DOWN)
                return
    #endregion

    #region Dialogs
    def _editParameterDialog(self):
        if self.currentPresetType in ('effects'):
            return
        self._showEditDialog(EditParameterDialog, self.currentPresetType)

    def _editSampleDialog(self):
        if self.currentPresetType in ('samples', 'envelopes'):
            return
        self._showEditDialog(EditSampleDialog, self.currentPresetType)

    def _editEnvelopeDialog(self):
        if self.currentPresetType in ('effects'):
            return
        self._showEditDialog(EditEnvelopeDialog)

    def _showEditDialog(self, dialogClass, *args):
        preset = self.selectedItem.data(Qt.ItemDataRole.UserRole)
        if not preset:
            return

        from App.Common.Helpers import clone_preset
        oldPreset = clone_preset(preset)

        dialog = dialogClass(preset, *args, self.page)
        if dialog.exec():
            editedPreset = dialog.preset
            dialog.applyChanges()

            cmd = EditPresetCommand(
                originalPreset=oldPreset,
                editedPreset=editedPreset,
                viewModel=self
            )
            self.undoStack.push(cmd)
            self.editedPresets.add(id(editedPreset))
            self._refreshListView()
            self._clearListSelection()
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
    #endregion

    def onThemeChanged(self):
        hasSelection = self.selectedItem is not None
        self.editAction.setEnabled(hasSelection)
        self.exportAction.setEnabled(hasSelection)
        self.deleteAction.setEnabled(hasSelection)
