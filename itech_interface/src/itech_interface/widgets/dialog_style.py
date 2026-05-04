"""Shared QSS stylesheet for all test dialog windows."""

POPUP_STYLESHEET = """
    QDialog {
        background-color: #1e1e2e;
    }
    QDialog * {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13pt;
        color: #e2e8f0;
    }
    QDialog QPushButton {
        min-height: 44px;
        padding: 8px 20px;
        background-color: #7c3aed;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 13pt;
        font-weight: 500;
    }
    QDialog QPushButton:hover {
        background-color: #6d28d9;
    }
    QDialog QPushButton:pressed {
        background-color: #5b21b6;
    }
    QDialog QPushButton:disabled {
        background-color: #3b3b54;
        color: #6b7280;
    }
    QDialog QPushButton#start_btn {
        background-color: #10b981;
        font-weight: bold;
        font-size: 14pt;
        min-height: 50px;
        border-radius: 10px;
    }
    QDialog QPushButton#start_btn:hover {
        background-color: #059669;
    }
    QDialog QPushButton#close_btn {
        background-color: #ef4444;
        font-size: 12pt;
        min-height: 38px;
    }
    QDialog QPushButton#close_btn:hover {
        background-color: #dc2626;
    }
    QDialog QPushButton#cart_btn {
        min-height: 80px;
        font-size: 15pt;
        font-weight: bold;
        border-radius: 10px;
        background-color: #7c3aed;
    }
    QDialog QPushButton#cart_btn:hover {
        background-color: #6d28d9;
    }
    QDialog QLabel#instructions {
        background-color: #1e3a5f;
        border: 1px solid #2563eb;
        border-radius: 8px;
        padding: 14px 16px;
        color: #93c5fd;
        font-size: 13pt;
    }
    QDialog QLabel#voltage_live {
        background-color: #422006;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 18pt;
        font-weight: bold;
        color: #fbbf24;
    }
    QDialog QLabel#cart_label {
        background-color: #2a2a3d;
        border: 1px solid #3b3b54;
        border-radius: 6px;
        padding: 8px 12px;
        color: #e2e8f0;
        font-size: 13pt;
    }
    QDialog QLabel {
        padding: 4px 0px;
        color: #e2e8f0;
    }
"""
