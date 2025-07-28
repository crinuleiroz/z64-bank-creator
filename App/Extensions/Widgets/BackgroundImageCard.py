# App/Extensions/Widgets/BackgroundImageCard.py

import os

from PySide6.QtCore import Qt, QStandardPaths
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog

from qfluentwidgets import BodyLabel, ToolButton, SimpleExpandGroupSettingCard
from qfluentwidgets import FluentIcon as FIF

# App/Common
from App.Common.Config import cfg


class BackgroundImageCard(SimpleExpandGroupSettingCard):
    def __init__(self, configItem, icon, title: str, content=None, parent=None):
        super().__init__(icon, title, content, parent=parent)

        self.configItem = configItem
        self.customImage = cfg.get(configItem)

        # Adjust card button
        self.card.setContentsMargins(0, 0, 8, 0)

        # Choose Image
        self.chooseImageWidget = QWidget(self.view)
        self.chooseImageLayout = QHBoxLayout(self.chooseImageWidget)
        self.chooseImageLabel = BodyLabel(
            text='Choose a photo',
            parent=self.chooseImageWidget
        )
        self.chooseImageButton = QPushButton(
            text='Browse photos',
            parent=self.chooseImageWidget
        )

        # Remove Image
        self.removeImageButton = ToolButton(FIF.DELETE)

        self.__initWidget()

    def __initWidget(self):
        self.chooseImageButton.setObjectName('chooseImageButton')
        self.chooseImageButton.clicked.connect(self.__chooseFileDialog)

        self.removeImageButton.setObjectName('removeImageButton')
        self.removeImageButton.clicked.connect(self.__removeBackground)

        self.__updateRemoveButtonState()
        self.__initLayout()

    def __initLayout(self):
        self.chooseImageLayout.setContentsMargins(48, 16, 48, 16)
        self.chooseImageLayout.addWidget(self.chooseImageLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.chooseImageLayout.addStretch(1)
        self.chooseImageLayout.addWidget(self.chooseImageButton, 0, Qt.AlignmentFlag.AlignRight)
        self.chooseImageLayout.addWidget(self.removeImageButton, 0, Qt.AlignmentFlag.AlignRight)

        self.viewLayout.setSpacing(0)
        self.addGroupWidget(self.chooseImageWidget)

    def __chooseFileDialog(self):
        imgPath, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select Background Image',
            dir=QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation),
            filter='*.png;;*.jpg;;*.jpeg;;All Files (*.png *.jpg *.jpeg)'
        )

        if imgPath:
            self.__onBackgroundImageChanged(imgPath)

    def __updateRemoveButtonState(self):
        path = cfg.get(self.configItem)
        self.removeImageButton.setEnabled(bool(path and os.path.isfile(path)))

    def __removeBackground(self):
        cfg.set(self.configItem, '')
        self.__updateRemoveButtonState()

    def __onBackgroundImageChanged(self, image):
        cfg.set(self.configItem, image)
        self.__updateRemoveButtonState()