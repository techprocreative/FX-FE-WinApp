"""
NexusTrade Main Window
Refactored modular UI with modern design.
"""
import asyncio
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QMouseEvent

from core.config import Config
from core.mt5_client import MT5Client
from api.server import set_mt5_client

from ui.design_system import DesignTokens as DT
from ui.widgets.title_bar import ModernTitleBar
from ui.widgets.sidebar import NavSidebar
from ui.pages.dashboard_page import DashboardPage
from ui.pages.models_page import ModelsPage
from ui.pages.settings_page import SettingsPage
from ui.pages.logs_page import LogsPage
from loguru import logger

# Type hints only
if TYPE_CHECKING:
    from security.model_security import ModelSecurity
    from trading.auto_trader import AutoTrader, Signal, TradingConfig

# Re-using the existing AutoTraderThread logic
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
    """Main application window with modern UI"""
    
    def __init__(self, config: Config, user_data: dict):
        super().__init__()
        self.config = config
        self.user_data = user_data
        self.mt5_client = MT5Client()
        
        # Initial Window Setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1280, 800)
        self.setMinimumSize(1024, 768)
        
        # Lazy Loading State
        self.model_security = None
        self.auto_trader = None
        self.trader_thread: Optional[AutoTraderThread] = None
        self.supabase_sync = None
        
        self._pages_loaded = {
            'dashboard': False,
            'models': False,
            'logs': False,
            'settings': False
        }
        
        # Supabase config for sync
        self._supabase_config = {
            'url': config.supabase.url,
            'anon_key': config.supabase.anon_key,
            'user_id': user_data['id'],
            'access_token': user_data.get('access_token')
        }
        
        # Initialize UI
        self._setup_ui()
        self._center_on_screen()
        
        # Connect MT5 if configured
        QTimer.singleShot(1000, self._check_mt5_connection)
        
    def _setup_ui(self):
        # Main Container
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f"background: {DT.BACKGROUND_DARK}; border-radius: {DT.RADIUS_LG}px;")
        self.setCentralWidget(self.central_widget)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Custom Title Bar
        self.title_bar = ModernTitleBar("NexusTrade Connector")
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)
        self.main_layout.addWidget(self.title_bar)
        
        # 2. Content Area (Sidebar + Stack)
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = NavSidebar()
        self.sidebar.page_changed.connect(self._navigate_to)
        content_layout.addWidget(self.sidebar)
        
        # Page Stack
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        self.main_layout.addWidget(content_area)
        
        # Initial Page (Dashboard)
        self._navigate_to(0)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def _navigate_to(self, index: int):
        page_map = {
            0: ('dashboard', self._create_dashboard_page),
            1: ('models', self._create_models_page),
            2: ('logs', self._create_logs_page),
            3: ('settings', self._create_settings_page)
        }
        
        if index not in page_map:
            return
            
        page_key, create_func = page_map[index]
        
        # Ensure we have enough widgets in stack
        while self.content_stack.count() <= index:
            self.content_stack.addWidget(QWidget())  # Add placeholder
        
        # Lazy load page if not already loaded
        if not self._pages_loaded[page_key]:
            # Pre-load dependencies
            if page_key in ['dashboard', 'models']:
                self._ensure_ml_loaded()
            if page_key == 'models':
                self._ensure_supabase_loaded()
            
            # Create the page
            page = create_func()
            
            # Replace placeholder with actual page
            old_widget = self.content_stack.widget(index)
            self.content_stack.removeWidget(old_widget)
            old_widget.deleteLater()
            self.content_stack.insertWidget(index, page)
            
            # Wire up signals
            if page_key == 'dashboard':
                page.start_trading_requested.connect(self._start_auto_trading)
                page.stop_trading_requested.connect(self._stop_auto_trading)
                page.load_model_requested.connect(self._load_model_for_dashboard)
            elif page_key == 'models':
                page.load_model_requested.connect(self._load_model_from_card)
                page.train_model_requested.connect(self._train_models_placeholder)
            elif page_key == 'settings':
                page.logout_requested.connect(self._handle_logout)
                page.connect_mt5_requested.connect(self._connect_mt5)
                page.refresh_models_requested.connect(self._refresh_models_from_cloud)
            
            self._pages_loaded[page_key] = True
        
        self.content_stack.setCurrentIndex(index)
        self.sidebar.set_active_index(index)

    # --- Page Creators ---
    
    def _create_dashboard_page(self) -> QWidget:
        return DashboardPage()

    def _create_models_page(self) -> QWidget:
        return ModelsPage(self.model_security, self.auto_trader)

    def _create_logs_page(self) -> QWidget:
        return LogsPage()

    def _create_settings_page(self) -> QWidget:
        return SettingsPage(self.user_data)

    # --- Logic & Signals ---

    def _ensure_ml_loaded(self):
        if not self.model_security or not self.auto_trader:
            logger.info("Initializing ML modules...")
            from security.model_security import ModelSecurity
            from trading.auto_trader import AutoTrader
            
            self.model_security = ModelSecurity()
            self.auto_trader = AutoTrader(self.mt5_client, self.model_security)
            
    def _ensure_supabase_loaded(self):
        if not self.supabase_sync:
            from core.supabase_sync import SupabaseModelSync
            self.supabase_sync = SupabaseModelSync(
                supabase_url=self._supabase_config['url'],
                supabase_key=self._supabase_config['anon_key'],
                user_id=self._supabase_config['user_id'],
                access_token=self._supabase_config.get('access_token')
            )

    def _check_mt5_connection(self):
        if self.mt5_client.is_connected:
             # Notify settings page if loaded
             if self._pages_loaded['settings']:
                 settings_page = self.content_stack.widget(3)
                 if isinstance(settings_page, SettingsPage):
                     settings_page.set_mt5_status(True)
             
             # Notify Dashboard
             # TODO: Add connection status to Dashboard
        else:
            logger.warning("MT5 not connected on startup")

    def _connect_mt5(self, info: dict):
        # Update config only if provided? 
        # For security, we might not save password to plain text config easily.
        # Just try to connect.
        if self.mt5_client.connect(login=int(info['login'] or 0), password=info['password'], server=info['server']):
            QMessageBox.information(self, "Success", "Connected to MT5")
            settings_page = self.content_stack.widget(3)
            settings_page.set_mt5_status(True)
        else:
             QMessageBox.warning(self, "Error", "Failed to connect to MT5")

    def _start_auto_trading(self, interval: int):
        self._ensure_ml_loaded()
        if not self.mt5_client.connected:
             QMessageBox.warning(self, "Error", "MT5 not connected")
             return
             
        if not self.auto_trader.models:
             QMessageBox.warning(self, "Error", "No models loaded")
             return
             
        dashboard = self.content_stack.widget(0)
        
        # Start thread
        self.trader_thread = AutoTraderThread(self.auto_trader, interval)
        self.trader_thread.signal_received.connect(dashboard.update_signal)
        self.trader_thread.trade_executed.connect(dashboard.handle_trade_execution)
        self.trader_thread.trade_closed.connect(dashboard.handle_trade_close)
        self.trader_thread.error_occurred.connect(lambda e: logger.error(f"AutoTrader Error: {e}"))
        
        self.trader_thread.start()
        dashboard.set_trading_state(True)

    def _stop_auto_trading(self):
        if self.trader_thread:
            self.trader_thread.stop()
            self.trader_thread.wait()
            self.trader_thread = None
            
        dashboard = self.content_stack.widget(0)
        if isinstance(dashboard, DashboardPage):
            dashboard.set_trading_state(False)

    def _load_model_for_dashboard(self, symbol: str):
        """Load model for a symbol from Dashboard signal cards"""
        self._ensure_ml_loaded()
        
        # Get models with metadata to properly match by symbol
        models = self.model_security.list_models_with_metadata()
        
        # Find models matching the requested symbol (case insensitive)
        symbol_upper = symbol.upper()
        symbol_models = [m for m in models if m.get('symbol', '').upper() == symbol_upper]
        
        if not symbol_models:
            QMessageBox.warning(self, "No Model", f"No model found for {symbol}. Sync from cloud or train one.")
            return

        # Pick the most recent one (by created_at or just first)
        model_info = symbol_models[0]  # Already sorted by created_at desc from list_models_with_metadata
        model_id = model_info['model_id']
        
        self._load_model_from_card(model_id)

    def _load_model_from_card(self, model_id: str):
        self._ensure_ml_loaded()
        
        # Logic from fix
        models = self.model_security.list_models_with_metadata()
        model_info = next((m for m in models if m['model_id'] == model_id), None)
        
        if not model_info:
             QMessageBox.warning(self, "Error", "Model not found")
             return
             
        symbol = model_info.get('symbol', '').upper()
        if not symbol:
             return
             
        # Lazy import config
        from trading.auto_trader import TradingConfig
        config = TradingConfig(symbol=symbol, timeframe="M15", volume=0.01)
        
        if self.auto_trader.load_model(model_id, symbol, config):
            QMessageBox.information(self, "Success", f"Loaded {model_info.get('name')} for {symbol}")
            
            # Update Dashboard Status
            if self._pages_loaded['dashboard']:
                dash = self.content_stack.widget(0)
                if isinstance(dash, DashboardPage):
                    dash.update_model_status(symbol, model_id, model_info.get('accuracy', 0))
                    
            # Update Models Page Status
            if self._pages_loaded['models']:
                mod_page = self.content_stack.widget(1)
                mod_page.refresh()
                
    def _refresh_models_from_cloud(self):
        self._ensure_supabase_loaded()
        try:
            models = self.supabase_sync.fetch_user_models()
            downloaded_count = 0
            for model in models:
                result = self.supabase_sync.download_model(model)
                if result:
                    downloaded_count += 1
            
            QMessageBox.information(self, "Sync", f"Synced {len(models)} models, downloaded {downloaded_count}")
            
            if self._pages_loaded['models']:
                self.content_stack.widget(1).refresh()
        except Exception as e:
            QMessageBox.warning(self, "Sync Error", f"Failed to sync: {e}")
            
    def _train_models_placeholder(self):
        QMessageBox.information(self, "Train", "Training feature coming soon!")

    def _handle_logout(self):
        self.close()
        # Should restart app or show login? 
        # For now, just close as per old logic usually handling restart elsewhere

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def mousePressEvent(self, event):
        # Resize handle emulation if needed, or rely on native methods if possible
        # For now, just allow title bar drag
        pass
