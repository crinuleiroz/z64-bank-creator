# App/Common/SignalBus.py

from PySide6.QtCore import QObject, Signal

class SignalBus(QObject):
    micaEnableChanged = Signal(bool)

signalBus = SignalBus()