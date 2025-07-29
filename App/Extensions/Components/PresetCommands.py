# App/Extensions/Components/PresetCommands.py

import os
import shutil
import tempfile
from send2trash import send2trash

from PySide6.QtCore import Qt
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import QListWidgetItem


#region Create Preset
class CreatePresetCommand(QUndoCommand):
    def __init__(self, viewModel, preset, description='Create structure preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.preset = preset
        self.item = None
        self.presetType = viewModel.currentPresetType

    def undo(self):
        self.viewModel.userPresets.remove_preset(self.preset)
        self.viewModel._refreshListView()

    def redo(self):
        self.viewModel.userPresets.add_preset(self.preset)
        self.viewModel._refreshListView()
#endregion


#region Edit Preset
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


#region Paste Preset
class PastePresetCommand(QUndoCommand):
    def __init__(self, viewModel, presets: list, description='Paste structure preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.presets = presets
        self.presetType = viewModel.currentPresetType

    def undo(self):
        for p in self.presets:
            self.viewModel.userPresets.remove_preset(p)
        self.viewModel._refreshListView()

    def redo(self):
        for p in self.presets:
            self.viewModel.userPresets.add_preset(p)
        self.viewModel._refreshListView()
#endregion


#region Delete Preset
class DeletePresetCommand(QUndoCommand):
    def __init__(self, viewModel, presets: list, description='Delete structure preset'):
        super().__init__(description)
        self.viewModel = viewModel
        self.presets = presets
        self.presetType = viewModel.currentPresetType
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
        self.viewModel._refreshListView()

    def redo(self):
        for preset, filePath in zip(self.presets, self.filePaths):
            if filePath and os.path.exists(filePath):
                try:
                    send2trash(filePath)
                except Exception as ex:
                    print(f'FIle deletion failed for {filePath}: {ex}')
            self.viewModel.userPresets.remove_preset(preset)
        self.viewModel._refreshListView()

    def __del__(self):
        try:
            for backupFile in self.backupFiles:
                if backupFile and os.path.exists(backupFile):
                    os.remove(backupFile)
        except Exception as ex:
            print(f'Error during cleanup: {ex}')
#endregion
