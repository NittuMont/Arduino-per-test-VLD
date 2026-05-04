from PyQt5 import QtWidgets, QtCore

class ResultLabel(QtWidgets.QLabel):
    def __init__(self, text="Pronto", parent=None):
        super().__init__(text, parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f1f5;
                border: 1px solid #e0e3eb;
                border-radius: 8px;
                padding: 12px;
                font-size: 14pt;
                font-weight: bold;
                color: #555;
            }
        """)

    def set_status(self, text, level="info"):
        colours = {
            "info":    ("#f0f1f5", "#555", "#e0e3eb"),
            "ok":      ("#e6f9e6", "#107c10", "#a3d9a3"),
            "error":   ("#fde7e9", "#d13438", "#f5b3b5"),
            "working": ("#fff8e1", "#7a5c00", "#ffe082"),
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
