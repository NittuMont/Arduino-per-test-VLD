from PyQt5 import QtWidgets, QtCore

class ResultLabel(QtWidgets.QLabel):
    def __init__(self, text="Pronto", parent=None):
        super().__init__(text, parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #2a2a3d;
                border: 1px solid #3b3b54;
                border-radius: 8px;
                padding: 12px;
                font-size: 14pt;
                font-weight: bold;
                color: #94a3b8;
            }
        """)

    def set_status(self, text, level="info"):
        colours = {
            "info":    ("#2a2a3d", "#94a3b8", "#3b3b54"),
            "ok":      ("#064e3b", "#10b981", "#065f46"),
            "error":   ("#450a0a", "#ef4444", "#7f1d1d"),
            "working": ("#422006", "#f59e0b", "#78350f"),
        }
        bg, fg, border = colours.get(level, colours["info"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 12px;
                font-size: 14pt;
                font-weight: bold;
                color: {fg};
            }}
        """)
        self.setText(text)
