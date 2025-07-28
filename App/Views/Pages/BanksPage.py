# App/Views/Pages/BanksPage.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import TitleLabel, CommandBar, ListWidget, ScrollArea

# App/Extensions
from App.Extensions.Widgets.Frame import Frame

# App/ViewModels
from App.ViewModels.Pages.BanksViewModel import BanksViewModel


class BanksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('banksPage')

        # Core widgets
        self._initHeader()
        self._initCommandBar()
        self._initScrollArea()

        # Layout
        self._buildLayout()

        # ViewModel
        self.viewModel = BanksViewModel()
        self.viewModel.initPage(self.listView, self.commandBar, self)

    #region Initialization
    def _initHeader(self):
        self.headerWidget = QWidget(self)
        self.headerLayout = QVBoxLayout(self.headerWidget)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)
        self.headerLabel = TitleLabel('Banks')

        self.headerLayout.addWidget(self.headerLabel)

    def _initCommandBar(self):
        self.commandBarWidget = QWidget(self)
        self.commandBarLayout = QVBoxLayout(self.commandBarWidget)
        self.commandBarLayout.setContentsMargins(0, 0, 0, 0)
        self.commandBar = CommandBar()

        self.commandBar.setSpaing(0) # Bugged should be setSpacing()
        self.commandBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        self.commandBarLayout.addWidget(self.commandBar)

    def _initScrollArea(self):
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setObjectName('banksScrollArea')
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setStyleSheet('background-color: transparent; border: none;')

        self.scrollWidget = QWidget(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollLayout.setSpacing(8)

        self.listFrame = Frame(self.scrollWidget)
        self.listView = ListWidget(self.listFrame)
        self.listView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.listFrame.addWidget(self.listView)
        self.scrollLayout.addWidget(self.listFrame)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

    def _buildLayout(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(20, 12, 20, 20)
        mainLayout.setSpacing(16)

        # Add widgets to page layout
        mainLayout.addWidget(self.headerWidget)
        mainLayout.addWidget(self.commandBarWidget)
        mainLayout.addWidget(self.scrollArea)
    #endregion

    def showEvent(self, event):
        super().showEvent(event)
        self.viewModel._clearListSelection()
