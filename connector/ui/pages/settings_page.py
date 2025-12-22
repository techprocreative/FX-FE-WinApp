from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.design_system import DesignTokens as DT, StyleSheets

class SettingsPage(QWidget):
    """
    Settings Page
    Manage Account, MT5 Connection, and Supabase Sync.
    """
    logout_requested = pyqtSignal()
    refresh_models_requested = pyqtSignal()
    connect_mt5_requested = pyqtSignal(dict) # login, password, server
    
    def __init__(self, user_data: Dict[str, Any]):
        super().__init__()
        self.user_data = user_data
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        spacing_mult = DT.get_responsive_spacing()
        margin = int(DT.SPACE_2XL * spacing_mult)
        spacing = int(DT.SPACE_LG * spacing_mult)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        # Header
        header = QLabel("Settings")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)

        # --- Account Section ---
        account_group = QGroupBox("Account")
        account_layout = QVBoxLayout(account_group)
        account_layout.setSpacing(DT.SPACE_MD)

        user_email = self.user_data.get('email', 'Unknown')
        email_label = QLabel(f"Logged in as: {user_email}")
        email_label.setStyleSheet(f"""
            color: {DT.SUCCESS};
            font-size: {DT.FONT_BASE}px;
            font-weight: {DT.WEIGHT_BOLD};
            font-family: {DT.FONT_FAMILY};
        """)
        account_layout.addWidget(email_label)

        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                border: none;
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_danger_hover()};
            }}
        """)
        logout_btn.clicked.connect(self.logout_requested.emit)
        account_layout.addWidget(logout_btn)
        layout.addWidget(account_group)

        # --- Model Sync Section ---
        sync_group = QGroupBox("Model Sync")
        sync_layout = QVBoxLayout(sync_group)
        sync_layout.setSpacing(DT.SPACE_MD)

        refresh_btn = QPushButton("🔄 Refresh Models from Cloud")
        refresh_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                border: none;
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_models_requested.emit)
        sync_layout.addWidget(refresh_btn)

        self.sync_status_label = QLabel("Last sync: Never")
        self.sync_status_label.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
        """)
        sync_layout.addWidget(self.sync_status_label)
        layout.addWidget(sync_group)

        # --- MT5 Connection Section ---
        mt5_group = QGroupBox("MT5 Connection")
        mt5_layout = QGridLayout(mt5_group)
        mt5_layout.setVerticalSpacing(DT.SPACE_MD)

        # Login
        label_style = f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};"
        mt5_layout.addWidget(QLabel("Login:", styleSheet=label_style), 0, 0)
        self.mt5_login = QLineEdit()
        self.mt5_login.setFixedHeight(DT.INPUT_HEIGHT)
        mt5_layout.addWidget(self.mt5_login, 0, 1)

        # Password
        mt5_layout.addWidget(QLabel("Password:", styleSheet=label_style), 1, 0)
        self.mt5_password = QLineEdit()
        self.mt5_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.mt5_password.setFixedHeight(DT.INPUT_HEIGHT)
        mt5_layout.addWidget(self.mt5_password, 1, 1)

        # Server
        mt5_layout.addWidget(QLabel("Server:", styleSheet=label_style), 2, 0)
        self.mt5_server = QLineEdit()
        self.mt5_server.setFixedHeight(DT.INPUT_HEIGHT)
        mt5_layout.addWidget(self.mt5_server, 2, 1)

        # Connect Button
        self.connect_btn = QPushButton("Connect to MT5")
        self.connect_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.SUCCESS};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                border: none;
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {DT.GLASS_HIGH};
            }}
        """)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        mt5_layout.addWidget(self.connect_btn, 3, 0, 1, 2)

        layout.addWidget(mt5_group)
        layout.addStretch()

    def _on_connect_clicked(self):
        self.connect_mt5_requested.emit({
            'login': self.mt5_login.text(),
            'password': self.mt5_password.text(),
            'server': self.mt5_server.text()
        })

    def update_sync_status(self, text: str):
        self.sync_status_label.setText(text)
        
    def set_mt5_status(self, connected: bool):
        if connected:
            self.connect_btn.setText("Connected ✓")
            self.connect_btn.setStyleSheet(f"background: {DT.SUCCESS}; color: white; border-radius: {DT.RADIUS_MD}px;")
            self.connect_btn.setEnabled(False)
        else:
            self.connect_btn.setText("Connect to MT5")
            self.connect_btn.setEnabled(True)
