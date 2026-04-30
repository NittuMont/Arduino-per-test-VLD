from PyQt5 import QtWidgets, QtCore

class ResultLabel(QtWidgets.QLabel):
    def __init__(self, text="Pronto", parent=None):
        super().__init__(text, parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #e8e8e8;
                border-radius: 6px;
                padding: 10px;
                font-size: 15pt;
                font-weight: bold;
                color: #555;
            }
        """)

    def set_status(self, text, level="info"):
        colours = {
            "info":    ("#e8e8e8", "#555"),
            "ok":      ("#dff6dd", "#107c10"),
            "error":   ("#fde7e9", "#d13438"),
            "working": ("#fff4ce", "#8a6d00"),
        }
        bg, fg = colours.get(level, colours["info"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                border-radius: 6px;
                padding: 10px;
                font-size: 15pt;
                font-weight: bold;
                color: {fg};
            }}
        """)
        self.setText(text)
