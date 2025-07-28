# App/Views/Pages/SettingsPage.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import (
    TitleLabel, ScrollArea, ExpandLayout, SettingCardGroup,
    ComboBoxSettingCard, SwitchSettingCard, PushSettingCard, RangeSettingCard
)
from qfluentwidgets import FluentIcon as FIF

# App/Common
from App.Common.Config import cfg

# App/Extensions
from App.Extensions.Widgets.BackgroundImageCard import BackgroundImageCard

# App/ViewModels
from App.ViewModels.Pages import SettingsViewModel


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('settingsPage')

        # Core widgets
        self._initHeader()
        self._initScrollArea()
        self._initAppearanceGroup()
        self._initPersonalizationGroup()
        self._initFoldersGroup()

        # Layout
        self._buildLayout()

        # Create page
        self.viewModel = SettingsViewModel()
        self.viewModel.initPage(self)

    #region initialization
    def _initHeader(self):
        self.headerWidget = QWidget(self)
        self.headerLayout = QVBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLabel = TitleLabel('Settings')

        self.headerLayout.addWidget(self.headerLabel)

    def _initScrollArea(self):
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setObjectName('settingsScrollArea')
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet('background-color: transparent; border: none;')

        self.scrollWidget = QWidget(self)
        self.expandLayout = ExpandLayout(self.scrollWidget)
        self.expandLayout.setContentsMargins(0, 0, 0, 0)
        self.expandLayout.setSpacing(20)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

    def _initAppearanceGroup(self):
        self.appearanceGroup = SettingCardGroup('Appearance', self.scrollWidget)

        # Currently causing more issues than is worth dealing with
        # self.themeCard = ComboBoxSettingCard(
        #     configItem=cfg.themeMode,
        #     icon=FIF.BRUSH,
        #     title='Color mode',
        #     content='Change the application\'s interface colors',
        #     texts=['Light', 'Dark', 'System'],
        #     parent=self.appearanceGroup
        # )
        self.dpiScaleCard = ComboBoxSettingCard(
            configItem=cfg.dpiscale,
            icon=FIF.ZOOM,
            title='Scaling',
            content='Choose the size of the application window',
            texts=['100%', '125%', '150%', '175%', '200%', 'Use System Settings'],
            parent=self.appearanceGroup
        )
        self.micaCard = SwitchSettingCard(
            configItem=cfg.micaenabled,
            icon=FIF.TRANSPARENT,
            title='Transparency effects',
            content='The app window and surfaces appear transparent',
            parent=self.appearanceGroup
        )

        self.appearanceGroup.addSettingCards([
            self.dpiScaleCard,
            self.micaCard
        ])

    def _initPersonalizationGroup(self):
        self.personalizationGroup = SettingCardGroup('Personalization', self.scrollWidget)

        self.bgPickerCard = BackgroundImageCard(
            configItem=cfg.bgimage,
            icon=FIF.PHOTO,
            title='Personalize app background',
            content='A picture background applies to the app window',
            parent=self.personalizationGroup
        )
        self.bgOpacityCard = RangeSettingCard(
            configItem=cfg.bgopacity,
            icon=FIF.TRANSPARENT,
            title='Background opacity',
            content='Choose the opacity of the application\'s background image',
            parent=self.personalizationGroup
        )

        self.personalizationGroup.addSettingCards([
            self.bgPickerCard,
            self.bgOpacityCard
        ])

    def _initFoldersGroup(self):
        self.foldersGroup = SettingCardGroup('Folders', self.scrollWidget)

        self.presetFolderPickerCard = PushSettingCard(
            text='Choose folder',
            icon=FIF.FOLDER_ADD,
            title='Presets folder',
            content=cfg.get(cfg.presetsfolder),
            parent=self.foldersGroup
        )
        self.outputFolderPickerCard = PushSettingCard(
            text='Choose folder',
            icon=FIF.FOLDER_ADD,
            title='Output folder',
            content=cfg.get(cfg.outputfolder),
            parent=self.foldersGroup
        )

        self.foldersGroup.addSettingCards([
            self.presetFolderPickerCard,
            self.outputFolderPickerCard
        ])

    def _buildLayout(self):
        self.expandLayout.addWidget(self.appearanceGroup)
        self.expandLayout.addWidget(self.personalizationGroup)
        self.expandLayout.addWidget(self.foldersGroup)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(20, 12, 20, 20)
        mainLayout.setSpacing(16)

        # Add widgets to page layout
        mainLayout.addWidget(self.headerWidget)
        mainLayout.addWidget(self.scrollArea)
    #endregion
