"""TestTrackerWidget — piccolo indicatore visivo dello stato dei test per
la matricola corrente.  Legge le celle chiave direttamente dall'Excel.
"""

from PyQt5 import QtWidgets, QtCore, QtGui

# Colori
_COLOR_DONE    = "#107c10"   # verde
_COLOR_PENDING = "#888888"   # grigio
_COLOR_UNKNOWN = "#c0c0c0"   # grigio chiaro (file/matricola assente)

# Ordine e label brevi dei test
_TEST_ORDER = ["100V", "500V", "Innesco", "AT+AL", "AD"]


class _Dot(QtWidgets.QLabel):
    """Piccolo cerchio colorato 14×14 px."""
    SIZE = 14

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self.set_unknown()

    def _apply(self, color: str):
        self.setStyleSheet(
            f"background-color:{color}; border-radius:{self.SIZE//2}px;"
        )

    def set_done(self):    self._apply(_COLOR_DONE)
    def set_pending(self): self._apply(_COLOR_PENDING)
    def set_unknown(self): self._apply(_COLOR_UNKNOWN)


class TestTrackerWidget(QtWidgets.QGroupBox):
    """Barra orizzontale con un indicatore colorato per ogni test."""

    def __init__(self, parent=None):
        super().__init__("Stato test matricola", parent)
        self.setFlat(True)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)

        self._dots: dict[str, _Dot] = {}
        for name in _TEST_ORDER:
            col = QtWidgets.QVBoxLayout()
            col.setSpacing(2)
            col.setAlignment(QtCore.Qt.AlignCenter)

            dot = _Dot()
            self._dots[name] = dot
            col.addWidget(dot, alignment=QtCore.Qt.AlignCenter)

            lbl = QtWidgets.QLabel(name)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("font-size:9pt; color:#555;")
            col.addWidget(lbl)

            layout.addLayout(col)

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
