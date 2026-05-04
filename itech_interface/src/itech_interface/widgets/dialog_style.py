"""Shared QSS stylesheet for all test dialog windows."""

POPUP_STYLESHEET = """
    QDialog {
        background-color: #f5f6fa;
    }
    QDialog * {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14pt;
    }
    QDialog QPushButton {
        min-height: 44px;
        padding: 8px 20px;
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 13pt;
        font-weight: 500;
    }
    QDialog QPushButton:hover {
        background-color: #106ebe;
    }
    QDialog QPushButton:pressed {
        background-color: #005a9e;
    }
    QDialog QPushButton:disabled {
        background-color: #d0d4dc;
        color: #8a8a8a;
    }
    QDialog QPushButton#start_btn {
        background-color: #107c10;
        font-weight: bold;
        font-size: 14pt;
        min-height: 50px;
        border-radius: 10px;
    }
    QDialog QPushButton#start_btn:hover {
        background-color: #0b6a0b;
    }
    QDialog QPushButton#close_btn {
        background-color: #d13438;
        font-size: 12pt;
        min-height: 38px;
    }
    QDialog QPushButton#close_btn:hover {
        background-color: #a4262c;
    }
    QDialog QPushButton#cart_btn {
        min-height: 80px;
        font-size: 15pt;
        font-weight: bold;
        border-radius: 10px;
    }
    QDialog QLabel#instructions {
        background-color: #e8f4fd;
        border: 1px solid #b3d7f0;
        border-radius: 8px;
        padding: 14px 16px;
        color: #004578;
        font-size: 13pt;
        line-height: 1.4;
    }
    QDialog QLabel#voltage_live {
        background-color: #fff8e1;
        border: 1px solid #ffe082;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 18pt;
        font-weight: bold;
        color: #6d4c00;
    }
    QDialog QLabel#cart_label {
        background-color: white;
        border: 1px solid #e0e3eb;
        border-radius: 6px;
        padding: 8px 12px;
        color: #333;
        font-size: 13pt;
    }
    QDialog QLabel {
        padding: 4px 0px;
        color: #333;
    }
"""
