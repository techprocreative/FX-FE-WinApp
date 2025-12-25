from typing import Dict, Optional, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QDoubleSpinBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.design_system import DesignTokens as DT, StyleSheets
from ui.components.stat_card import StatCard
from ui.components.signal_card import SignalCard
from ui.animation_system import AnimationUtils, HoverAnimator, PageTransitionAnimator
from loguru import logger

class TradingMetricsPanel(QFrame):
    """Enhanced trading metrics panel with better visual hierarchy"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.metrics = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the metrics panel UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_LG}px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_LG, DT.SPACE_LG, DT.SPACE_LG, DT.SPACE_LG)
        layout.setSpacing(DT.SPACE_BASE)
        
        # Title
        title = QLabel("📊 Trading Metrics")
        title.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_BOLD))
        title.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)
        
        # Metrics grid
        self.metrics_layout = QGridLayout()
        self.metrics_layout.setSpacing(DT.SPACE_BASE)
        layout.addLayout(self.metrics_layout)
        
        # Initialize key metrics
        self._create_metric_labels()
        
    def _create_metric_labels(self):
        """Create metric labels with enhanced styling"""
        metrics_config = [
            ("balance", "Account Balance", "$0.00", DT.PRIMARY_400),
            ("equity", "Equity", "$0.00", DT.SUCCESS_400),
            ("margin", "Free Margin", "$0.00", DT.WARNING_400),
            ("drawdown", "Drawdown", "0.0%", DT.DANGER_400),
        ]
        
        for i, (key, label, default_value, color) in enumerate(metrics_config):
            row = i // 2
            col = (i % 2) * 2
            
            # Label
            label_widget = QLabel(label)
            label_widget.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_MEDIUM))
            label_widget.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
            self.metrics_layout.addWidget(label_widget, row, col)
            
            # Value
            value_widget = QLabel(default_value)
            value_widget.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_BOLD))
            value_widget.setStyleSheet(f"color: {color}; background: transparent;")
            value_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.metrics_layout.addWidget(value_widget, row, col + 1)
            
            self.metrics[key] = value_widget
            
    def update_metric(self, key: str, value: str, color: str = None):
        """Update a specific metric"""
        if key in self.metrics:
            self.metrics[key].setText(value)
            if color:
                self.metrics[key].setStyleSheet(f"color: {color}; background: transparent;")


class EnhancedTradeLog(QFrame):
    """Enhanced trade log with better visual indicators and filtering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trade_log_tickets = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the enhanced trade log UI"""
        self.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_LG, DT.SPACE_LG, DT.SPACE_LG, DT.SPACE_LG)
        layout.setSpacing(DT.SPACE_BASE)
        
        # Header with title and filters
        header_layout = QHBoxLayout()
        
        title = QLabel("📈 Live Trading Activity")
        title.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_BOLD))
        title.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("● Live")
        self.status_indicator.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_MEDIUM))
        self.status_indicator.setStyleSheet(f"color: {DT.SUCCESS_400}; background: transparent;")
        header_layout.addWidget(self.status_indicator)
        
        layout.addLayout(header_layout)
        
        # Enhanced table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(8)
        self.log_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Signal", "Confidence", "Action", "Size", "P&L", "Status"
        ])
        
        # Enhanced table styling
        self.log_table.setStyleSheet(f"""
            QTableWidget {{
                background: {DT.GLASS_DARKEST};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: {DT.RADIUS_MD}px;
                gridline-color: {DT.BORDER_SUBTLE};
                color: {DT.TEXT_PRIMARY};
                font-family: {DT.FONT_FAMILY};
                font-size: {DT.FONT_SM}px;
            }}
            QTableWidget::item {{
                padding: {DT.SPACE_SM}px;
                border-bottom: 1px solid {DT.BORDER_SUBTLE};
            }}
            QTableWidget::item:selected {{
                background: {DT.GLASS_MEDIUM};
                color: {DT.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background: {DT.GLASS_MEDIUM};
                color: {DT.TEXT_SECONDARY};
                padding: {DT.SPACE_SM}px;
                border: none;
                border-bottom: 2px solid {DT.BORDER_DEFAULT};
                font-weight: {DT.WEIGHT_SEMIBOLD};
            }}
        """)
        
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setMaximumHeight(300)  # Limit height
        
        layout.addWidget(self.log_table)
        
    def add_log_entry(self, symbol: str, signal: str, confidence: float, size: float = 0.0):
        """Add enhanced log entry with better formatting"""
        # Increment existing ticket row indices
        for ticket in self.trade_log_tickets:
            self.trade_log_tickets[ticket] += 1
            
        self.log_table.insertRow(0)
        
        # Time with enhanced formatting
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        time_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_MEDIUM))
        time_item.setForeground(QColor(DT.TEXT_SECONDARY))
        self.log_table.setItem(0, 0, time_item)
        
        # Symbol with icon
        symbol_icon = "₿" if "BTC" in symbol else ("🥇" if "XAU" in symbol else "📊")
        symbol_item = QTableWidgetItem(f"{symbol_icon} {symbol}")
        symbol_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
        symbol_item.setForeground(QColor(DT.TEXT_PRIMARY))
        self.log_table.setItem(0, 1, symbol_item)
        
        # Signal with enhanced styling
        signal_upper = signal.upper()
        signal_emoji = "🟢" if signal == "buy" else ("🔴" if signal == "sell" else "⚪")
        signal_item = QTableWidgetItem(f"{signal_emoji} {signal_upper}")
        signal_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_BOLD))
        
        if signal == "buy":
            signal_item.setForeground(QColor(DT.SUCCESS_400))
        elif signal == "sell":
            signal_item.setForeground(QColor(DT.DANGER_400))
        else:
            signal_item.setForeground(QColor(DT.WARNING_400))
        self.log_table.setItem(0, 2, signal_item)
        
        # Confidence with color coding
        conf_item = QTableWidgetItem(f"{confidence:.0%}")
        conf_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_MEDIUM))
        if confidence >= 0.8:
            conf_item.setForeground(QColor(DT.SUCCESS_400))
        elif confidence >= 0.6:
            conf_item.setForeground(QColor(DT.WARNING_400))
        else:
            conf_item.setForeground(QColor(DT.DANGER_400))
        self.log_table.setItem(0, 3, conf_item)
        
        # Action, Size, P&L, Status placeholders
        self.log_table.setItem(0, 4, QTableWidgetItem("-"))  # Action
        size_item = QTableWidgetItem(f"{size:.2f}" if size > 0 else "-")
        self.log_table.setItem(0, 5, size_item)  # Size
        self.log_table.setItem(0, 6, QTableWidgetItem("-"))  # P&L
        
        status_item = QTableWidgetItem("🔄 Signal")
        status_item.setForeground(QColor(DT.PRIMARY_400))
        self.log_table.setItem(0, 7, status_item)  # Status

        # Limit rows
        while self.log_table.rowCount() > 50:
            self.log_table.removeRow(self.log_table.rowCount() - 1)
            
    def handle_trade_execution(self, symbol: str, signal: str, ticket: int, volume: float):
        """Handle trade execution with enhanced display"""
        if self.log_table.rowCount() > 0:
            self.trade_log_tickets[ticket] = 0
            
            action_item = QTableWidgetItem(f"#{ticket}")
            action_item.setForeground(QColor(DT.PRIMARY_400))
            action_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
            self.log_table.setItem(0, 4, action_item)
            
            size_item = QTableWidgetItem(f"{volume:.2f}")
            size_item.setForeground(QColor(DT.TEXT_PRIMARY))
            self.log_table.setItem(0, 5, size_item)
            
            status_item = QTableWidgetItem("✅ Opened")
            status_item.setForeground(QColor(DT.SUCCESS_400))
            status_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
            self.log_table.setItem(0, 7, status_item)
            
    def handle_trade_close(self, ticket: int, profit: float):
        """Handle trade close with enhanced display"""
        if ticket not in self.trade_log_tickets:
            return
            
        row = self.trade_log_tickets[ticket]
        if row >= self.log_table.rowCount():
            return
            
        pl_item = QTableWidgetItem(f"${profit:+.2f}")
        pl_item.setForeground(QColor(DT.SUCCESS_400 if profit >= 0 else DT.DANGER_400))
        pl_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_BOLD))
        self.log_table.setItem(row, 6, pl_item)
        
        status_emoji = "✅" if profit >= 0 else "❌"
        status_item = QTableWidgetItem(f"{status_emoji} Closed")
        status_item.setForeground(QColor(DT.SUCCESS_400 if profit >= 0 else DT.DANGER_400))
        status_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
        self.log_table.setItem(row, 7, status_item)
        
        del self.trade_log_tickets[ticket]


class DashboardPage(QWidget):
    """
    Enhanced Dashboard Page with improved visual hierarchy and information prominence
    Main hub for auto-trading controls, statistics, and active signals.
    """
    # Signals to communicate with MainWindow/Controller
    start_trading_requested = pyqtSignal(int)  # interval
    stop_trading_requested = pyqtSignal()
    load_model_requested = pyqtSignal(str)     # symbol
    
    def __init__(self):
        super().__init__()
        self.signal_cards: Dict[str, SignalCard] = {}
        self.stat_cards: Dict[str, StatCard] = {}
        self.metrics_panel = None
        self.trade_log = None
        self.page_animator = None
        
        self._setup_ui()
        self._setup_timers()
        self._setup_animations()

    def _setup_ui(self):
        """Setup enhanced dashboard UI with better visual hierarchy"""
        # Main scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {DT.GLASS_DARK};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {DT.PRIMARY_400};
                border-radius: 4px;
                min-height: 20px;
            }}
        """)
        
        # Main container
        container = QWidget()
        scroll_area.setWidget(container)
        
        layout = QVBoxLayout(container)
        
        # Get responsive spacing
        spacing_mult = DT.get_responsive_spacing()
        margin = int(DT.SPACE_2XL * spacing_mult)
        spacing = int(DT.SPACE_LG * spacing_mult)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        # --- Enhanced Header with Status ---
        header_layout = QHBoxLayout()
        
        # Main title with enhanced styling
        header = QLabel("🤖 Auto Trading Dashboard")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"""
            color: {DT.TEXT_PRIMARY}; 
            font-family: {DT.FONT_FAMILY};
            background: transparent;
        """)
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Enhanced session timer with status
        self.session_timer_label = QLabel("⏱ Ready")
        self.session_timer_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_SEMIBOLD))
        self.session_timer_label.setStyleSheet(f"""
            color: {DT.TEXT_SECONDARY};
            background: {DT.GLASS_DARK};
            padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
            border-radius: {DT.RADIUS_SM}px;
            border: 1px solid {DT.BORDER_SUBTLE};
        """)
        header_layout.addWidget(self.session_timer_label)
        layout.addLayout(header_layout)

        # --- Enhanced Stats Row with Better Visual Hierarchy ---
        stats_container = QFrame()
        stats_container.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_SUBTLE};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_LG}px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(DT.SPACE_BASE)
        
        # Stats title
        stats_title = QLabel("📊 Performance Overview")
        stats_title.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_SEMIBOLD))
        stats_title.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        stats_layout.addWidget(stats_title)
        
        # Stats cards grid
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(spacing)
        
        # Enhanced stat cards with drill-down capability
        self.stat_cards['trades'] = StatCard("📊", "TRADES TODAY", "0", stat_type="trades")
        self.stat_cards['winrate'] = StatCard("🎯", "WIN RATE", "0%", stat_type="winrate")
        self.stat_cards['profit'] = StatCard("💰", "P&L TODAY", "$0.00", stat_type="profit")
        self.stat_cards['positions'] = StatCard("📈", "ACTIVE POS", "0", stat_type="positions")
        
        # Connect drill-down signals
        for card in self.stat_cards.values():
            card.clicked.connect(self._handle_stat_card_click)
        
        for card in self.stat_cards.values():
            stats_grid.addWidget(card)
        stats_grid.addStretch()
        
        stats_layout.addLayout(stats_grid)
        layout.addWidget(stats_container)

        # --- Enhanced Control Panel ---
        control_group = QGroupBox("🎮 Trading Control")
        control_group.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_SEMIBOLD))
        control_group.setStyleSheet(f"""
            QGroupBox {{
                color: {DT.TEXT_PRIMARY};
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
                padding-top: {DT.SPACE_LG}px;
                font-family: {DT.FONT_FAMILY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {DT.SPACE_BASE}px;
                padding: 0 {DT.SPACE_SM}px 0 {DT.SPACE_SM}px;
            }}
        """)
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(DT.SPACE_BASE)

        # Enhanced Start Button
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
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background: {StyleSheets.gradient_primary_pressed()};
                transform: translateY(1px);
            }}
            QPushButton:disabled {{
                background: {DT.GLASS_MEDIUM};
                color: {DT.TEXT_DISABLED};
            }}
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        control_layout.addWidget(self.start_btn)

        # Enhanced Stop Button
        self.stop_btn = QPushButton("⬛ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                border: none;
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_BASE}px {DT.SPACE_XL}px;
                color: white;
                font-size: {DT.FONT_BASE}px;
                font-weight: {DT.WEIGHT_BOLD};
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_danger_hover()};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                transform: translateY(1px);
            }}
            QPushButton:disabled {{
                background: {DT.GLASS_MEDIUM};
                color: {DT.TEXT_DISABLED};
            }}
        """)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()

        # Enhanced Interval Control
        interval_container = QFrame()
        interval_container.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_MEDIUM};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
            }}
        """)
        interval_layout = QHBoxLayout(interval_container)
        interval_layout.setSpacing(DT.SPACE_SM)

        interval_label = QLabel("⏱ Interval:")
        interval_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_MEDIUM))
        interval_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        interval_layout.addWidget(interval_label)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(10, 300)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" sec")
        self.interval_spin.setStyleSheet(StyleSheets.input_field())
        interval_layout.addWidget(self.interval_spin)
        
        control_layout.addWidget(interval_container)
        layout.addWidget(control_group)

        # --- Enhanced Signal Cards Section ---
        signals_container = QFrame()
        signals_container.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_SUBTLE};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_LG}px;
            }}
        """)
        signals_layout = QVBoxLayout(signals_container)
        signals_layout.setSpacing(DT.SPACE_BASE)
        
        # Signals title
        signals_title = QLabel("🎯 Live Trading Signals")
        signals_title.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_SEMIBOLD))
        signals_title.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        signals_layout.addWidget(signals_title)

        # Signal cards layout
        signals_cards_layout = QHBoxLayout()
        signals_cards_layout.setSpacing(spacing)

        # Enhanced signal cards
        for symbol in ["BTCUSD", "XAUUSD"]:
            signal_card = SignalCard(symbol)
            signal_card.load_model_clicked.connect(lambda s=symbol: self.load_model_requested.emit(s))
            self.signal_cards[symbol] = signal_card
            signals_cards_layout.addWidget(signal_card)
        
        signals_cards_layout.addStretch()
        signals_layout.addLayout(signals_cards_layout)
        layout.addWidget(signals_container)

        # --- Two-column layout for metrics and trade log ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(spacing)
        
        # Trading metrics panel
        self.metrics_panel = TradingMetricsPanel()
        bottom_layout.addWidget(self.metrics_panel, 1)
        
        # Enhanced trade log
        self.trade_log = EnhancedTradeLog()
        bottom_layout.addWidget(self.trade_log, 2)
        
        layout.addLayout(bottom_layout)
        
        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
    def _setup_timers(self):
        """Setup enhanced timers"""
        self.trading_session_start = None
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        self.session_timer.start(1000)
        
    def _setup_animations(self):
        """Setup page animations"""
        self.page_animator = PageTransitionAnimator(self)
        
    def _handle_stat_card_click(self, stat_type: str):
        """Handle stat card click for drill-down functionality"""
        logger.info(f"Stat card clicked: {stat_type}")
        # Could open detailed view, filter trade log, etc.
        
    def _on_start_clicked(self):
        """Handle start button click with enhanced feedback"""
        interval = int(self.interval_spin.value())
        self.start_trading_requested.emit(interval)
        
        # Visual feedback
        from ui.animation_system import MicroInteractionAnimator
        micro_animator = MicroInteractionAnimator(self.start_btn)
        micro_animator.button_press_feedback()
        
    def _on_stop_clicked(self):
        """Handle stop button click with enhanced feedback"""
        self.stop_trading_requested.emit()
        
        # Visual feedback
        from ui.animation_system import MicroInteractionAnimator
        micro_animator = MicroInteractionAnimator(self.stop_btn)
        micro_animator.button_press_feedback()

    def set_trading_state(self, is_running: bool):
        """Update UI based on trading state with enhanced visual feedback"""
        self.start_btn.setEnabled(not is_running)
        self.stop_btn.setEnabled(is_running)
        
        if is_running:
            self.trading_session_start = datetime.now()
            # Update signal cards to show real-time status
            for card in self.signal_cards.values():
                card.set_real_time_status(True)
        else:
            self.trading_session_start = None
            self.session_timer_label.setText("⏱ Ready")
            self.session_timer_label.setStyleSheet(f"""
                color: {DT.TEXT_SECONDARY};
                background: {DT.GLASS_DARK};
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                border-radius: {DT.RADIUS_SM}px;
                border: 1px solid {DT.BORDER_SUBTLE};
            """)
            # Update signal cards to show inactive status
            for card in self.signal_cards.values():
                card.set_real_time_status(False)

    def _update_session_timer(self):
        """Update session timer with enhanced styling"""
        if self.trading_session_start:
            elapsed = datetime.now() - self.trading_session_start
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.session_timer_label.setText(f"⏱ Active: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.session_timer_label.setStyleSheet(f"""
                color: {DT.SUCCESS_400};
                background: {DT.GLASS_DARK};
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                border-radius: {DT.RADIUS_SM}px;
                border: 1px solid {DT.SUCCESS_400};
            """)

    def update_model_status(self, symbol: str, model_id: str, accuracy: float):
        """Update signal card when model is loaded"""
        if symbol in self.signal_cards:
            self.signal_cards[symbol].set_model_loaded(model_id, accuracy)

    def update_signal(self, symbol: str, signal: str, confidence: float, timing_info: str = ""):
        """Update signal display and log with enhanced information"""
        if symbol in self.signal_cards:
            self.signal_cards[symbol].update_signal(signal, confidence, timing_info)
        
        # Add to enhanced trade log
        self.trade_log.add_log_entry(symbol, signal, confidence)

    def handle_trade_execution(self, symbol: str, signal: str, ticket: int, volume: float):
        """Handle trade execution with enhanced logging"""
        self.trade_log.handle_trade_execution(symbol, signal, ticket, volume)

    def handle_trade_close(self, ticket: int, profit: float):
        """Handle trade close with enhanced logging"""
        self.trade_log.handle_trade_close(ticket, profit)

    def update_statistics(self, total_trades: int, win_rate: float, total_profit: float, active_pos: int):
        """Update statistics with enhanced animations and sparklines"""
        # Update stat cards with animations and trend data
        self.stat_cards['trades'].update_value(str(total_trades), animated=True)
        self.stat_cards['winrate'].update_value(f"{win_rate:.1f}%", animated=True)
        
        # Enhanced P&L display with trend
        profit_trend = "+5%" if total_profit > 0 else "-2%" if total_profit < 0 else ""
        self.stat_cards['profit'].update_value(f"${total_profit:+.2f}", profit_trend, total_profit >= 0, animated=True)
        
        self.stat_cards['positions'].update_value(str(active_pos), animated=True)
        
        # Pulse highlight for significant changes
        if abs(total_profit) > 100:  # Significant profit/loss
            self.stat_cards['profit'].pulse_highlight()
            
    def update_account_metrics(self, balance: float, equity: float, margin: float, drawdown: float):
        """Update account metrics panel"""
        if self.metrics_panel:
            self.metrics_panel.update_metric("balance", f"${balance:,.2f}", DT.PRIMARY_400)
            self.metrics_panel.update_metric("equity", f"${equity:,.2f}", 
                                           DT.SUCCESS_400 if equity >= balance else DT.DANGER_400)
            self.metrics_panel.update_metric("margin", f"${margin:,.2f}", DT.WARNING_400)
            self.metrics_panel.update_metric("drawdown", f"{drawdown:.1f}%", 
                                           DT.SUCCESS_400 if drawdown < 5 else DT.DANGER_400)
