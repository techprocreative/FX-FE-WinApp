"""
NexusTrade Main Window
Primary UI for the Windows connector application with Auto Trading

Performance optimization: Heavy ML imports (AutoTrader, ModelSecurity) are 
lazy-loaded in __init__ to speed up window display.
"""

import asyncio
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame,
    QMessageBox, QStatusBar, QTableWidget, QTableWidgetItem,
    QComboBox, QDoubleSpinBox, QGroupBox, QGridLayout,
    QHeaderView, QLineEdit, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

from core.config import Config
from core.mt5_client import MT5Client
from api.server import set_mt5_client
from ui.strategy_builder import StrategyBuilderTab
from ui.design_system import DesignTokens as DT, StyleSheets
from loguru import logger

# Type hints only (no import at runtime)
if TYPE_CHECKING:
    from security.model_security import ModelSecurity
    from trading.auto_trader import AutoTrader, Signal, TradingConfig


class AutoTraderThread(QThread):
    """Background thread for auto trading loop"""
    signal_received = pyqtSignal(str, str, float)  # symbol, signal, confidence
    trade_executed = pyqtSignal(str, str, int, float)  # symbol, signal, ticket, volume
    trade_closed = pyqtSignal(int, float)  # ticket, profit
    error_occurred = pyqtSignal(str)
    
    def __init__(self, auto_trader: 'AutoTrader', interval: int = 60):
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
        self.auto_trader.on_close_callback = lambda t, p: self.trade_closed.emit(t, p)
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

        # PERFORMANCE: Defer heavy ML modules - only load when actually needed
        # These will be lazy-loaded on first use in Trading/Models pages
        self.model_security = None  # Loaded in _ensure_ml_loaded()
        self.auto_trader = None  # Loaded in _ensure_ml_loaded()
        self.trader_thread: Optional['AutoTraderThread'] = None

        # PERFORMANCE: Defer Supabase sync - only load when Models page is accessed
        self.supabase_sync = None  # Loaded in _ensure_supabase_loaded()
        self._supabase_config = {
            'url': config.supabase.url,
            'anon_key': config.supabase.anon_key,
            'user_id': user_data['id'],
            'access_token': user_data.get('access_token')
        }

        # UI references for updates
        self.signal_labels: Dict[str, QLabel] = {}
        self.position_table: Optional[QTableWidget] = None
        self.stat_values: Dict[str, QLabel] = {}

        # Trade log tracking: ticket -> row_index mapping
        self.trade_log_tickets: Dict[int, int] = {}

        # PERFORMANCE: Lazy-loaded pages (created on first navigation)
        self._pages_loaded = {
            'dashboard': False,
            'trading': False,
            'models': False,
            'strategy': False,
            'settings': False
        }

        # Set MT5 client reference for API server
        set_mt5_client(self.mt5_client)

        self._setup_ui()
        self._setup_timers()

    def _ensure_ml_loaded(self):
        """Lazy-load ML modules on first use (PERFORMANCE OPTIMIZATION)"""
        if self.model_security is None:
            logger.info("Loading ML modules (first use)...")
            from security.model_security import ModelSecurity
            from trading.auto_trader import AutoTrader

            self.model_security = ModelSecurity()
            self.auto_trader = AutoTrader(self.mt5_client, self.model_security)
            logger.info("✓ ML modules loaded")

    def _ensure_supabase_loaded(self):
        """Lazy-load Supabase sync on first use (PERFORMANCE OPTIMIZATION)"""
        if self.supabase_sync is None:
            logger.info("Loading Supabase sync (first use)...")
            from core.supabase_sync import SupabaseModelSync

            self.supabase_sync = SupabaseModelSync(
                self._supabase_config['url'],
                self._supabase_config['anon_key'],
                self._supabase_config['user_id'],
                access_token=self._supabase_config['access_token']
            )
            logger.info("✓ Supabase sync loaded")

            # Trigger model sync in background
            import threading
            def fetch_models_thread():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._fetch_and_sync_models())
                    QTimer.singleShot(0, self._refresh_models_page_ui)
                except Exception as e:
                    logger.error(f"Failed to fetch models: {e}")
                finally:
                    loop.close()
            threading.Thread(target=fetch_models_thread, daemon=True).start()

    
    def _setup_ui(self):
        """Setup the main UI with design system"""
        self.setWindowTitle("NexusTrade - Forex Trading Platform")

        # Set minimum size (absolute minimum for usability)
        self.setMinimumSize(DT.MAIN_MIN_WIDTH, DT.MAIN_MIN_HEIGHT)

        # Set responsive initial size based on screen
        responsive_w, responsive_h = DT.get_responsive_window_size()
        self.resize(responsive_w, responsive_h)

        # Center window on screen
        self._center_on_screen()

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
        main_layout.addWidget(self.content_stack, 1)

        # Add pages
        self._create_pages()

        # Status bar
        self._create_status_bar()

        # Apply global styles
        self._apply_styles()
    
    def _create_sidebar(self) -> QFrame:
        """Create the sidebar navigation with design system"""
        sidebar = QFrame()
        sidebar.setFixedWidth(DT.SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {StyleSheets.gradient_sidebar()};
                border-right: 1px solid {DT.BORDER_SUBTLE};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo section
        logo_frame = QFrame()
        logo_frame.setFixedHeight(DT.SIDEBAR_LOGO_HEIGHT)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {DT.BORDER_SUBTLE};
            }}
        """)
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(DT.SPACE_XL, 0, DT.SPACE_XL, 0)

        logo_label = QLabel("⚡ NexusTrade")
        logo_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL, DT.WEIGHT_BOLD))
        logo_label.setStyleSheet(f"""
            color: {DT.PRIMARY};
            background: transparent;
        """)
        logo_layout.addWidget(logo_label)

        layout.addWidget(logo_frame)

        # Navigation section
        nav_frame = QFrame()
        nav_frame.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(DT.SPACE_MD, DT.SPACE_LG, DT.SPACE_MD, DT.SPACE_LG)
        nav_layout.setSpacing(DT.SPACE_SM)

        nav_items = [
            ("📊", "Dashboard", 0),
            ("📈", "Auto Trading", 1),
            ("🤖", "ML Models", 2),
            ("🎯", "Strategy Builder", 3),
            ("⚙️", "Settings", 4),
        ]

        self.nav_buttons = []
        for icon, name, index in nav_items:
            btn = self._create_nav_button(icon, name, index)
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addWidget(nav_frame)
        layout.addStretch()

        # Status section
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARK};
                border-top: 1px solid {DT.BORDER_SUBTLE};
                padding: {DT.SPACE_BASE}px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(DT.SPACE_LG, DT.SPACE_BASE, DT.SPACE_LG, DT.SPACE_BASE)
        status_layout.setSpacing(DT.SPACE_MD)

        # MT5 status indicator
        mt5_row = QHBoxLayout()
        mt5_indicator = QLabel("●")
        mt5_indicator.setStyleSheet(f"color: {DT.DANGER}; font-size: {DT.FONT_XS}px;")
        mt5_row.addWidget(mt5_indicator)
        self.mt5_status_label = QLabel("MT5: Disconnected")
        self.mt5_status_label.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_SM}px;
            font-weight: {DT.WEIGHT_MEDIUM};
            font-family: {DT.FONT_FAMILY};
        """)
        mt5_row.addWidget(self.mt5_status_label)
        mt5_row.addStretch()
        status_layout.addLayout(mt5_row)

        self.mt5_indicator = mt5_indicator

        # Auto trading status indicator
        trading_row = QHBoxLayout()
        trading_indicator = QLabel("●")
        trading_indicator.setStyleSheet(f"color: {DT.TEXT_PLACEHOLDER}; font-size: {DT.FONT_XS}px;")
        trading_row.addWidget(trading_indicator)
        self.trading_status_label = QLabel("Auto: Stopped")
        self.trading_status_label.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_SM}px;
            font-weight: {DT.WEIGHT_MEDIUM};
            font-family: {DT.FONT_FAMILY};
        """)
        trading_row.addWidget(self.trading_status_label)
        trading_row.addStretch()
        status_layout.addLayout(trading_row)

        self.trading_indicator = trading_indicator

        layout.addWidget(status_frame)

        return sidebar
    
    def _create_nav_button(self, icon: str, name: str, index: int) -> QPushButton:
        """Create a navigation button with design system"""
        btn = QPushButton(f"  {icon}   {name}")
        btn.setFixedHeight(DT.NAV_BUTTON_HEIGHT)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {DT.TEXT_DISABLED};
                border: none;
                border-radius: {DT.RADIUS_LG}px;
                text-align: left;
                padding-left: {DT.SPACE_BASE}px;
                font-size: {DT.FONT_BASE}px;
                font-weight: {DT.WEIGHT_MEDIUM};
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: rgba(6, 182, 212, 0.1);
                color: {DT.TEXT_SECONDARY};
            }}
            QPushButton:checked {{
                background: {StyleSheets.gradient_primary()};
                color: white;
                border-left: 3px solid {DT.PRIMARY};
                font-weight: {DT.WEIGHT_SEMIBOLD};
            }}
        """)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._navigate_to(index))

        if index == 0:
            btn.setChecked(True)

        return btn
    
    def _navigate_to(self, index: int):
        """Navigate to a page - lazy load if not yet created (PERFORMANCE)"""
        # Lazy load pages on first navigation
        page_map = {
            0: ('dashboard', None),
            1: ('trading', self._create_trading_page),
            2: ('models', self._create_models_page),
            3: ('strategy', self._create_strategy_page),
            4: ('settings', self._create_settings_page)
        }

        if index in page_map:
            page_key, create_func = page_map[index]

            # Load page if not yet loaded
            if not self._pages_loaded[page_key] and create_func:
                logger.info(f"Lazy-loading {page_key} page...")

                # Ensure dependencies are loaded for specific pages
                if page_key == 'trading':
                    self._ensure_ml_loaded()
                elif page_key == 'models':
                    self._ensure_ml_loaded()
                    self._ensure_supabase_loaded()
                elif page_key == 'strategy':
                    # Strategy builder needs to be initialized
                    pass

                # Create and replace placeholder
                new_page = create_func()
                old_widget = self.content_stack.widget(index)
                if old_widget:
                    self.content_stack.removeWidget(old_widget)
                    old_widget.deleteLater()
                else:
                    logger.warning(f"No widget found at index {index} for {page_key} page (stack has {self.content_stack.count()} widgets)")
                self.content_stack.insertWidget(index, new_page)
                self._pages_loaded[page_key] = True
                logger.info(f"✓ {page_key} page loaded")

        self.content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def _create_pages(self):
        """Create content pages - LAZY LOADED for performance"""
        # PERFORMANCE: Only create Dashboard initially (index 0, visible on startup)
        # Other pages created on first navigation
        self.content_stack.addWidget(self._create_dashboard_page())
        self._pages_loaded['dashboard'] = True

        # Add placeholder widgets for other pages (will be replaced on first navigation)
        for _ in range(4):  # Trading, Models, Strategy, Settings
            placeholder = QWidget()
            self.content_stack.addWidget(placeholder)
    
    def _create_dashboard_page(self) -> QWidget:
        """Dashboard with account stats"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        layout.setSpacing(DT.SPACE_LG)

        # Header
        header = QLabel("Dashboard")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)

        # Stats cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(DT.SPACE_LG)

        stats = [
            ("balance", "Account Balance", "$0.00", DT.SUCCESS),
            ("profit", "Today's P/L", "$0.00", DT.DANGER),
            ("positions", "Open Positions", "0", DT.PRIMARY),
            ("win_rate", "Win Rate", "0%", DT.WARNING),
        ]

        for key, title, value, color in stats:
            card, value_label = self._create_stat_card(title, value, color)
            self.stat_values[key] = value_label
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # Positions table - inherits from global stylesheet
        pos_group = QGroupBox("Open Positions")
        pos_layout = QVBoxLayout(pos_group)

        self.position_table = QTableWidget()
        self.position_table.setColumnCount(7)
        self.position_table.setHorizontalHeaderLabels([
            "Symbol", "Type", "Volume", "Open Price", "Current", "Profit", "Time"
        ])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pos_layout.addWidget(self.position_table)

        layout.addWidget(pos_group)
        layout.addStretch()

        return page
    
    def _create_trading_page(self) -> QWidget:
        """Auto trading control page - Enhanced dashboard"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        layout.setSpacing(DT.SPACE_LG)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("🤖 Auto Trading")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Session timer label (will be updated)
        self.session_timer_label = QLabel("⏱ Ready")
        self.session_timer_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_SEMIBOLD))
        self.session_timer_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")
        header_layout.addWidget(self.session_timer_label)

        layout.addLayout(header_layout)

        # Statistics Cards Row
        from ui.components.stat_card import StatCard

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(DT.SPACE_LG)

        # Create stat cards (will be updated dynamically)
        self.stat_card_trades = StatCard("📊", "TRADES TODAY", "0")
        self.stat_card_winrate = StatCard("🎯", "WIN RATE", "0%")
        self.stat_card_profit = StatCard("💰", "P&L TODAY", "$0.00")
        self.stat_card_positions = StatCard("📈", "ACTIVE POS", "0")

        stats_layout.addWidget(self.stat_card_trades)
        stats_layout.addWidget(self.stat_card_winrate)
        stats_layout.addWidget(self.stat_card_profit)
        stats_layout.addWidget(self.stat_card_positions)
        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        # Control panel
        control_group = QGroupBox("Trading Control")
        control_layout = QHBoxLayout(control_group)

        # Start/Stop buttons
        self.start_btn = QPushButton("▶ Start Auto Trading")
        self.start_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                border: none;
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_BASE}px {DT.SPACE_2XL}px;
                color: white;
                font-size: {DT.FONT_BASE}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
            QPushButton:disabled {{
                background: {DT.GLASS_MEDIUM};
                color: {DT.TEXT_DISABLED};
            }}
        """)
        self.start_btn.clicked.connect(self._start_auto_trading)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⬛ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
        self.stop_btn.setStyleSheet(StyleSheets.danger_button())
        self.stop_btn.clicked.connect(self._stop_auto_trading)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()

        # Interval selector
        interval_label = QLabel("Interval:")
        interval_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};")
        control_layout.addWidget(interval_label)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(10, 300)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" sec")
        control_layout.addWidget(self.interval_spin)

        layout.addWidget(control_group)

        # Enhanced Signal Cards
        from ui.components.signal_card import SignalCard

        signals_layout = QHBoxLayout()
        signals_layout.setSpacing(DT.SPACE_LG)

        # Store SignalCard instances
        self.signal_cards = {}

        for symbol in ["BTCUSD", "XAUUSD"]:
            signal_card = SignalCard(symbol)
            signal_card.load_model_clicked.connect(lambda s=symbol: self._load_model(s))
            self.signal_cards[symbol] = signal_card
            signals_layout.addWidget(signal_card)

        signals_layout.addStretch()
        layout.addLayout(signals_layout)

        # Trade log
        log_group = QGroupBox("📈 Recent Signals & Trades")
        log_layout = QVBoxLayout(log_group)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(7)
        self.log_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Signal", "Confidence", "Action", "P&L", "Status"
        ])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        log_layout.addWidget(self.log_table)

        layout.addWidget(log_group)

        # Auto-load available models for trading symbols
        QTimer.singleShot(100, self._auto_load_models)

        # Setup session timer update
        self.trading_session_start = None
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        self.session_timer.start(1000)  # Update every second

        return page
    
    def _create_signal_card(self, symbol: str) -> QFrame:
        """Create a signal display card for a symbol - Modern style"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {DT.GLASS_MEDIUM}, stop:1 {DT.GLASS_DARKEST}
                );
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_2XL}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(DT.SPACE_XL, DT.SPACE_XL, DT.SPACE_XL, DT.SPACE_XL)
        layout.setSpacing(DT.SPACE_BASE)

        # Symbol header with icon
        sym_label = QLabel(f"📊 {symbol}")
        sym_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL, DT.WEIGHT_BOLD))
        sym_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(sym_label)

        # Signal indicator
        signal_label = QLabel("WAITING")
        signal_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_4XL, DT.WEIGHT_BOLD))
        signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signal_label.setStyleSheet(f"""
            color: {DT.TEXT_PLACEHOLDER};
            background: {DT.GLASS_DARKEST};
            border-radius: {DT.RADIUS_XL}px;
            padding: {DT.SPACE_XL}px;
        """)
        layout.addWidget(signal_label)
        self.signal_labels[symbol] = signal_label

        # Load model button
        load_btn = QPushButton(f"🔄 Load {symbol} Model")
        load_btn.setObjectName("loadModelBtn")
        load_btn.clicked.connect(lambda: self._load_model(symbol))
        layout.addWidget(load_btn)

        return card
    
    def _create_models_page(self) -> QWidget:
        """ML Models management page - Enhanced dashboard style"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        layout.setSpacing(DT.SPACE_LG)

        # Header with action button
        header_layout = QHBoxLayout()

        header = QLabel("📦 ML Models")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        header_layout.addWidget(header)

        header_layout.addStretch()

        # Train button in header
        train_btn = QPushButton("🔧 Train New Models")
        train_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        train_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                color: white;
                padding: {DT.SPACE_SM}px {DT.SPACE_XL}px;
                border-radius: {DT.RADIUS_MD}px;
                font-size: {DT.FONT_SM}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-family: {DT.FONT_FAMILY};
                border: none;
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
        """)
        train_btn.clicked.connect(self._train_models)
        header_layout.addWidget(train_btn)

        layout.addLayout(header_layout)

        # List models with metadata
        models = self.model_security.list_models_with_metadata()
        logger.info(f"Creating models page - found {len(models)} models")

        # Summary stats cards
        if models:
            stats_layout = QHBoxLayout()
            stats_layout.setSpacing(DT.SPACE_LG)

            # Import StatCard
            from ui.components.stat_card import StatCard

            # Total models card
            total_card = StatCard("📦", "TOTAL MODELS", str(len(models)))
            stats_layout.addWidget(total_card)

            # Average accuracy card
            avg_accuracy = sum(m.get('accuracy', 0) for m in models) / len(models)
            avg_accuracy_pct = avg_accuracy * 100 if avg_accuracy <= 1.0 else avg_accuracy
            accuracy_card = StatCard("🎯", "AVG ACCURACY", f"{avg_accuracy_pct:.1f}%")
            stats_layout.addWidget(accuracy_card)

            # Active models card (models currently loaded in trading)
            active_count = sum(1 for m in models if m.get('is_active', False))
            active_card = StatCard("🟢", "ACTIVE", str(active_count))
            stats_layout.addWidget(active_card)

            stats_layout.addStretch()
            layout.addLayout(stats_layout)

        # Models grid/list
        models_group = QGroupBox("Your Models")
        models_layout = QVBoxLayout(models_group)
        models_layout.setSpacing(DT.SPACE_BASE)

        if models:
            # Import ModelCard
            from ui.components.model_card import ModelCard

            # Check which models are currently loaded in AutoTrader
            loaded_models = set()
            if self.auto_trader and hasattr(self.auto_trader, 'models'):
                for symbol, model_info in self.auto_trader.models.items():
                    loaded_models.add(model_info.model_id)

            # Create ModelCard for each model
            for model_info in models:
                # Mark as active if loaded in trader
                model_info['is_active'] = model_info['model_id'] in loaded_models

                model_card = ModelCard(model_info)

                # Connect signals
                model_card.delete_clicked.connect(self._handle_model_delete)
                model_card.details_clicked.connect(self._handle_model_details)
                model_card.load_clicked.connect(self._handle_model_load_from_card)

                models_layout.addWidget(model_card)

        else:
            # Empty state
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.setSpacing(DT.SPACE_LG)

            empty_icon = QLabel("📦")
            empty_icon.setFont(QFont(DT.FONT_FAMILY.strip("'"), 72))
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_title = QLabel("No Models Found")
            empty_title.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_2XL, DT.WEIGHT_BOLD))
            empty_title.setStyleSheet(f"color: {DT.TEXT_PRIMARY};")
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_title)

            empty_desc = QLabel("Train your first ML model to start automated trading")
            empty_desc.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE))
            empty_desc.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")
            empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_desc)

            # CTA button
            empty_train_btn = QPushButton("🔧 Train Models Now")
            empty_train_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
            empty_train_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {StyleSheets.gradient_primary()};
                    color: white;
                    padding: {DT.SPACE_MD}px {DT.SPACE_2XL}px;
                    border-radius: {DT.RADIUS_LG}px;
                    font-size: {DT.FONT_BASE}px;
                    font-weight: {DT.WEIGHT_BOLD};
                    border: none;
                }}
                QPushButton:hover {{
                    background: {StyleSheets.gradient_primary_hover()};
                }}
            """)
            empty_train_btn.clicked.connect(self._train_models)
            empty_layout.addWidget(empty_train_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            models_layout.addWidget(empty_widget)

        models_layout.addStretch()
        layout.addWidget(models_group)
        layout.addStretch()

        return page

    def _create_model_row(self, model_info: dict) -> QHBoxLayout:
        """Create a rich model display row with metadata

        Args:
            model_info: Dict with keys: model_id, name, symbol, accuracy, created_at, file_size
        """
        row = QHBoxLayout()
        row.setSpacing(DT.SPACE_BASE)

        # Icon based on symbol
        symbol = model_info.get('symbol', 'Unknown').upper()
        if 'BTC' in symbol:
            icon = "₿"
            color = DT.WARNING
        elif 'XAU' in symbol or 'GOLD' in symbol:
            icon = "🥇"
            color = DT.WARNING
        else:
            icon = "📦"
            color = DT.PRIMARY

        # Main info container
        info_container = QVBoxLayout()
        info_container.setSpacing(DT.SPACE_XS)

        # Model name and symbol (primary line)
        name_label = QLabel(f"{icon} {model_info.get('name', 'Unknown Model')} ({symbol})")
        name_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_BOLD))
        name_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        info_container.addWidget(name_label)

        # Metadata (secondary line)
        accuracy = model_info.get('accuracy', 0.0)
        file_size_kb = model_info.get('file_size', 0) / 1024

        # Format created_at
        created_at = model_info.get('created_at', 'Unknown')
        if isinstance(created_at, str) and created_at != 'Unknown':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass

        metadata_text = f"Accuracy: {accuracy:.1%} • Size: {file_size_kb:.1f}KB • Created: {created_at}"
        metadata_label = QLabel(metadata_text)
        metadata_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        metadata_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};")
        info_container.addWidget(metadata_label)

        row.addLayout(info_container)
        row.addStretch()

        # Delete button
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setFixedHeight(DT.BUTTON_HEIGHT_SM)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                color: white;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                border-radius: {DT.RADIUS_SM}px;
                border: none;
                font-weight: {DT.WEIGHT_SEMIBOLD};
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_danger_hover()};
            }}
        """)
        # Connect delete action
        model_id = model_info.get('model_id')
        delete_btn.clicked.connect(lambda: self._delete_model(model_id))
        row.addWidget(delete_btn)

        return row

    def _delete_model(self, model_id: str):
        """Delete a model after confirmation"""
        reply = QMessageBox.question(
            self, "Delete Model",
            f"Are you sure you want to delete this model?\n\nModel ID: {model_id}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.model_security.delete_model(model_id):
                QMessageBox.information(self, "Success", "Model deleted successfully")
                # Refresh the models page
                self._refresh_models_page_ui()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete model")

    def _handle_model_delete(self, model_id: str):
        """Handle model delete from ModelCard"""
        self._delete_model(model_id)

    def _handle_model_details(self, model_id: str):
        """Show detailed model information"""
        # Load model metadata
        secured = self.model_security.load_secured_model(model_id)
        if not secured:
            QMessageBox.warning(self, "Error", "Failed to load model details")
            return

        metadata = secured.metadata

        # Build details message
        details = f"""
Model Details
─────────────────────────────────

Model ID: {model_id}
Name: {metadata.get('name', 'Unknown')}
Symbol: {metadata.get('symbol', 'Unknown')}
Accuracy: {metadata.get('accuracy', 0):.1%}
Created: {metadata.get('created_at', 'Unknown')}

File Size: {len(secured.encrypted_data) / 1024:.1f} KB
Model Hash: {secured.model_hash[:16]}...
HWID Bound: {secured.hwid_hash[:16]}...
"""

        msg = QMessageBox(self)
        msg.setWindowTitle("Model Details")
        msg.setText(details)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _handle_model_load_from_card(self, model_id: str):
        """Load model from ModelCard"""
        # Find model info
        models = self.model_security.list_models_with_metadata()
        model_info = next((m for m in models if m['model_id'] == model_id), None)

        if not model_info:
            QMessageBox.warning(self, "Error", "Model not found")
            return

        symbol = model_info.get('symbol', '').upper()
        if not symbol:
            QMessageBox.warning(self, "Error", "Model has no associated symbol")
            return

        # Load using existing _load_model method
        self._load_model(symbol)

    def _refresh_models_page_ui(self):
        """Refresh the ML Models page UI with current models"""
        try:
            # Get the models page widget (index 2 in content_stack)
            old_page = self.content_stack.widget(2)
            if old_page:
                # Remove old page
                self.content_stack.removeWidget(old_page)
                old_page.deleteLater()
            
            # Create new page with updated models
            new_page = self._create_models_page()
            self.content_stack.insertWidget(2, new_page)
            
            logger.info("Models page UI refreshed")
        except Exception as e:
            logger.error(f"Failed to refresh models page UI: {e}")

    def _create_strategy_page(self) -> QWidget:
        """Strategy Builder page - lazy loaded"""
        api_url = "https://fx.nusanexus.com"  # Production API URL
        self.strategy_builder = StrategyBuilderTab(api_url, self.user_data)
        self.strategy_builder.training_requested.connect(self._handle_training_request)
        return self.strategy_builder

    def _create_settings_page(self) -> QWidget:
        """Settings page with account, MT5, and logout"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        layout.setSpacing(DT.SPACE_LG)

        header = QLabel("Settings")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)

        # Account section - inherits from global QGroupBox style
        account_group = QGroupBox("Account")
        account_layout = QVBoxLayout(account_group)

        # User info
        user_email = self.user_data.get('email', 'Unknown')
        email_label = QLabel(f"Logged in as: {user_email}")
        email_label.setStyleSheet(f"""
            color: {DT.SUCCESS};
            font-size: {DT.FONT_BASE}px;
            font-weight: {DT.WEIGHT_BOLD};
            font-family: {DT.FONT_FAMILY};
        """)
        account_layout.addWidget(email_label)

        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-size: {DT.FONT_BASE}px;
                font-family: {DT.FONT_FAMILY};
                border: none;
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_danger_hover()};
            }}
        """)
        logout_btn.clicked.connect(self._handle_logout)
        account_layout.addWidget(logout_btn)

        layout.addWidget(account_group)

        # Model Sync section
        sync_group = QGroupBox("Model Sync")
        sync_layout = QVBoxLayout(sync_group)

        refresh_btn = QPushButton("🔄 Refresh Models from Cloud")
        refresh_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-size: {DT.FONT_BASE}px;
                font-family: {DT.FONT_FAMILY};
                border: none;
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
        """)
        refresh_btn.clicked.connect(self._refresh_models_from_cloud)
        sync_layout.addWidget(refresh_btn)

        self.sync_status_label = QLabel("Last sync: Never")
        self.sync_status_label.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
        """)
        sync_layout.addWidget(self.sync_status_label)

        layout.addWidget(sync_group)

        # MT5 connection
        mt5_group = QGroupBox("MT5 Connection")
        mt5_layout = QGridLayout(mt5_group)

        # MT5 labels
        login_label = QLabel("Login:")
        login_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};")
        mt5_layout.addWidget(login_label, 0, 0)

        self.mt5_login = QLineEdit()
        self.mt5_login.setFixedHeight(DT.INPUT_HEIGHT)
        mt5_layout.addWidget(self.mt5_login, 0, 1)

        password_label = QLabel("Password:")
        password_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};")
        mt5_layout.addWidget(password_label, 1, 0)

        self.mt5_password = QLineEdit()
        self.mt5_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.mt5_password.setFixedHeight(DT.INPUT_HEIGHT)
        mt5_layout.addWidget(self.mt5_password, 1, 1)

        server_label = QLabel("Server:")
        server_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};")
        mt5_layout.addWidget(server_label, 2, 0)

        self.mt5_server = QLineEdit()
        self.mt5_server.setFixedHeight(DT.INPUT_HEIGHT)
        mt5_layout.addWidget(self.mt5_server, 2, 1)

        connect_btn = QPushButton("Connect to MT5")
        connect_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        connect_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.SUCCESS};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-family: {DT.FONT_FAMILY};
                border: none;
            }}
            QPushButton:hover {{
                background: {DT.SUCCESS_DARK};
            }}
        """)
        connect_btn.clicked.connect(self._connect_mt5)
        mt5_layout.addWidget(connect_btn, 3, 0, 1, 2)

        layout.addWidget(mt5_group)
        layout.addStretch()

        return page
    
    def _handle_logout(self):
        """Handle logout from Supabase"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Sign out from Supabase
                from supabase import create_client
                client = create_client(self.config.supabase.url, self.config.supabase.anon_key)
                client.auth.sign_out()
                logger.info("User logged out")
                
                # Update MT5 status to offline
                if self.supabase_sync:
                    import threading
                    def update_status():
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.supabase_sync.update_mt5_connection_status(is_online=False))
                        loop.close()
                    threading.Thread(target=update_status, daemon=True).start()
                
                # Close and restart app
                QMessageBox.information(self, "Logged Out", "You have been logged out. The application will now restart.")
                self.close()
                
            except Exception as e:
                logger.error(f"Logout error: {e}")
                QMessageBox.warning(self, "Error", f"Logout failed: {e}")
    
    def _refresh_models_from_cloud(self):
        """Refresh models from Supabase Storage"""
        self._ensure_supabase_loaded()  # Ensure Supabase is loaded
        self.sync_status_label.setText("Syncing...")
        
        def do_sync():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._fetch_and_sync_models())
                # Schedule UI update on main thread
                timestamp = datetime.now().strftime("%H:%M:%S")
                QTimer.singleShot(0, lambda: self.sync_status_label.setText(f"Last sync: {timestamp}"))
                # Refresh models page UI
                QTimer.singleShot(0, self._refresh_models_page_ui)
            except Exception as e:
                logger.error(f"Sync failed: {e}")
                QTimer.singleShot(0, lambda: self.sync_status_label.setText(f"Sync failed"))
            finally:
                loop.close()
        
        import threading
        threading.Thread(target=do_sync, daemon=True).start()
    
    def _create_stat_card(self, title: str, value: str, color: str) -> tuple:
        """Create a statistics card with design system"""
        card = QFrame()
        card.setFixedHeight(DT.CARD_MIN_HEIGHT)
        card.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_MEDIUM};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-left: 4px solid {color};
                border-radius: {DT.RADIUS_2XL}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(DT.SPACE_XL, DT.SPACE_LG, DT.SPACE_XL, DT.SPACE_LG)
        layout.setSpacing(DT.SPACE_SM)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_SM}px;
            font-weight: {DT.WEIGHT_MEDIUM};
            font-family: {DT.FONT_FAMILY};
            background: transparent;
        """)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        value_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(value_label)

        layout.addStretch()

        return card, value_label
    
    def _create_status_bar(self):
        """Create the status bar"""
        status_bar = QStatusBar()
        # Status bar style inherited from global stylesheet
        self.setStatusBar(status_bar)

        self.api_status = QLabel("API: Running on 127.0.0.1:8765")
        status_bar.addPermanentWidget(self.api_status)
    
    def _center_on_screen(self):
        """Center the window on the primary screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

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
        """Check MT5 connection status and sync to Supabase"""
        is_connected = self.mt5_client.is_connected

        if is_connected:
            self.mt5_status_label.setText("MT5: Connected ✓")
            self.mt5_status_label.setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_MD}px; font-size: {DT.FONT_XS}px; font-family: {DT.FONT_FAMILY};")
        else:
            self.mt5_status_label.setText("MT5: Disconnected")
            self.mt5_status_label.setStyleSheet(f"color: {DT.DANGER}; padding: {DT.SPACE_MD}px; font-size: {DT.FONT_XS}px; font-family: {DT.FONT_FAMILY};")
        
        self.mt5_status_changed.emit(is_connected)
        
        # Sync MT5 status to Supabase for dashboard (use threading for async)
        if hasattr(self, 'supabase_sync') and self.supabase_sync:
            try:
                # Get MT5 login/server info if connected
                mt5_login = ""
                mt5_server = ""
                if is_connected:
                    account = self.mt5_client.get_account_info()
                    if account:
                        mt5_login = str(account.login) if hasattr(account, 'login') else ""
                        mt5_server = account.server if hasattr(account, 'server') else ""
                
                # Use threading for async call
                import threading
                def sync_status():
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(
                            self.supabase_sync.update_mt5_connection_status(
                                is_online=is_connected,
                                mt5_login=mt5_login,
                                mt5_server=mt5_server
                            )
                        )
                    finally:
                        loop.close()
                threading.Thread(target=sync_status, daemon=True).start()
            except Exception as e:
                logger.error(f"Failed to sync MT5 status to Supabase: {e}")
    
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
                self.stat_values['profit'].setStyleSheet(f"color: {DT.SUCCESS}; font-size: {DT.FONT_2XL}px; font-weight: {DT.WEIGHT_BOLD}; font-family: {DT.FONT_FAMILY};")
            else:
                self.stat_values['profit'].setStyleSheet(f"color: {DT.DANGER}; font-size: {DT.FONT_2XL}px; font-weight: {DT.WEIGHT_BOLD}; font-family: {DT.FONT_FAMILY};")
        
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
            profit_item.setForeground(QColor(DT.SUCCESS if pos.profit >= 0 else DT.DANGER))
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

    def _auto_load_models(self):
        """Auto-load available models for trading symbols on page load"""
        self._ensure_ml_loaded()  # Ensure ML modules are loaded

        # Try to load models for each trading symbol
        for symbol in ["BTCUSD", "XAUUSD"]:
            # Check if model already loaded
            if symbol in self.auto_trader.models:
                logger.info(f"Model for {symbol} already loaded")
                # Update signal card if it exists
                if hasattr(self, 'signal_cards') and symbol in self.signal_cards:
                    model_info = self.auto_trader.models[symbol]
                    accuracy = model_info.accuracy if hasattr(model_info, 'accuracy') else 0.85
                    self.signal_cards[symbol].set_model_loaded(model_info.model_id, accuracy)
                # Legacy signal_labels support
                elif hasattr(self, 'signal_labels') and symbol in self.signal_labels:
                    self.signal_labels[symbol].setText("LOADED")
                    self.signal_labels[symbol].setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_LG}px; font-family: {DT.FONT_FAMILY};")
                continue

            # Find available models for this symbol
            models = self.model_security.list_models()
            symbol_models = [m for m in models if symbol.lower() in m.lower()]

            if not symbol_models:
                logger.info(f"No model found for {symbol}")
                continue

            # Load latest model
            model_id = sorted(symbol_models)[-1]

            # Lazy import for TradingConfig
            from trading.auto_trader import TradingConfig
            config = TradingConfig(
                symbol=symbol,
                timeframe="M15",
                volume=0.01,
                risk_percent=1.0,
                confidence_threshold=0.6
            )

            # Load the model
            if self.auto_trader.load_model(model_id, symbol, config):
                logger.success(f"Auto-loaded model {model_id} for {symbol}")
                # Update signal card if it exists
                if hasattr(self, 'signal_cards') and symbol in self.signal_cards:
                    model_info = self.auto_trader.models[symbol]
                    accuracy = model_info.accuracy if hasattr(model_info, 'accuracy') else 0.85
                    self.signal_cards[symbol].set_model_loaded(model_id, accuracy)
                # Legacy signal_labels support
                elif hasattr(self, 'signal_labels') and symbol in self.signal_labels:
                    self.signal_labels[symbol].setText("LOADED")
                    self.signal_labels[symbol].setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_LG}px; font-family: {DT.FONT_FAMILY};")
            else:
                logger.warning(f"Failed to auto-load model for {symbol}")

    def _load_model(self, symbol: str):
        """Load model for symbol"""
        self._ensure_ml_loaded()  # Ensure ML modules are loaded

        models = self.model_security.list_models()
        symbol_models = [m for m in models if symbol.lower() in m.lower()]
        
        if not symbol_models:
            QMessageBox.warning(self, "No Model", f"No model found for {symbol}. Train one first.")
            return
        
        # Load latest model
        model_id = sorted(symbol_models)[-1]
        
        # Lazy import for TradingConfig
        from trading.auto_trader import TradingConfig
        config = TradingConfig(
            symbol=symbol,
            timeframe="M15",
            volume=0.01,
            risk_percent=1.0,
            confidence_threshold=0.6
        )
        
        if self.auto_trader.load_model(model_id, symbol, config):
            self.signal_labels[symbol].setText("LOADED")
            self.signal_labels[symbol].setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_LG}px; font-family: {DT.FONT_FAMILY};")
            QMessageBox.information(self, "Success", f"Model loaded for {symbol}")
        else:
            QMessageBox.warning(self, "Error", f"Failed to load model for {symbol}")
    
    def _train_models(self):
        """Train demo models"""
        self._ensure_ml_loaded()  # Ensure ML modules are loaded
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
    
    def _update_session_timer(self):
        """Update the trading session timer display"""
        if hasattr(self, 'session_timer_label'):
            if self.trading_session_start:
                elapsed = datetime.now() - self.trading_session_start
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.session_timer_label.setText(f"⏱ Active: {hours:02d}:{minutes:02d}:{seconds:02d}")
                self.session_timer_label.setStyleSheet(f"color: {DT.SUCCESS};")
            else:
                self.session_timer_label.setText("⏱ Ready")
                self.session_timer_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")

    def _start_auto_trading(self):
        """Start auto trading"""
        self._ensure_ml_loaded()  # Ensure ML modules are loaded

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
        self.trader_thread.trade_closed.connect(self._on_trade_close)
        self.trader_thread.error_occurred.connect(self._on_error)
        self.trader_thread.start()

        # Start session timer
        self.trading_session_start = datetime.now()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # Update status label if exists
        if hasattr(self, 'trading_status_label'):
            self.trading_status_label.setText("Auto: RUNNING")
            self.trading_status_label.setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_MD}px; font-size: {DT.FONT_XS}px; font-family: {DT.FONT_FAMILY};")

    def _stop_auto_trading(self):
        """Stop auto trading"""
        if self.trader_thread:
            self.trader_thread.stop()
            self.trader_thread.wait()
            self.trader_thread = None

        # Stop session timer
        self.trading_session_start = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # Update status label if exists
        if hasattr(self, 'trading_status_label'):
            self.trading_status_label.setText("Auto: Stopped")
            self.trading_status_label.setStyleSheet(f"color: {DT.TEXT_DISABLED}; padding: {DT.SPACE_MD}px; font-size: {DT.FONT_XS}px; font-family: {DT.FONT_FAMILY};")
    
    def _on_signal(self, symbol: str, signal: str, confidence: float):
        """Handle signal from auto trader - Enhanced with SignalCard support"""
        # Update SignalCard if exists (new UI)
        if hasattr(self, 'signal_cards') and symbol in self.signal_cards:
            self.signal_cards[symbol].update_signal(signal, confidence)

        # Legacy signal_labels support (old UI)
        elif hasattr(self, 'signal_labels') and symbol in self.signal_labels:
            label = self.signal_labels[symbol]
            label.setText(f"{signal.upper()}\n{confidence:.0%}")

            if signal == "buy":
                label.setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_LG}px; font-size: {DT.FONT_3XL}px; font-family: {DT.FONT_FAMILY};")
            elif signal == "sell":
                label.setStyleSheet(f"color: {DT.DANGER}; padding: {DT.SPACE_LG}px; font-size: {DT.FONT_3XL}px; font-family: {DT.FONT_FAMILY};")
            else:
                label.setStyleSheet(f"color: {DT.TEXT_DISABLED}; padding: {DT.SPACE_LG}px; font-size: {DT.FONT_3XL}px; font-family: {DT.FONT_FAMILY};")

        # Increment all existing ticket row indices (new row inserted at top)
        for ticket in self.trade_log_tickets:
            self.trade_log_tickets[ticket] += 1

        # Add to log table with enhanced formatting
        row = self.log_table.rowCount()
        self.log_table.insertRow(0)

        # Time
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        time_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM))
        self.log_table.setItem(0, 0, time_item)

        # Symbol
        symbol_item = QTableWidgetItem(symbol)
        symbol_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
        self.log_table.setItem(0, 1, symbol_item)

        # Signal with color coding
        signal_item = QTableWidgetItem(signal.upper())
        signal_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_BOLD))
        if signal == "buy":
            signal_item.setForeground(QColor(DT.SUCCESS))
        elif signal == "sell":
            signal_item.setForeground(QColor(DT.DANGER))
        else:
            signal_item.setForeground(QColor(DT.TEXT_DISABLED))
        self.log_table.setItem(0, 2, signal_item)

        # Confidence
        conf_item = QTableWidgetItem(f"{confidence:.0%}")
        conf_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM))
        self.log_table.setItem(0, 3, conf_item)

        # Action (will be updated on trade)
        action_item = QTableWidgetItem("-")
        action_item.setForeground(QColor(DT.TEXT_DISABLED))
        self.log_table.setItem(0, 4, action_item)

        # P&L (empty for signals, updated on trade close)
        pl_item = QTableWidgetItem("-")
        pl_item.setForeground(QColor(DT.TEXT_DISABLED))
        self.log_table.setItem(0, 5, pl_item)

        # Status
        status_item = QTableWidgetItem("Signal" if signal == "hold" else "Pending")
        status_item.setForeground(QColor(DT.TEXT_SECONDARY))
        self.log_table.setItem(0, 6, status_item)

        # Keep only last 50 rows
        while self.log_table.rowCount() > 50:
            self.log_table.removeRow(self.log_table.rowCount() - 1)

    def _on_trade(self, symbol: str, signal: str, ticket: int, volume: float):
        """Handle trade execution - Enhanced with stats update"""
        # Update first row action in log table
        if self.log_table.rowCount() > 0:
            # Store ticket -> row mapping for P&L updates later
            self.trade_log_tickets[ticket] = 0

            action_item = QTableWidgetItem(f"#{ticket}")
            action_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
            action_item.setForeground(QColor(DT.PRIMARY))
            self.log_table.setItem(0, 4, action_item)

            # Update status
            status_item = QTableWidgetItem("✅ Opened")
            status_item.setForeground(QColor(DT.SUCCESS))
            self.log_table.setItem(0, 6, status_item)

        # Update stat cards
        if hasattr(self, 'stat_card_trades'):
            # Get current stats from AutoTrader
            if self.auto_trader and hasattr(self.auto_trader, 'stats'):
                total_trades = sum(s.total_trades for s in self.auto_trader.stats.values())
                total_wins = sum(s.winning_trades for s in self.auto_trader.stats.values())
                total_profit = sum(s.total_profit for s in self.auto_trader.stats.values())

                # Update trades card
                self.stat_card_trades.update_value(str(total_trades), f"+1", True)

                # Update win rate card
                win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
                self.stat_card_winrate.update_value(f"{win_rate:.1f}%")

                # Update P&L card
                profit_positive = total_profit >= 0
                self.stat_card_profit.update_value(
                    f"${total_profit:+.2f}",
                    f"${total_profit:+.2f}",
                    profit_positive
                )

                # Update active positions (query MT5)
                try:
                    positions = self.mt5_client.get_positions()
                    active_count = len(positions) if positions else 0
                    self.stat_card_positions.update_value(str(active_count))
                except:
                    pass

        # Update symbol-specific stats in SignalCard
        if hasattr(self, 'signal_cards') and symbol in self.signal_cards:
            if self.auto_trader and symbol in self.auto_trader.stats:
                stats = self.auto_trader.stats[symbol]
                self.signal_cards[symbol].update_statistics(
                    stats.win_rate,
                    stats.total_trades
                )
    
    def _on_error(self, error: str):
        """Handle error from auto trader"""
        self.statusBar().showMessage(f"Error: {error}", 5000)

    def _on_trade_close(self, ticket: int, profit: float):
        """Handle trade close - Update P&L in trade log"""
        # Find row for this ticket
        if ticket not in self.trade_log_tickets:
            logger.warning(f"Trade close for unknown ticket: {ticket}")
            return

        row = self.trade_log_tickets[ticket]

        # Check if row still valid (might have been removed if > 50 entries)
        if row >= self.log_table.rowCount():
            logger.warning(f"Row {row} for ticket {ticket} no longer exists")
            del self.trade_log_tickets[ticket]
            return

        # Update P&L column (column 5)
        pl_item = QTableWidgetItem(f"${profit:+.2f}")
        pl_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))

        # Color code: green for profit, red for loss
        if profit > 0:
            pl_item.setForeground(QColor(DT.SUCCESS))
        elif profit < 0:
            pl_item.setForeground(QColor(DT.DANGER))
        else:
            pl_item.setForeground(QColor(DT.TEXT_MUTED))

        self.log_table.setItem(row, 5, pl_item)

        # Update status column (column 6)
        if profit > 0:
            status_item = QTableWidgetItem("✅ Closed +")
            status_item.setForeground(QColor(DT.SUCCESS))
        elif profit < 0:
            status_item = QTableWidgetItem("❌ Closed -")
            status_item.setForeground(QColor(DT.DANGER))
        else:
            status_item = QTableWidgetItem("⚪ Closed")
            status_item.setForeground(QColor(DT.TEXT_SECONDARY))

        self.log_table.setItem(row, 6, status_item)

        # Clean up ticket mapping
        del self.trade_log_tickets[ticket]

        logger.info(f"Updated trade log for ticket {ticket}: P&L=${profit:+.2f}")
    
    def _apply_styles(self):
        """Apply global styles using design system"""
        self.setStyleSheet(f"""
            /* Main Window */
            QMainWindow {{
                background: {StyleSheets.gradient_background()};
                font-family: {DT.FONT_FAMILY};
            }}

            /* Labels */
            QLabel {{
                color: {DT.TEXT_PRIMARY};
                font-family: {DT.FONT_FAMILY};
            }}

            /* Group Boxes - Glassmorphism */
            QGroupBox {{
                {StyleSheets.glass_card()}
                margin-top: {DT.SPACE_BASE}px;
                font-size: {DT.FONT_BASE}px;
                font-weight: {DT.WEIGHT_SEMIBOLD};
                color: {DT.TEXT_SECONDARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {DT.SPACE_LG}px;
                padding: 0 {DT.SPACE_MD}px;
                color: {DT.TEXT_PRIMARY};
            }}

            /* Tables */
            QTableWidget {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_XL}px;
                gridline-color: {DT.BORDER_SUBTLE};
                color: {DT.TEXT_PRIMARY};
                selection-background-color: rgba(6, 182, 212, 0.3);
            }}
            QTableWidget::item {{
                padding: {DT.SPACE_MD}px;
                border-bottom: 1px solid {DT.BORDER_SUBTLE};
            }}
            QTableWidget::item:alternate {{
                background: {DT.GLASS_LIGHT};
            }}
            QTableWidget::item:hover {{
                background: rgba(6, 182, 212, 0.15);
            }}
            QHeaderView::section {{
                background: {StyleSheets.gradient_primary()};
                color: {DT.TEXT_PRIMARY};
                padding: {DT.SPACE_MD}px {DT.SPACE_BASE}px;
                border: none;
                border-bottom: 2px solid {DT.BORDER_MEDIUM};
                font-weight: {DT.WEIGHT_SEMIBOLD};
                font-size: {DT.FONT_SM}px;
                text-transform: uppercase;
            }}

            /* Buttons - Secondary (default) */
            QPushButton {{
                background: {DT.GLASS_MEDIUM};
                border: 1px solid {DT.BORDER_MEDIUM};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                color: {DT.TEXT_SECONDARY};
                font-weight: {DT.WEIGHT_SEMIBOLD};
                font-size: {DT.FONT_SM}px;
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: rgba(6, 182, 212, 0.2);
                border: 1px solid {DT.BORDER_FOCUS};
                color: {DT.PRIMARY};
            }}
            QPushButton:pressed {{
                background: rgba(6, 182, 212, 0.3);
            }}
            QPushButton:disabled {{
                background: rgba(71, 85, 105, 0.5);
                color: {DT.TEXT_DISABLED};
                border: 1px solid rgba(100, 116, 139, 0.3);
            }}

            /* Input Fields */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                {StyleSheets.input_field()}
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border: 2px solid {DT.BORDER_STRONG};
                background: {DT.GLASS_DARKEST};
            }}
            QLineEdit::placeholder {{
                color: {DT.TEXT_PLACEHOLDER};
            }}

            /* Scrollbars */
            QScrollBar:vertical {{
                background: rgba(15, 23, 42, 0.3);
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(6, 182, 212, 0.4);
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(6, 182, 212, 0.6);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background: rgba(15, 23, 42, 0.3);
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(6, 182, 212, 0.4);
                border-radius: 5px;
                min-width: 30px;
            }}

            /* Progress Bar */
            QProgressBar {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_MD}px;
                text-align: center;
                color: {DT.TEXT_PRIMARY};
                font-weight: {DT.WEIGHT_SEMIBOLD};
            }}
            QProgressBar::chunk {{
                background: {StyleSheets.gradient_primary()};
                border-radius: {DT.RADIUS_SM}px;
            }}

            /* Status Bar */
            QStatusBar {{
                background: {DT.GLASS_DARK};
                border-top: 1px solid {DT.BORDER_DEFAULT};
                color: {DT.TEXT_DISABLED};
                font-size: {DT.FONT_SM}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
            }}

            /* Message Box */
            QMessageBox {{
                background: {DT.BG_DARK};
            }}
            QMessageBox QLabel {{
                color: {DT.TEXT_PRIMARY};
            }}
            QMessageBox QPushButton {{
                min-width: 80px;
            }}
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
    
    async def _fetch_and_sync_models(self):
        """Fetch user's models from Supabase and download them"""
        try:
            logger.info("Fetching models from Supabase...")
            models = await self.supabase_sync.fetch_user_models()
            
            if not models:
                logger.info("No models found in Supabase")
                return
            
            logger.info(f"Found {len(models)} models, downloading...")
            
            for model_meta in models:
                # Download model file
                local_path = await self.supabase_sync.download_model(model_meta)
                
                if local_path:
                    # Use 'name' column which exists in the database
                    model_name = model_meta.get('name') or model_meta.get('model_name', 'unknown')
                    logger.success(f"Model {model_name} ready")
            
            self.statusBar().showMessage(f"Synced {len(models)} models from cloud", 5000)
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            self.statusBar().showMessage(f"Failed to sync models: {e}", 5000)
    
    def _handle_training_request(self, config: dict, symbol: str, model_name: str):
        """Handle custom model training request from Strategy Builder"""
        logger.info(f"Training request: {model_name} for {symbol}")

        # Ensure dependencies are loaded
        self._ensure_supabase_loaded()

        # Import here to avoid circular dependency
        from ai.custom_trainer import CustomModelTrainer
        
        # Create trainer with progress callback and Supabase sync
        def on_progress(message: str, percent: int):
            self.strategy_builder.update_progress(message, percent)
        
        trainer = CustomModelTrainer(
            symbol=symbol,
            llm_config=config,
            model_name=model_name,
            progress_callback=on_progress,
            supabase_sync=self.supabase_sync  # Pass Supabase sync
        )
        
        # Start training in background thread
        import threading
        
        def train_thread():
            try:
                # Run async training
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(trainer.train())
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Training Complete",
                    f"Model '{model_name}' trained successfully!\\n\\n"
                    f"Win Rate: {result.get('win_rate', 0):.1f}%\\n"
                    f"Kelly Fraction: {result.get('kelly_fraction', 0):.2f}\\n"
                    f"Model ID: {result.get('model_id', 'N/A')}\\n"
                    f"Cloud Synced: {'Yes' if result.get('cloud_model_id') else 'No'}"
                )
                
            except Exception as e:
                logger.exception(f"Training failed: {e}")
                QMessageBox.critical(
                    self,
                    "Training Failed",
                    f"Failed to train model:\\n{str(e)}"
                )
        
        thread = threading.Thread(target=train_thread, daemon=True)
        thread.start()
