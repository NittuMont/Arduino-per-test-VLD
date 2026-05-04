from PyQt5 import QtWidgets, QtCore

class StatusSemaphore(QtWidgets.QLabel):
    def __init__(self, label_text="", color="#cccccc", parent=None):
        super().__init__(parent)
        self.setText(label_text)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedSize(16, 16)
        self._set_color(color)

    def _set_color(self, color):
        self.setStyleSheet(
            f"background-color: {color}; "
            f"border-radius: 8px; "
            f"border: 2px solid rgba(255,255,255,0.1);"
        )

    def set_status(self, label_text, color):
        self.setText(label_text)
        self._set_color(color)
