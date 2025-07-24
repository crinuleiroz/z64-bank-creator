# App/Extensions/Icons.py

from enum import Enum

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from qfluentwidgets.common.icon import FluentIconBase, getIconColor
from qfluentwidgets.common.style_sheet import Theme, isDarkTheme


class MSFluentIcon(FluentIconBase, Enum):
    ADD_CIRCLE = "add_circle_48"
    APPS = "apps_48"
    ARROW_CLOCKWISE = "arrow_clockwise"
    ARROW_COUNTERCLOCKWISE = "arrow_counterclockwise"
    BOOK = "book_48"
    BOOK_ADD = "book_add_48"
    BOOK_OPEN = "book_open_48"
    BOOK_TEMPLATE = "book_template_20"
    BRANCH = "branch_24"
    BRANCH_FORK = "branch_fork_32"
    CODE = "code_24"
    COLOR = "color_24"
    COPY = "copy_32"
    DISMISS_CIRCLE = "dismiss_circle_48"
    DOCUMENT = "document_48"
    DOCUMENT_ADD = "document_add_48"
    DOCUMENT_EDIT = "document_edit_24"
    EDIT = "edit_48"
    FAST_FORWARD = "fast_forward_28"
    FOLDER = "folder_48"
    FOLDER_ADD = "folder_add_48"
    FORM = "form_48"
    FORM_NEW = "form_new"
    HEART = "heart_48"
    HEART_BROKEN = "heart_broken_24"
    HOME = "home_48"
    LAYER_DIAGONAL = "layer_diagonal_24"
    LAYER_DIAGONAL_ADD = "layer_diagonal_add_24"
    LIBRARY = "library_32"
    MOLECULE = "molecule_48"
    MORE_HORIZONTAL = "more_horizontal_48"
    MORE_VERTICAL = "more_vertical_48"
    MUSIC_NOTE_1 = "music_note_1_24"
    MUSIC_NOTE_2 = "music_note_2_24"
    NOTE = "note_48"
    NOTE_ADD = "note_add_48"
    NOTE_EDIT = "note_edit_24"
    PAINT_BRUSH = "paint_brush_32"
    PAINT_BRUSH_SPARKLE = "paint_brush_sparkle_24"
    PUZZLE_PIECE = "puzzle_piece_48"
    REDO = "arrow_redo_48"
    SAVE = "save_32"
    SETTINGS = "settings_48"
    SHARE = "share_48"
    SHARE_ANDROID = "share_android_32"
    SHARE_IOS = "share_ios_48"
    SPARKLE = "sparkle_48"
    UNDO = "arrow_undo_48"

    def path(self, theme=Theme.AUTO):
        return f':/assets/icons/{self.value}_{getIconColor(theme)}.svg'

def load_scaled_icon(icon_enum, size=48):
    icon = QIcon(icon_enum.path())
    pixmap = icon.pixmap(QSize(size, size))
    return QIcon(pixmap)