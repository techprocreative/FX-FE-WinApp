"""
NexusTrade Main Window
Primary UI for the Windows connector application with Auto Trading
"""

import asyncio
from typing import Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame,
    QMessageBox, QStatusBar, QTableWidget, QTableWidgetItem,
    QComboBox, QDoubleSpinBox, QGroupBox, QGridLayout,
    QHeaderView, QLineEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

from core.config import Config
from core.mt5_client import MT5Client
from security.model_security import ModelSecurity
from trading.auto_trader import AutoTrader, Signal, TradingConfig
from api.server import set_mt5_client
from ui.strategy_builder import StrategyBuilderTab


class AutoTraderThread(QThread):
    """Background thread for auto trading loop"""
    signal_received = pyqtSignal(str, str, float)  # symbol, signal, confidence
    trade_executed = pyqtSignal(str, str, int, float)  # symbol, signal, ticket, volume
    error_occurred = pyqtSignal(str)
    
    def __init__(self, auto_trader: AutoTrader, interval: int = 60):
        super().__init__()
        self.auto_trader = auto_trader
        self.interval = interval
        self._running = False
    
    def run(self):
        """Run the trading loop"""
        self._running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Set callbacks
        self.auto_trader.on_signal_callback = lambda s, sig, c: self.signal_received.emit(s, sig.value, c)
        self.auto_trader.on_trade_callback = lambda s, sig, t, v: self.trade_executed.emit(s, sig.value, t, v)
        self.auto_trader.on_error_callback = lambda e: self.error_occurred.emit(e)
        
        self.auto_trader.running = True
        loop.run_until_complete(self.auto_trader.run_loop(self.interval))
    
    def stop(self):
        self._running = False
        self.auto_trader.running = False


