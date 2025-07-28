# App/ViewModels/Pages/SettingsViewModel.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog

from qfluentwidgets import InfoBar

# App/Common
from App.Common.Config import cfg, isWin11, APP_VERSION
from App.Common.SignalBus import signalBus


class SettingsViewModel(object):
    #region Initialization
    def initPage(self, parentPage):
        self.page = parentPage

        # Signals
        self._connectSlots()

    def _connectSlots(self):
        # cfg.themeChanged.connect(setTheme)
        cfg.appRestartSig.connect(self._showRestartTooltip)

        self.page.presetFolderPickerCard.clicked.connect(self._presetsFolderPickerClicked)
        self.page.outputFolderPickerCard.clicked.connect(self._outputFolderPickerClicked)
        self.page.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
    #endregion

    #region Dialogs
    def _presetsFolderPickerClicked(self):
        folder = QFileDialog.getExistingDirectory(
            parent=self,
            caption='Choose folder',
            dir='./',
            options=QFileDialog.Option.ShowDirsOnly
        )
        if not folder or cfg.get(cfg.presetsfolder) == folder:
            return

        cfg.set(cfg.presetsfolder, folder)
        self.page.presetFolderPickerCard.setContent(folder)

    def _outputFolderPickerClicked(self):
        folder = QFileDialog.getExistingDirectory(
            parent=self,
            caption='Choose folder',
            dir='./',
            options=QFileDialog.Option.ShowDirsOnly
        )
        if not folder or cfg.get(cfg.outputfolder) == folder:
            return

        cfg.set(cfg.outputfolder, folder)
        self.page.outputFolderPickerCard.setContent(folder)
    #endregion

    #region Tooltips
    def _showRestartTooltip(self):
        InfoBar.success(
            title='Updated scaling',
            content='Scaling will be changed after restarting the application',
            duration=3000,
            parent=self.page
        )
    #endregion
