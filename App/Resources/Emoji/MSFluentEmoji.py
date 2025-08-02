# App/Extensions/MSFluentIcon.py

from enum import Enum

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from qfluentwidgets.common.icon import FluentIconBase, getIconColor
from qfluentwidgets.common.style_sheet import Theme


class MSFluentEmoji(FluentIconBase, Enum):
    WARNING_COLOR = "warning_color"

    def path(self, theme=Theme.AUTO):
        return f':/assets/emoji/msfluent/{self.value}.svg'