class MainWindow(QMainWindow):
    """Main application window with auto trading support"""
    
    mt5_status_changed = pyqtSignal(bool)
    
    def __init__(self, config: Config, user_data: dict):
        super().__init__()
        self.config = config
        self.user_data = user_data  # Store user data from login
        self.mt5_client = MT5Client()
        self.model_security = ModelSecurity()
        self.auto_trader = AutoTrader(self.mt5_client, self.model_security)
        self.trader_thread: Optional[AutoTraderThread] = None
        
        # UI references for updates
        self.signal_labels: Dict[str, QLabel] = {}
        self.position_table: Optional[QTableWidget] = None
        self.stat_values: Dict[str, QLabel] = {}
        
        # Set MT5 client reference for API server
        set_mt5_client(self.mt5_client)
        
        self._setup_ui()
        self._setup_timers()
    
    def _setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("NexusTrade - Forex Trading Platform")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #1a1a2e;")
        main_layout.addWidget(self.content_stack, 1)
        
        # Add pages
        self._create_pages()
        
        # Status bar
        self._create_status_bar()
        
        # Apply styles
        self._apply_styles()
    
    def _create_sidebar(self) -> QFrame:
        """Create the sidebar navigation"""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-right: 1px solid #0f3460;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo
        logo_frame = QFrame()
        logo_frame.setFixedHeight(80)
        logo_layout = QHBoxLayout(logo_frame)
        
        logo_label = QLabel("NexusTrade")
        logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #e94560; padding: 20px;")
        logo_layout.addWidget(logo_label)
        
        layout.addWidget(logo_frame)
        
        # Navigation
        nav_items = [
            ("📊 Dashboard", 0),
            ("📈 Auto Trading", 1),
            ("🤖 ML Models", 2),
            ("🎯 Strategy Builder", 3),
            ("⚙️ Settings", 4),
        ]
        
        self.nav_buttons = []
        for name, index in nav_items:
            btn = self._create_nav_button(name, index)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addStretch()
        
        # MT5 status
        self.mt5_status_label = QLabel("MT5: Disconnected")
        self.mt5_status_label.setStyleSheet("color: #ff6b6b; padding: 15px; font-size: 11px;")
        layout.addWidget(self.mt5_status_label)
        
        # Auto trading status
        self.trading_status_label = QLabel("Auto: Stopped")
        self.trading_status_label.setStyleSheet("color: #888; padding: 15px; font-size: 11px;")
        layout.addWidget(self.trading_status_label)
        
        return sidebar
    
    def _create_nav_button(self, text: str, index: int) -> QPushButton:
        """Create a navigation button"""
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0a0a0;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0f3460;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #0f3460;
                color: #e94560;
                border-left: 3px solid #e94560;
            }
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._navigate_to(index))
        
        if index == 0:
            btn.setChecked(True)
        
        return btn
    
    def _navigate_to(self, index: int):
        """Navigate to a page"""
        self.content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def _create_pages(self):
        """Create content pages"""
        self.content_stack.addWidget(self._create_dashboard_page())
        self.content_stack.addWidget(self._create_trading_page())
        self.content_stack.addWidget(self._create_models_page())
        
        # Strategy Builder
        api_url = "https://your-app.vercel.app"  # TODO: Configure from settings
        self.strategy_builder = StrategyBuilderTab(api_url, self.user_data)
        self.strategy_builder.training_requested.connect(self._handle_training_request)
        self.content_stack.addWidget(self.strategy_builder)
        
        self.content_stack.addWidget(self._create_settings_page())
    
    def _create_dashboard_page(self) -> QWidget:
        """Dashboard with account stats"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Dashboard")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        # Stats cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        stats = [
            ("balance", "Account Balance", "$0.00", "#4ecca3"),
            ("profit", "Today's P/L", "$0.00", "#e94560"),
            ("positions", "Open Positions", "0", "#0f3460"),
            ("win_rate", "Win Rate", "0%", "#ffd369"),
        ]
        
        for key, title, value, color in stats:
            card, value_label = self._create_stat_card(title, value, color)
            self.stat_values[key] = value_label
            cards_layout.addWidget(card)
        
        layout.addLayout(cards_layout)
        
        # Positions table
        pos_group = QGroupBox("Open Positions")
        pos_group.setStyleSheet("""
            QGroupBox {
                color: #fff;
                font-size: 14px;
                border: 1px solid #0f3460;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        pos_layout = QVBoxLayout(pos_group)
        
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(7)
        self.position_table.setHorizontalHeaderLabels([
            "Symbol", "Type", "Volume", "Open Price", "Current", "Profit", "Time"
        ])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.position_table.setStyleSheet("""
            QTableWidget {
                background-color: #16213e;
                color: #fff;
                border: none;
            }
            QHeaderView::section {
                background-color: #0f3460;
                color: #fff;
                padding: 8px;
                border: none;
            }
        """)
        pos_layout.addWidget(self.position_table)
        
        layout.addWidget(pos_group)
        layout.addStretch()
        
        return page
    
    def _create_trading_page(self) -> QWidget:
        """Auto trading control page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Auto Trading")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        # Control panel
        control_group = QGroupBox("Trading Control")
        control_group.setStyleSheet("""
            QGroupBox {
                color: #fff;
                font-size: 14px;
                border: 1px solid #0f3460;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
        """)
        control_layout = QHBoxLayout(control_group)
        
        # Start/Stop buttons
        self.start_btn = QPushButton("▶ Start Auto Trading")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ecca3;
                color: #000;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3db892; }
            QPushButton:disabled { background-color: #666; color: #999; }
        """)
        self.start_btn.clicked.connect(self._start_auto_trading)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⬛ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: #fff;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #d63050; }
            QPushButton:disabled { background-color: #666; color: #999; }
        """)
        self.stop_btn.clicked.connect(self._stop_auto_trading)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        
        # Interval selector
        control_layout.addWidget(QLabel("Interval:"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(10, 300)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" sec")
        self.interval_spin.setStyleSheet("background: #16213e; color: #fff; padding: 5px;")
        control_layout.addWidget(self.interval_spin)
        
        layout.addWidget(control_group)
        
        # Signals panel
        signals_layout = QHBoxLayout()
        
        for symbol in ["BTCUSD", "XAUUSD"]:
            signal_card = self._create_signal_card(symbol)
            signals_layout.addWidget(signal_card)
        
        layout.addLayout(signals_layout)
        
        # Trade log
        log_group = QGroupBox("Recent Signals")
        log_group.setStyleSheet("""
            QGroupBox {
                color: #fff;
                font-size: 14px;
                border: 1px solid #0f3460;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Time", "Symbol", "Signal", "Confidence", "Action"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.setStyleSheet("""
            QTableWidget { background-color: #16213e; color: #fff; border: none; }
            QHeaderView::section { background-color: #0f3460; color: #fff; padding: 8px; border: none; }
        """)
        log_layout.addWidget(self.log_table)
        
        layout.addWidget(log_group)
        
        return page
    
    def _create_signal_card(self, symbol: str) -> QFrame:
        """Create a signal display card for a symbol"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-radius: 10px;
                border: 1px solid #0f3460;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Symbol header
        sym_label = QLabel(symbol)
        sym_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        sym_label.setStyleSheet("color: #fff;")
        layout.addWidget(sym_label)
        
        # Signal indicator
        signal_label = QLabel("WAITING")
        signal_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_label.setStyleSheet("color: #888; padding: 20px;")
        layout.addWidget(signal_label)
        self.signal_labels[symbol] = signal_label
        
        # Load model button
        load_btn = QPushButton(f"Load {symbol} Model")
        load_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #fff;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1a4a80; }
        """)
        load_btn.clicked.connect(lambda: self._load_model(symbol))
        layout.addWidget(load_btn)
        
        return card
    
    def _create_models_page(self) -> QWidget:
        """ML Models management page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("ML Models")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        # Model list
        models_group = QGroupBox("Available Models")
        models_group.setStyleSheet("QGroupBox { color: #fff; border: 1px solid #0f3460; border-radius: 8px; padding: 15px; }")
        models_layout = QVBoxLayout(models_group)
        
        # List models
        models = self.model_security.list_models()
        if models:
            for model_id in models:
                model_row = QHBoxLayout()
                model_row.addWidget(QLabel(f"📦 {model_id}"))
                model_row.addStretch()
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("background: #e94560; color: #fff; padding: 5px 10px; border-radius: 3px;")
                model_row.addWidget(delete_btn)
                models_layout.addLayout(model_row)
        else:
            models_layout.addWidget(QLabel("No models found. Train models first."))
        
        # Train button
        train_btn = QPushButton("🔧 Train New Models (BTC & XAU)")
        train_btn.setStyleSheet("""
            QPushButton {
                background-color: #4ecca3;
                color: #000;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin-top: 20px;
            }
        """)
        train_btn.clicked.connect(self._train_models)
        models_layout.addWidget(train_btn)
        
        layout.addWidget(models_group)
        layout.addStretch()
        
        return page
    
    def _create_settings_page(self) -> QWidget:
        """Settings page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel("Settings")
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        # MT5 connection
        mt5_group = QGroupBox("MT5 Connection")
        mt5_group.setStyleSheet("QGroupBox { color: #fff; border: 1px solid #0f3460; border-radius: 8px; padding: 15px; }")
        mt5_layout = QGridLayout(mt5_group)
        
        mt5_layout.addWidget(QLabel("Login:"), 0, 0)
        self.mt5_login = QLineEdit()
        self.mt5_login.setStyleSheet("background: #16213e; color: #fff; padding: 8px; border-radius: 4px;")
        mt5_layout.addWidget(self.mt5_login, 0, 1)
        
        mt5_layout.addWidget(QLabel("Password:"), 1, 0)
        self.mt5_password = QLineEdit()
        self.mt5_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.mt5_password.setStyleSheet("background: #16213e; color: #fff; padding: 8px; border-radius: 4px;")
        mt5_layout.addWidget(self.mt5_password, 1, 1)
        
        mt5_layout.addWidget(QLabel("Server:"), 2, 0)
        self.mt5_server = QLineEdit()
        self.mt5_server.setStyleSheet("background: #16213e; color: #fff; padding: 8px; border-radius: 4px;")
        mt5_layout.addWidget(self.mt5_server, 2, 1)
        
        connect_btn = QPushButton("Connect to MT5")
        connect_btn.setStyleSheet("background: #4ecca3; color: #000; padding: 10px; border-radius: 5px; font-weight: bold;")
        connect_btn.clicked.connect(self._connect_mt5)
        mt5_layout.addWidget(connect_btn, 3, 0, 1, 2)
        
        layout.addWidget(mt5_group)
        layout.addStretch()
        
        return page
    
    def _create_stat_card(self, title: str, value: str, color: str) -> tuple:
        """Create a statistics card, return (card, value_label)"""
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #16213e;
                border-radius: 10px;
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        return card, value_label
    
    def _create_status_bar(self):
        """Create the status bar"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("QStatusBar { background-color: #0f0f1a; color: #888; font-size: 11px; }")
        self.setStatusBar(status_bar)
        
        self.api_status = QLabel("API: Running on 127.0.0.1:8765")
        status_bar.addPermanentWidget(self.api_status)
    
    def _setup_timers(self):
        """Setup background timers"""
        # MT5 check
        self.mt5_timer = QTimer()
        self.mt5_timer.timeout.connect(self._check_mt5_connection)
        self.mt5_timer.start(5000)
        
        # Position update
        self.pos_timer = QTimer()
        self.pos_timer.timeout.connect(self._update_positions)
        self.pos_timer.start(2000)
    
    def _check_mt5_connection(self):
        """Check MT5 connection status"""
        is_connected = self.mt5_client.is_connected
        
        if is_connected:
            self.mt5_status_label.setText("MT5: Connected ✓")
            self.mt5_status_label.setStyleSheet("color: #4ecca3; padding: 15px; font-size: 11px;")
        else:
            self.mt5_status_label.setText("MT5: Disconnected")
            self.mt5_status_label.setStyleSheet("color: #ff6b6b; padding: 15px; font-size: 11px;")
        
        self.mt5_status_changed.emit(is_connected)
    
    def _update_positions(self):
        """Update positions table and stats"""
        if not self.mt5_client.is_connected:
            return
        
        # Update account stats
        account = self.mt5_client.get_account_info()
        if account:
            self.stat_values['balance'].setText(f"${account.balance:,.2f}")
            self.stat_values['profit'].setText(f"${account.profit:,.2f}")
            if account.profit >= 0:
                self.stat_values['profit'].setStyleSheet("color: #4ecca3; font-size: 20px; font-weight: bold;")
            else:
                self.stat_values['profit'].setStyleSheet("color: #e94560; font-size: 20px; font-weight: bold;")
        
        # Update positions table
        positions = self.mt5_client.get_positions()
        self.stat_values['positions'].setText(str(len(positions)))
        
        self.position_table.setRowCount(len(positions))
        for i, pos in enumerate(positions):
            self.position_table.setItem(i, 0, QTableWidgetItem(pos.symbol))
            self.position_table.setItem(i, 1, QTableWidgetItem(pos.type.upper()))
            self.position_table.setItem(i, 2, QTableWidgetItem(f"{pos.volume}"))
            self.position_table.setItem(i, 3, QTableWidgetItem(f"{pos.open_price:.5f}"))
            self.position_table.setItem(i, 4, QTableWidgetItem(f"{pos.current_price:.5f}"))
            
            profit_item = QTableWidgetItem(f"${pos.profit:.2f}")
            profit_item.setForeground(QColor("#4ecca3" if pos.profit >= 0 else "#e94560"))
            self.position_table.setItem(i, 5, profit_item)
            
            self.position_table.setItem(i, 6, QTableWidgetItem(pos.open_time.strftime("%H:%M:%S")))
    
    def _connect_mt5(self):
        """Connect to MT5"""
        login = self.mt5_login.text()
        password = self.mt5_password.text()
        server = self.mt5_server.text()
        
        if not all([login, password, server]):
            QMessageBox.warning(self, "Error", "Please fill all MT5 connection fields")
            return
        
        try:
            success = self.mt5_client.login(int(login), password, server)
            if success:
                QMessageBox.information(self, "Success", "Connected to MT5!")
            else:
                QMessageBox.warning(self, "Error", "Failed to connect to MT5")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {e}")
    
    def _load_model(self, symbol: str):
        """Load model for symbol"""
        models = self.model_security.list_models()
        symbol_models = [m for m in models if symbol.lower() in m.lower()]
        
        if not symbol_models:
            QMessageBox.warning(self, "No Model", f"No model found for {symbol}. Train one first.")
            return
        
        # Load latest model
        model_id = sorted(symbol_models)[-1]
        config = TradingConfig(
            symbol=symbol,
            timeframe="M15",
            volume=0.01,
            risk_percent=1.0,
            confidence_threshold=0.6
        )
        
        if self.auto_trader.load_model(model_id, symbol, config):
            self.signal_labels[symbol].setText("LOADED")
            self.signal_labels[symbol].setStyleSheet("color: #4ecca3; padding: 20px;")
            QMessageBox.information(self, "Success", f"Model loaded for {symbol}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load model for {symbol}")
    
    def _train_models(self):
        """Train demo models"""
        from ai.model_trainer import train_demo_models
        
        reply = QMessageBox.question(
            self, "Train Models",
            "This will train ML models for BTCUSD and XAUUSD.\nThis may take a few minutes. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                results = train_demo_models()
                msg = "Training Complete!\n\n"
                for symbol, data in results.items():
                    if 'error' in data:
                        msg += f"{symbol}: Failed - {data['error']}\n"
                    else:
                        msg += f"{symbol}: {data['metrics']['accuracy']:.1%} accuracy\n"
                QMessageBox.information(self, "Training Complete", msg)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Training failed: {e}")
    
    def _start_auto_trading(self):
        """Start auto trading"""
        if not self.mt5_client.is_connected:
            QMessageBox.warning(self, "Error", "Please connect to MT5 first")
            return
        
        if not self.auto_trader.models:
            QMessageBox.warning(self, "Error", "Please load at least one model first")
            return
        
        interval = int(self.interval_spin.value())
        
        self.trader_thread = AutoTraderThread(self.auto_trader, interval)
        self.trader_thread.signal_received.connect(self._on_signal)
        self.trader_thread.trade_executed.connect(self._on_trade)
        self.trader_thread.error_occurred.connect(self._on_error)
        self.trader_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.trading_status_label.setText("Auto: RUNNING")
        self.trading_status_label.setStyleSheet("color: #4ecca3; padding: 15px; font-size: 11px;")
    
    def _stop_auto_trading(self):
        """Stop auto trading"""
        if self.trader_thread:
            self.trader_thread.stop()
            self.trader_thread.wait()
            self.trader_thread = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.trading_status_label.setText("Auto: Stopped")
        self.trading_status_label.setStyleSheet("color: #888; padding: 15px; font-size: 11px;")
    
    def _on_signal(self, symbol: str, signal: str, confidence: float):
        """Handle signal from auto trader"""
        if symbol in self.signal_labels:
            label = self.signal_labels[symbol]
            label.setText(f"{signal.upper()}\n{confidence:.0%}")
            
            if signal == "buy":
                label.setStyleSheet("color: #4ecca3; padding: 20px; font-size: 24px;")
            elif signal == "sell":
                label.setStyleSheet("color: #e94560; padding: 20px; font-size: 24px;")
            else:
                label.setStyleSheet("color: #888; padding: 20px; font-size: 24px;")
        
        # Add to log
        row = self.log_table.rowCount()
        self.log_table.insertRow(0)
        self.log_table.setItem(0, 0, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        self.log_table.setItem(0, 1, QTableWidgetItem(symbol))
        self.log_table.setItem(0, 2, QTableWidgetItem(signal.upper()))
        self.log_table.setItem(0, 3, QTableWidgetItem(f"{confidence:.0%}"))
        self.log_table.setItem(0, 4, QTableWidgetItem("-"))
        
        # Keep only last 50 rows
        while self.log_table.rowCount() > 50:
            self.log_table.removeRow(self.log_table.rowCount() - 1)
    
    def _on_trade(self, symbol: str, signal: str, ticket: int, volume: float):
        """Handle trade execution"""
        # Update first row action
        if self.log_table.rowCount() > 0:
            self.log_table.setItem(0, 4, QTableWidgetItem(f"#{ticket}"))
    
    def _on_error(self, error: str):
        """Handle error from auto trader"""
        self.statusBar().showMessage(f"Error: {error}", 5000)
    
    def _apply_styles(self):
        """Apply global styles"""
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1a2e; }
            QLabel { color: #ffffff; }
        """)
    
    def closeEvent(self, event):
        """Handle window close"""
        # Stop auto trading
        if self.trader_thread:
            self.trader_thread.stop()
            self.trader_thread.wait()
        
        reply = QMessageBox.question(
            self, "Exit NexusTrade", "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.mt5_client.is_connected:
                self.mt5_client.logout()
            event.accept()
        else:
            event.ignore()
    
    def _handle_training_request(self, config: dict, symbol: str, model_name: str):
        """Handle custom model training request from Strategy Builder"""
        logger.info(f"Training request: {model_name} for {symbol}")
        
        # Import here to avoid circular dependency
        from ai.custom_trainer import CustomModelTrainer
        
        # Create trainer with progress callback
        def on_progress(message: str, percent: int):
            self.strategy_builder.update_progress(message, percent)
        
        trainer = CustomModelTrainer(config, symbol, model_name, on_progress)
        
        # Start training in background thread
        import threading
        
        def train_thread():
            try:
                result = trainer.train()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Training Complete",
                    f"Model '{model_name}' trained successfully!\n\n"
                    f"Win Rate: {result.get('win_rate', 0):.1f}%\n"
                    f"Kelly Fraction: {result.get('kelly_fraction', 0):.2f}\n"
                    f"Model ID: {result.get('model_id', 'N/A')}"
                )
                
            except Exception as e:
                logger.exception(f"Training failed: {e}")
                QMessageBox.critical(
                    self,
                    "Training Failed",
                    f"Failed to train model:\n{str(e)}"
                )
        
        thread = threading.Thread(target=train_thread, daemon=True)
        thread.start()
