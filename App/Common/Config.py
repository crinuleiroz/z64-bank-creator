# App/Common/Config.py

import os
import sys

from PySide6.QtCore import QObject, Signal

from qfluentwidgets import (
    qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
    OptionsValidator, RangeConfigItem, RangeValidator, FolderValidator,
    FolderListValidator, Theme, ConfigSerializer, ConfigValidator
)


class ImageValidator(ConfigValidator):
    def __init__(self, extensions: list[str] = None):
        super().__init__()
        self.extensions = extensions or ['.png', '.jpg', '.jpeg']

    def Validate(self, value: str) -> bool:
        if not value:
            return True
        return os.path.isfile(value) and any(value.lower().endswith(ext) for ext in self.extensions)


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig, QObject):
    backgroundChanged = Signal(str)
    presetsFolderChanged = Signal(str)
    outputFolderChanged = Signal(str)

    # Appearance
    dpiscale = OptionsConfigItem(
        group='Appearance',
        name='DpiScale',
        default='Auto',
        validator=OptionsValidator([1, 1.25, 1.5, 1.75, 2, 'Auto']),
        restart=True
    )
    micaenabled = ConfigItem(
        group='Appearance',
        name='MicaEnabled',
        default=isWin11(),
        validator=BoolValidator()
    )

    # Personalization
    bgimage = ConfigItem(
        group='Personalization',
        name='BackgroundImage',
        default='Choose a background image for the application',
        validator=ImageValidator()
    )
    bgopacity = RangeConfigItem(
        group='Personalization',
        name='BackgroundOpacity',
        default=15,
        validator=RangeValidator(0, 100),
        restart=False
    )

    # Folders
    presetsfolder = ConfigItem(
        group='Folders',
        name='PresetsFolder',
        default='presets/',
        validator=FolderValidator()
    )
    outputfolder = ConfigItem(
        group='Folders',
        name='OutputFolder',
        default='output/',
        validator=FolderValidator()
    )

    def set(self, item: ConfigItem, value):
        super().set(item, value)

        if item is self.bgimage:
            self.backgroundChanged.emit(value)

        if item is self.presetsfolder:
            self.presetsFolderChanged.emit(value)

        if item is self.outputfolder:
            self.outputFolderChanged.emit(value)


APP_VERSION = '0.8.0' # Major.Minor.Patch

cfg = Config()
# cfg.themeMode.value = Theme.AUTO
cfg.themeMode.value = Theme.DARK
qconfig.load('config.json', cfg)
