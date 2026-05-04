"""Shared QSS stylesheet for all test dialog windows."""

POPUP_STYLESHEET = """
    QDialog {
        background-color: #f0f2f5;
    }
    QDialog * {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 15pt;
    }
    QDialog QPushButton {
        min-height: 46px;
        padding: 8px 18px;
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 6px;
    }
    QDialog QPushButton:hover {
        background-color: #106ebe;
    }
    QDialog QPushButton:pressed {
        background-color: #005a9e;
    }
    QDialog QPushButton:disabled {
        background-color: #b0b0b0;
        color: #e0e0e0;
    }
    QDialog QPushButton#start_btn {
        background-color: #107c10;
        font-weight: bold;
    }
    QDialog QPushButton#start_btn:hover {
        background-color: #0b6a0b;
    }
    QDialog QPushButton#close_btn {
        background-color: #d13438;
    }
    QDialog QPushButton#close_btn:hover {
        background-color: #a4262c;
    }
    QDialog QPushButton#cart_btn {
        min-height: 92px;
    }
    QDialog QLabel#instructions {
        background-color: #e8f4fd;
        border: 1px solid #b3d7f0;
        border-radius: 6px;
        padding: 12px;
        color: #004578;
        font-size: 14pt;
    }
    QDialog QLabel#voltage_live {
        background-color: #fff4ce;
        border: 1px solid #f0d060;
        border-radius: 6px;
        padding: 10px;
        font-size: 16pt;
        font-weight: bold;
        color: #8a6d00;
    }
    QDialog QLabel#cart_label {
        background-color: white;
        border: 1px solid #d0d0d0;
        border-radius: 4px;
        padding: 6px 10px;
        color: #333;
    }
    QDialog QLabel {
        padding: 4px 0px;
        color: #333;
    }
"""
