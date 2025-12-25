from typing import Dict, Any, Optional, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QLineEdit, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui.design_system import DesignTokens as DT, StyleSheets
from core.config_manager import ConfigManager, MT5ConfigData

if TYPE_CHECKING:
    from core.mt5_client import MT5Client


class SettingsPage(QWidget):
    """
    Settings Page
    Manage Account, MT5 Connection, and Supabase Sync.
    """
    logout_requested = pyqtSignal()
    refresh_models_requested = pyqtSignal()
    connect_mt5_requested = pyqtSignal(dict) # login, password, server
    
    def __init__(self, user_data: Dict[str, Any], config_manager: Optional[ConfigManager] = None, 
                 mt5_client: Optional['MT5Client'] = None):
        super().__init__()
        self.user_data = user_data
        self._config_manager = config_manager or ConfigManager()
        self._mt5_client = mt5_client
        
        # Account info update timer
        self._account_update_timer: Optional[QTimer] = None
        
        self._setup_ui()
        self._load_saved_config()
        
        # Start account info updates if MT5 client is provided
        if self._mt5_client:
            self._start_account_updates()

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

        # --- MT5 Account Info Section ---
        self._create_account_info_section(layout)

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
                background: {DT.SUCCESS_DARK};
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

    def _load_saved_config(self):
        """Load saved MT5 configuration (excluding password)"""
        mt5_config = self._config_manager.get_mt5_config()
        
        if mt5_config.login is not None:
            self.mt5_login.setText(str(mt5_config.login))
        
        if mt5_config.server:
            self.mt5_server.setText(mt5_config.server)
        
        # Load last sync time
        last_sync = self._config_manager.get_last_sync_time()
        if last_sync:
            self.sync_status_label.setText(f"Last sync: {last_sync}")

    def save_mt5_config(self, login: int, server: str):
        """
        Save MT5 configuration after successful connection.
        Password is NOT saved for security.
        
        Args:
            login: MT5 account login number
            server: MT5 server name
        """
        mt5_config = MT5ConfigData(
            login=login,
            server=server
        )
        self._config_manager.set_mt5_config(mt5_config)

    def update_sync_status(self, text: str):
        self.sync_status_label.setText(text)
        # Save sync time to config
        if "Last sync:" in text:
            self._config_manager.set_last_sync_time(text.replace("Last sync: ", ""))
        
    def set_mt5_status(self, connected: bool):
        if connected:
            self.connect_btn.setText("Connected ✓")
            self.connect_btn.setStyleSheet(f"background: {DT.SUCCESS}; color: white; border-radius: {DT.RADIUS_MD}px;")
            self.connect_btn.setEnabled(False)
            # Show account info section
            self._account_info_group.setVisible(True)
            # Start real-time updates
            self._start_account_updates()
        else:
            self.connect_btn.setText("Connect to MT5")
            self.connect_btn.setEnabled(True)
            # Hide account info section
            self._account_info_group.setVisible(False)
            # Stop updates
            self._stop_account_updates()

    def _create_account_info_section(self, parent_layout: QVBoxLayout):
        """Create the MT5 account info display section"""
        self._account_info_group = QGroupBox("MT5 Account Info")
        self._account_info_group.setVisible(False)  # Hidden until connected
        
        info_layout = QGridLayout(self._account_info_group)
        info_layout.setVerticalSpacing(DT.SPACE_MD)
        info_layout.setHorizontalSpacing(DT.SPACE_XL)
        
        label_style = f"""
            color: {DT.TEXT_SECONDARY};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
        """
        value_style = f"""
            color: {DT.TEXT_PRIMARY};
            font-size: {DT.FONT_LG}px;
            font-weight: {DT.WEIGHT_BOLD};
            font-family: {DT.FONT_FAMILY};
        """
        
        # Balance
        info_layout.addWidget(QLabel("Balance:", styleSheet=label_style), 0, 0)
        self._balance_label = QLabel("--")
        self._balance_label.setStyleSheet(value_style)
        info_layout.addWidget(self._balance_label, 0, 1)
        
        # Equity
        info_layout.addWidget(QLabel("Equity:", styleSheet=label_style), 0, 2)
        self._equity_label = QLabel("--")
        self._equity_label.setStyleSheet(value_style)
        info_layout.addWidget(self._equity_label, 0, 3)
        
        # Margin
        info_layout.addWidget(QLabel("Margin:", styleSheet=label_style), 1, 0)
        self._margin_label = QLabel("--")
        self._margin_label.setStyleSheet(value_style)
        info_layout.addWidget(self._margin_label, 1, 1)
        
        # Leverage
        info_layout.addWidget(QLabel("Leverage:", styleSheet=label_style), 1, 2)
        self._leverage_label = QLabel("--")
        self._leverage_label.setStyleSheet(value_style)
        info_layout.addWidget(self._leverage_label, 1, 3)
        
        parent_layout.addWidget(self._account_info_group)

    def set_mt5_client(self, mt5_client: 'MT5Client'):
        """Set the MT5 client reference for account info updates"""
        self._mt5_client = mt5_client
        if mt5_client and mt5_client.is_connected:
            self._start_account_updates()

    def _start_account_updates(self):
        """Start the real-time account info update timer"""
        if self._account_update_timer is None:
            self._account_update_timer = QTimer(self)
            self._account_update_timer.timeout.connect(self._update_account_info)
        
        # Update immediately
        self._update_account_info()
        
        # Then update every 5 seconds
        self._account_update_timer.start(5000)

    def _stop_account_updates(self):
        """Stop the account info update timer"""
        if self._account_update_timer:
            self._account_update_timer.stop()

    def _update_account_info(self):
        """Fetch and display current account info from MT5"""
        if not self._mt5_client or not self._mt5_client.is_connected:
            return
        
        account_info = self._mt5_client.get_account_info()
        if account_info:
            currency = account_info.currency
            
            # Format balance with currency
            self._balance_label.setText(f"{account_info.balance:,.2f} {currency}")
            
            # Format equity with color based on profit/loss
            equity_color = DT.SUCCESS if account_info.equity >= account_info.balance else DT.DANGER
            self._equity_label.setText(f"{account_info.equity:,.2f} {currency}")
            self._equity_label.setStyleSheet(f"""
                color: {equity_color};
                font-size: {DT.FONT_LG}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-family: {DT.FONT_FAMILY};
            """)
            
            # Format margin
            self._margin_label.setText(f"{account_info.margin:,.2f} {currency}")
            
            # Format leverage
            self._leverage_label.setText(f"1:{account_info.leverage}")
