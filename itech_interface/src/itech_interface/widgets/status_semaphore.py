from PyQt5 import QtWidgets, QtCore

class StatusSemaphore(QtWidgets.QLabel):
    def __init__(self, label_text="", color="#cccccc", parent=None):
        super().__init__(parent)
        self.setText(label_text)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedHeight(36)
        self.setStyleSheet(f"background:{color}; font-size:15pt; border-radius:8px; padding:8px;")

    def set_status(self, label_text, color):
        self.setText(label_text)
        self.setStyleSheet(f"background:{color}; font-size:15pt; border-radius:8px; padding:8px;")
