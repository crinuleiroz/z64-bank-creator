# App/Extensions/Forms/EnvelopeArrayEditForm.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QSizePolicy

from qfluentwidgets import TableWidget, CommandBar, Action, LineEdit

# App/Resources
from App.Resources.Icons.MSFluentIcons import MSFluentIcon as FICO

# App/Common
from App.Common.Enums import EnvelopeOpcode

# App/Extensions
from App.Extensions.Widgets.CardGroup import CardGroup


S16_MIN = -32768
S16_MAX = 32767


class EnvelopeArrayEditForm(QWidget):
    def __init__(self, preset, parent=None):
        super().__init__(parent)
        self.preset = preset
        self.envArray: list[int | str] = preset.array

        self._initForm()
        self._initLayout()

    def _initForm(self):
        self._createNameGroup()
        self._createTableGroup()

    def _initLayout(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(self.nameGroup)
        layout.addWidget(self.tableGroup)

    def _createNameGroup(self):
        self.nameGroup = CardGroup('Preset name', 14, self)

        self.nameEdit = LineEdit(self.nameGroup)
        self.nameEdit.setText(self.preset.name)

        self.nameGroup.addCard(self.nameEdit)

    def _createTableGroup(self):
        self.tableGroup = CardGroup('Envelope array', 14, self)
        self.tableGroup.cardLayout.setSpacing(4)

        self._createCommandBar()
        self._createTableView()

        self.tableGroup.addCards([
            self.commandBar,
            self.tableView
        ])

    def _createCommandBar(self):
        self.commandBar = CommandBar(self.tableGroup)
        self.commandBar.setSpaing(0) # Bugged should be setSpacing()
        self.commandBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self._setupCommandBarButtons()

    def _setupCommandBarButtons(self):
        self.addTableRowAction = Action(icon=FICO.ADD, text='Add point', triggered=self._addRow)
        self.removeTableRowAction = Action(icon=FICO.DELETE, text='Remove point', triggered=self._deleteSelectedRow)

        self.removeTableRowAction.setEnabled(False)

        self.commandBar.addActions([
            self.addTableRowAction,
            self.removeTableRowAction
        ])

    def _createTableView(self):
        self.tableView = TableWidget(self.tableGroup)
        self.tableView.setRowCount(self._getRowCount())
        self.tableView.setColumnCount(2)
        self.tableView.setBorderVisible(True)
        self.tableView.setSelectionBehavior(self.tableView.SelectionBehavior.SelectRows)
        self.tableView.setFixedHeight(264) # Each row is ~47.5

        # Headers
        self.tableView.setHorizontalHeaderLabels(["Time or Opcode", "Amplitude or Index"])
        self.tableView.verticalHeader().hide()

        # Resize Columns
        self.tableView.setColumnWidth(0, 235)
        self.tableView.setColumnWidth(1, 235)

        self._loadTableViewData()
        self.tableView.itemSelectionChanged.connect(self._updateCommandBarButtonState)

    def _getRowCount(self):
        return len(self.envArray) // 2

    def _loadTableViewData(self):
        for i in range(0, len(self.envArray), 2):
            row = i // 2

            timeOrOpcodeVal = self.envArray[i]
            ampOrIndexVal = self.envArray[i + 1]

            timeOrOpcodeStr = timeOrOpcodeVal.name if isinstance(timeOrOpcodeVal, EnvelopeOpcode) else str(timeOrOpcodeVal)
            ampOrIndexStr = str(ampOrIndexVal)

            time = QTableWidgetItem(str(timeOrOpcodeStr))
            value = QTableWidgetItem(ampOrIndexStr)
            time.setData(Qt.ItemDataRole.UserRole, timeOrOpcodeVal)
            value.setData(Qt.ItemDataRole.UserRole, ampOrIndexVal)

            self.tableView.setItem(row, 0, time)
            self.tableView.setItem(row, 1, value)

    def _addRow(self):
        row = self.tableView.rowCount()
        self.tableView.insertRow(row)
        self.tableView.setItem(row, 0, QTableWidgetItem('HANG'))
        self.tableView.setItem(row, 1, QTableWidgetItem('0'))

    def _deleteSelectedRow(self):
        selectedRows = [item.row() for item in self.tableView.selectedItems()]
        for row in sorted(set(selectedRows), reverse=True):
            self.tableView.removeRow(row)

    def _updateCommandBarButtonState(self):
        selectedCount: int = len(self.tableView.selectedItems())
        hasSelection: bool = selectedCount > 0
        hasSingleSelection: bool = selectedCount == 1

        self.removeTableRowAction.setEnabled(hasSelection)

    def _getEnvelope(self) -> list[int | EnvelopeOpcode]:
        result = []
        for row in range(self.tableView.rowCount()):
            try:
                timeOrOpcodeText = self.tableView.item(row, 0).text().strip()
                ampOrIndexText = self.tableView.item(row, 1).text().strip()

                if timeOrOpcodeText.upper() in EnvelopeOpcode.__members__:
                    timeOrOpcodeValue = EnvelopeOpcode[timeOrOpcodeText.upper()]
                else:
                    timeOrOpcodeValue = int(timeOrOpcodeText)

                ampOrIndexValue = int(ampOrIndexText)

                for v in (int(timeOrOpcodeValue), ampOrIndexValue):
                    if not (S16_MIN <= v <= S16_MAX):
                        raise ValueError(f' Value {v} out of s16 range')

                result.extend([timeOrOpcodeValue, ampOrIndexValue])

            except Exception as ex:
                print(f'Invalid input for row {row}: {ex}')
                continue

        return result

    def applyChanges(self):
        newArray = self._getEnvelope()
        self.preset.array = newArray
