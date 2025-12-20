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
    QHeaderView, QLineEdit, QProgressBar
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
        self.setMinimumSize(DT.MAIN_MIN_WIDTH, DT.MAIN_MIN_HEIGHT)

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
                self.content_stack.removeWidget(old_widget)
                old_widget.deleteLater()
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
        """Auto trading control page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        layout.setSpacing(DT.SPACE_LG)

        # Header
        header = QLabel("Auto Trading")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)

        # Control panel - inherits from global QGroupBox style
        control_group = QGroupBox("Trading Control")
        control_layout = QHBoxLayout(control_group)

        # Start/Stop buttons with design system
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
        
        # Signals panel
        signals_layout = QHBoxLayout()
        
        for symbol in ["BTCUSD", "XAUUSD"]:
            signal_card = self._create_signal_card(symbol)
            signals_layout.addWidget(signal_card)
        
        layout.addLayout(signals_layout)
        
        # Trade log - inherits from global stylesheet
        log_group = QGroupBox("Recent Signals")
        log_layout = QVBoxLayout(log_group)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Time", "Symbol", "Signal", "Confidence", "Action"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        log_layout.addWidget(self.log_table)
        
        layout.addWidget(log_group)
        
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
        """ML Models management page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL, DT.SPACE_2XL)
        layout.setSpacing(DT.SPACE_LG)

        header = QLabel("ML Models")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)

        # Model list - inherits from global QGroupBox style
        models_group = QGroupBox("Available Models")
        models_layout = QVBoxLayout(models_group)

        # List models
        models = self.model_security.list_models()
        logger.info(f"Creating models page - found {len(models)} models: {models}")
        if models:
            for model_id in models:
                model_row = QHBoxLayout()
                model_label = QLabel(f"📦 {model_id}")
                model_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
                model_row.addWidget(model_label)
                model_row.addStretch()
                delete_btn = QPushButton("Delete")
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
                model_row.addWidget(delete_btn)
                models_layout.addLayout(model_row)
        else:
            no_models_label = QLabel("No models found. Train models first.")
            no_models_label.setStyleSheet(f"color: {DT.TEXT_DISABLED}; font-family: {DT.FONT_FAMILY};")
            models_layout.addWidget(no_models_label)

        # Train button
        train_btn = QPushButton("🔧 Train New Models (BTC & XAU)")
        train_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
        train_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.SUCCESS};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_XL}px;
                border-radius: {DT.RADIUS_LG}px;
                font-size: {DT.FONT_BASE}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-family: {DT.FONT_FAMILY};
                border: none;
            }}
            QPushButton:hover {{
                background: {DT.SUCCESS_DARK};
            }}
        """)
        train_btn.clicked.connect(self._train_models)
        models_layout.addWidget(train_btn)

        layout.addWidget(models_group)
        layout.addStretch()

        return page
    
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
        self.trader_thread.error_occurred.connect(self._on_error)
        self.trader_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.trading_status_label.setText("Auto: RUNNING")
        self.trading_status_label.setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_MD}px; font-size: {DT.FONT_XS}px; font-family: {DT.FONT_FAMILY};")
    
    def _stop_auto_trading(self):
        """Stop auto trading"""
        if self.trader_thread:
            self.trader_thread.stop()
            self.trader_thread.wait()
            self.trader_thread = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.trading_status_label.setText("Auto: Stopped")
        self.trading_status_label.setStyleSheet(f"color: {DT.TEXT_DISABLED}; padding: {DT.SPACE_MD}px; font-size: {DT.FONT_XS}px; font-family: {DT.FONT_FAMILY};")
    
    def _on_signal(self, symbol: str, signal: str, confidence: float):
        """Handle signal from auto trader"""
        if symbol in self.signal_labels:
            label = self.signal_labels[symbol]
            label.setText(f"{signal.upper()}\n{confidence:.0%}")

            if signal == "buy":
                label.setStyleSheet(f"color: {DT.SUCCESS}; padding: {DT.SPACE_LG}px; font-size: {DT.FONT_3XL}px; font-family: {DT.FONT_FAMILY};")
            elif signal == "sell":
                label.setStyleSheet(f"color: {DT.DANGER}; padding: {DT.SPACE_LG}px; font-size: {DT.FONT_3XL}px; font-family: {DT.FONT_FAMILY};")
            else:
                label.setStyleSheet(f"color: {DT.TEXT_DISABLED}; padding: {DT.SPACE_LG}px; font-size: {DT.FONT_3XL}px; font-family: {DT.FONT_FAMILY};")
        
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
