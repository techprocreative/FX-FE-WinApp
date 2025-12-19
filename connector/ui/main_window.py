"""
NexusTrade Main Window
Primary UI for the Windows connector application
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QFrame,
    QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from core.config import Config
from core.mt5_client import MT5Client
from api.server import set_mt5_client


class MainWindow(QMainWindow):
    """Main application window"""
    
    mt5_status_changed = pyqtSignal(bool)
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.mt5_client = MT5Client()
        
        # Set MT5 client reference for API server
        set_mt5_client(self.mt5_client)
        
        self._setup_ui()
        self._setup_timers()
    
    def _setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("NexusTrade - Forex Trading Platform")
        self.setMinimumSize(1200, 800)
        
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
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-right: 1px solid #0f3460;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(80)
        logo_layout = QHBoxLayout(logo_frame)
        
        logo_label = QLabel("NexusTrade")
        logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        logo_label.setStyleSheet("color: #e94560; padding: 20px;")
        logo_layout.addWidget(logo_label)
        
        layout.addWidget(logo_frame)
        
        # Navigation buttons
        nav_items = [
            ("Dashboard", 0),
            ("Trading", 1),
            ("Backtest", 2),
            ("ML Models", 3),
            ("Strategy AI", 4),
            ("Settings", 5),
        ]
        
        self.nav_buttons = []
        for name, index in nav_items:
            btn = self._create_nav_button(name, index)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addStretch()
        
        # MT5 connection status
        self.mt5_status_label = QLabel("MT5: Disconnected")
        self.mt5_status_label.setStyleSheet("""
            color: #ff6b6b;
            padding: 20px;
            font-size: 12px;
        """)
        layout.addWidget(self.mt5_status_label)
        
        return sidebar
    
    def _create_nav_button(self, text: str, index: int) -> QPushButton:
        """Create a navigation button"""
        btn = QPushButton(f"  {text}")
        btn.setFixedHeight(50)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0a0a0;
                border: none;
                text-align: left;
                padding-left: 20px;
                font-size: 14px;
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
        
        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def _create_pages(self):
        """Create content pages"""
        # Dashboard page
        dashboard = self._create_dashboard_page()
        self.content_stack.addWidget(dashboard)
        
        # Trading page (placeholder)
        trading = self._create_placeholder_page("Trading", "Execute trades and manage positions")
        self.content_stack.addWidget(trading)
        
        # Backtest page (placeholder)
        backtest = self._create_placeholder_page("Backtesting", "Test your strategies on historical data")
        self.content_stack.addWidget(backtest)
        
        # ML Models page (placeholder)
        models = self._create_placeholder_page("ML Models", "Train and manage ML trading models")
        self.content_stack.addWidget(models)
        
        # Strategy AI page (placeholder)
        strategy = self._create_placeholder_page("Strategy AI", "Generate strategies with AI")
        self.content_stack.addWidget(strategy)
        
        # Settings page (placeholder)
        settings = self._create_placeholder_page("Settings", "Configure application settings")
        self.content_stack.addWidget(settings)
    
    def _create_dashboard_page(self) -> QWidget:
        """Create the dashboard page"""
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
        
        cards = [
            ("Account Balance", "$0.00", "#4ecca3"),
            ("Today's P/L", "$0.00", "#e94560"),
            ("Open Positions", "0", "#0f3460"),
            ("Win Rate", "0%", "#ffd369"),
        ]
        
        for title, value, color in cards:
            card = self._create_stat_card(title, value, color)
            cards_layout.addWidget(card)
        
        layout.addLayout(cards_layout)
        
        # Placeholder for chart
        chart_placeholder = QFrame()
        chart_placeholder.setMinimumHeight(300)
        chart_placeholder.setStyleSheet(f"""
            QFrame {{
                background-color: #16213e;
                border-radius: 10px;
                border: 1px solid #0f3460;
            }}
        """)
        
        chart_label = QLabel("Equity Chart")
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_label.setStyleSheet("color: #666; font-size: 16px;")
        
        chart_layout = QVBoxLayout(chart_placeholder)
        chart_layout.addWidget(chart_label)
        
        layout.addWidget(chart_placeholder)
        
        layout.addStretch()
        
        return page
    
    def _create_stat_card(self, title: str, value: str, accent_color: str) -> QFrame:
        """Create a statistics card"""
        card = QFrame()
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #16213e;
                border-radius: 10px;
                border-left: 4px solid {accent_color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {accent_color};")
        layout.addWidget(value_label)
        
        return card
    
    def _create_placeholder_page(self, title: str, description: str) -> QWidget:
        """Create a placeholder page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QLabel(title)
        header.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        desc = QLabel(description)
        desc.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(desc)
        
        coming_soon = QLabel("Coming Soon...")
        coming_soon.setStyleSheet("color: #e94560; font-size: 18px; margin-top: 50px;")
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(coming_soon)
        
        layout.addStretch()
        
        return page
    
    def _create_status_bar(self):
        """Create the status bar"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0f0f1a;
                color: #888;
                font-size: 11px;
            }
        """)
        self.setStatusBar(status_bar)
        
        # API server status
        self.api_status = QLabel("API: Running on 127.0.0.1:8765")
        status_bar.addPermanentWidget(self.api_status)
    
    def _setup_timers(self):
        """Setup background timers"""
        # MT5 connection check timer
        self.mt5_timer = QTimer()
        self.mt5_timer.timeout.connect(self._check_mt5_connection)
        self.mt5_timer.start(5000)  # Check every 5 seconds
    
    def _check_mt5_connection(self):
        """Check MT5 connection status"""
        is_connected = self.mt5_client.is_connected
        
        if is_connected:
            self.mt5_status_label.setText("MT5: Connected ✓")
            self.mt5_status_label.setStyleSheet("color: #4ecca3; padding: 20px; font-size: 12px;")
        else:
            self.mt5_status_label.setText("MT5: Disconnected")
            self.mt5_status_label.setStyleSheet("color: #ff6b6b; padding: 20px; font-size: 12px;")
        
        self.mt5_status_changed.emit(is_connected)
    
    def _apply_styles(self):
        """Apply global styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close"""
        reply = QMessageBox.question(
            self,
            "Exit NexusTrade",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Cleanup
            if self.mt5_client.is_connected:
                self.mt5_client.logout()
            event.accept()
        else:
            event.ignore()
