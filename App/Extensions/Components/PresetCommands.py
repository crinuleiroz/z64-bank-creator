# App/Extensions/Components/PresetCommands.py

import os
import shutil
import tempfile
from send2trash import send2trash

from PySide6.QtCore import Qt
from PySide6.QtGui import QUndoCommand


#region Create Preset
class CreatePresetCommand(QUndoCommand):
    def __init__(self, viewModel, preset, description='Create preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.preset = preset
        self.item = None

    def undo(self):
        self.viewModel.userPresets.remove_preset(self.preset)
        self.viewModel.refresh()
        self.viewModel._clearPresetSelection()

    def redo(self):
        self.viewModel.userPresets.add_preset(self.preset)
        self.viewModel.refresh()
        self.viewModel._clearPresetSelection()
#endregion


#region Edit Table Entry
class EditBankTableEntryCommand(QUndoCommand):
    def __init__(self, preset, oldEntry, newEntry, viewModel, description='Edit table entry'):
        super().__init__(description)
        self.preset = preset
        self.oldEntry = oldEntry
        self.newEntry = newEntry
        self.viewModel = viewModel

    def undo(self):
        self.preset.tableEntry = self.oldEntry
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()

    def redo(self):
        self.preset.tableEntry = self.newEntry
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()
#endregion


#region Edit Bank List
class EditBankListCommand(QUndoCommand):
    def __init__(self, viewModel, preset, listType, oldList, newList):
        super().__init__(f'Edit {listType}')
        self.preset = preset
        self.listType = listType
        self.oldList = oldList
        self.newList = newList
        self.viewModel = viewModel

    def undo(self):
        setattr(self.preset, self.listType, self.oldList)
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()

    def redo(self):
        setattr(self.preset, self.listType, self.newList)
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()
#endregion


#region Edit Preset
class EditStructDataCommand(QUndoCommand):
    def __init__(self, viewModel, originalPreset, editedPreset, description='Edit preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.originalPreset = originalPreset
        self.editedPreset = editedPreset

    def undo(self):
        self.viewModel.userPresets.replace_preset(self.editedPreset, self.originalPreset)
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()

    def redo(self):
        self.viewModel.userPresets.replace_preset(self.originalPreset, self.editedPreset)
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()
#endregion


#region Paste Preset
class PastePresetCommand(QUndoCommand):
    def __init__(self, viewModel, presets: list, description='Paste preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.presets = presets

    def undo(self):
        for p in self.presets:
            self.viewModel.userPresets.remove_preset(p)
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()

    def redo(self):
        for p in self.presets:
            self.viewModel.userPresets.add_preset(p)
        self.viewModel.refresh()
        # self.viewModel._clearPresetSelection()
#endregion


#region Delete Preset
class DeletePresetCommand(QUndoCommand):
    def __init__(self, viewModel, presets: list, description='Delete preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.presets = presets
        self.filePaths = [viewModel.userPresets.get_path(id(p)) for p in presets]
        self.backupFiles = []

        for filePath in self.filePaths:
            backupFile = None
            if filePath and os.path.exists(filePath):
                try:
                    _, ext = os.path.splitext(filePath)
                    fd, backupFile = tempfile.mkstemp(suffix=ext)
                    os.close(fd)
                    shutil.copy2(filePath, backupFile)
                except Exception as ex:
                    print(f'Backup failed for {filePath}: {ex}')
                    backupFile = None
            self.backupFiles.append(backupFile)

    def undo(self):
        for preset, backupFile, filePath in zip(self.presets, self.backupFiles, self.filePaths):
            if backupFile and os.path.exists(backupFile):
                shutil.copy2(backupFile, filePath)
                self.viewModel.userPresets.add_preset(preset, filePath)
            else:
                self.viewModel.userPresets.add_preset(preset, filePath)
        self.viewModel.refresh()
        self.viewModel._clearPresetSelection()

    def redo(self):
        for preset, filePath in zip(self.presets, self.filePaths):
            if filePath and os.path.exists(filePath):
                try:
                    send2trash(filePath)
                except Exception as ex:
                    print(f'FIle deletion failed for {filePath}: {ex}')
            self.viewModel.userPresets.remove_preset(preset)
        self.viewModel.refresh()
        self.viewModel._clearPresetSelection()

    def __del__(self):
        try:
            for backupFile in self.backupFiles:
                if backupFile and os.path.exists(backupFile):
                    os.remove(backupFile)
        except Exception as ex:
            print(f'Error during cleanup: {ex}')
#endregion
