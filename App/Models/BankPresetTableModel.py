# App/Models/BankPresetTableModel.py

from PySide6.QtCore import Qt, QAbstractTableModel

# App/Resources
from App.Resources.Emoji.MSFluentEmoji import MSFluentEmoji as FEMO


GAME_TITLES = {
    'OOT': "Ocarina of Time",
    'MM': "Majora's Mask",
}


class BankPresetTableModel(QAbstractTableModel):
    def __init__(self, presets=None):
        super().__init__()
        self.presets = presets or []

    def rowCount(self, parent=None):
        return len(self.presets)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        preset = self.presets[index.row()]
        col = index.column()

        match col:
            case 0:
                if role == Qt.ItemDataRole.DisplayRole:
                    return GAME_TITLES.get(preset.game, 'INVALID GAME')
                if role == Qt.ItemDataRole.DecorationRole:
                    if preset.game in GAME_TITLES:
                        return None
                    else:
                        return FEMO.WARNING_COLOR.icon()

            case 1:
                if role == Qt.ItemDataRole.DisplayRole:
                    return preset.name

            case _:
                if role == Qt.ItemDataRole.UserRole:
                    return preset

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ["Game", "Preset Name"][section]
        return None

    def updatePresets(self, presets):
        self.beginResetModel()
        self.presets = presets
        self.endResetModel()
