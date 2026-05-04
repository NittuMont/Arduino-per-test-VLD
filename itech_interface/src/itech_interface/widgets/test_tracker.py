"""TestTrackerWidget — piccolo indicatore visivo dello stato dei test per
la matricola corrente.  Legge le celle chiave direttamente dall'Excel.
"""

from PyQt5 import QtWidgets, QtCore, QtGui

# Colori
_COLOR_DONE    = "#10b981"   # verde accento
_COLOR_PENDING = "#4b5563"   # grigio scuro
_COLOR_UNKNOWN = "#374151"   # grigio molto scuro

# Layout a due righe: stessa disposizione dei pulsanti test
_ROW_TOP = ["100V", "500V"]
_ROW_BOTTOM = ["AD", "AT+AL", "Innesco"]
_ALL_TESTS = _ROW_TOP + _ROW_BOTTOM


class _Dot(QtWidgets.QLabel):
    """Cerchio colorato 24×24 px."""
    SIZE = 24

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.set_unknown()

    def _apply(self, color: str):
        self.setStyleSheet(
            f"background-color:{color}; border-radius:{self.SIZE//2}px; "
            f"border: 2px solid rgba(0,0,0,0.08);"
        )

    def set_done(self):    self._apply(_COLOR_DONE)
    def set_pending(self): self._apply(_COLOR_PENDING)
    def set_unknown(self): self._apply(_COLOR_UNKNOWN)


class TestTrackerWidget(QtWidgets.QGroupBox):
    """Indicatore visivo a due righe, allineato ai pulsanti test."""

    def __init__(self, parent=None):
        super().__init__("Stato test matricola", parent)
        self.setFlat(True)
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(16)

        self._dots: dict[str, _Dot] = {}

        for row_names in (_ROW_TOP, _ROW_BOTTOM):
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.setSpacing(24)
            row_layout.setAlignment(QtCore.Qt.AlignCenter)
            for name in row_names:
                col = QtWidgets.QVBoxLayout()
                col.setSpacing(2)
                col.setAlignment(QtCore.Qt.AlignCenter)

                dot = _Dot()
                self._dots[name] = dot
                col.addWidget(dot, alignment=QtCore.Qt.AlignCenter)

                lbl = QtWidgets.QLabel(name)
                lbl.setAlignment(QtCore.Qt.AlignCenter)
                lbl.setStyleSheet("font-size:10pt; color:#e2e8f0; font-weight:bold;")
                col.addWidget(lbl)

                row_layout.addLayout(col)
            outer.addLayout(row_layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_unknown(self):
        """Tutti i test sconosciuti (nessun file / matricola)."""
        for dot in self._dots.values():
            dot.set_unknown()

    def update_status(self, status: dict):
        """*status* è il dict restituito da ExcelHandler.get_test_status().
        Chiavi assenti vengono trattate come pendenti.
        """
        for name, dot in self._dots.items():
            done = status.get(name, False)
            if done:
                dot.set_done()
            else:
                dot.set_pending()
