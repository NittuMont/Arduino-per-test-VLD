"""Numeric text field shared by the main window and the Innesco dialog."""

from PyQt5 import QtCore, QtWidgets


class DiodeOffsetInput(QtWidgets.QDoubleSpinBox):
    LABEL_TEXT = "Caduta di tensione: (con SCR e iTech= 10,55 V"
    MINIMUM_V = -9999.99
    MAXIMUM_V = 9999.99

    def __init__(self, value: float, parent=None):
        super().__init__(parent)
        self.setObjectName("diode_offset_input")
        self.setLocale(QtCore.QLocale.c())
        self.setDecimals(2)
        self.setRange(self.MINIMUM_V, self.MAXIMUM_V)
        self.setSingleStep(0.01)
        self.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setKeyboardTracking(True)
        self.setMaximumWidth(140)
        self.setValue(value)
        self.setToolTip(
            "Offset in volt sottratto alla misura per la caduta diodo in Excel.\n"
            "Modificabile anche durante il test; accetta punto o virgola decimale.\n"
            "Il valore inserito viene ricordato per i successivi avvii."
        )
        self.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #3b3b54;
                border-radius: 6px;
                padding: 6px 10px;
                background: #1e1e2e;
                color: #e2e8f0;
                font-size: 13pt;
                selection-background-color: #7c3aed;
            }
            QDoubleSpinBox:focus { border-color: #7c3aed; }
            QDoubleSpinBox QLineEdit {
                border: none;
                padding: 0;
                background: transparent;
            }
        """)

    def validate(self, text, pos):
        return super().validate((text or "").replace(",", "."), pos)

    def valueFromText(self, text):  # noqa: N802 (Qt naming)
        return super().valueFromText((text or "").replace(",", "."))

    def set_synced_value(self, value: float) -> None:
        # Avoid feedback reformatting the field while the operator is typing.
        if self.value() != value:
            self.setValue(value)

    def current_value(self) -> float:
        # Commit pending input even if focus has not left the text field.
        # Invalid/incomplete input is restored to the last valid value by Qt.
        self.interpretText()
        return self.value()