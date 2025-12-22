from typing import Dict, Optional, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.design_system import DesignTokens as DT, StyleSheets
from ui.components.stat_card import StatCard
from ui.components.signal_card import SignalCard
from loguru import logger

class DashboardPage(QWidget):
    """
    Dashboard Page
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
        self.trade_log_tickets: Dict[int, int] = {} # ticket -> row index
        
        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Get responsive spacing
        spacing_mult = DT.get_responsive_spacing()
        margin = int(DT.SPACE_2XL * spacing_mult)
        spacing = int(DT.SPACE_LG * spacing_mult)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)

        # --- Header ---
        header_layout = QHBoxLayout()
        header = QLabel("🤖 Auto Trading Dashboard")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Session timer
        self.session_timer_label = QLabel("⏱ Ready")
        self.session_timer_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_SEMIBOLD))
        self.session_timer_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")
        header_layout.addWidget(self.session_timer_label)
        layout.addLayout(header_layout)

        # --- Stats Row ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(spacing)
        
        self.stat_cards['trades'] = StatCard("📊", "TRADES TODAY", "0")
        self.stat_cards['winrate'] = StatCard("🎯", "WIN RATE", "0%")
        self.stat_cards['profit'] = StatCard("💰", "P&L TODAY", "$0.00")
        self.stat_cards['positions'] = StatCard("📈", "ACTIVE POS", "0")
        
        for card in self.stat_cards.values():
            stats_layout.addWidget(card)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # --- Control Panel ---
        control_group = QGroupBox("Trading Control")
        control_layout = QHBoxLayout(control_group)

        # Start Button
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
        self.start_btn.clicked.connect(self._on_start_clicked)
        control_layout.addWidget(self.start_btn)

        # Stop Button
        self.stop_btn = QPushButton("⬛ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(DT.BUTTON_HEIGHT_LG)
        self.stop_btn.setStyleSheet(StyleSheets.danger_button())
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()

        # Interval
        interval_label = QLabel("Interval:")
        interval_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; font-family: {DT.FONT_FAMILY};")
        control_layout.addWidget(interval_label)

        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(10, 300)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" sec")
        control_layout.addWidget(self.interval_spin)

        layout.addWidget(control_group)

        # --- Signal Cards ---
        signals_layout = QHBoxLayout()
        signals_layout.setSpacing(spacing)

        for symbol in ["BTCUSD", "XAUUSD"]:
            signal_card = SignalCard(symbol)
            # Forward signal
            signal_card.load_model_clicked.connect(lambda s=symbol: self.load_model_requested.emit(s))
            self.signal_cards[symbol] = signal_card
            signals_layout.addWidget(signal_card)
        
        signals_layout.addStretch()
        layout.addLayout(signals_layout)

        # --- Trade Log ---
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
        
    def _setup_timers(self):
        self.trading_session_start = None
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)
        self.session_timer.start(1000)

    def _on_start_clicked(self):
        interval = int(self.interval_spin.value())
        self.start_trading_requested.emit(interval)
        
    def _on_stop_clicked(self):
        self.stop_trading_requested.emit()

    def set_trading_state(self, is_running: bool):
        """Update UI based on trading state"""
        self.start_btn.setEnabled(not is_running)
        self.stop_btn.setEnabled(is_running)
        
        if is_running:
            self.trading_session_start = datetime.now()
        else:
            self.trading_session_start = None
            self.session_timer_label.setText("⏱ Ready")
            self.session_timer_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")

    def _update_session_timer(self):
        if self.trading_session_start:
            elapsed = datetime.now() - self.trading_session_start
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.session_timer_label.setText(f"⏱ Active: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.session_timer_label.setStyleSheet(f"color: {DT.SUCCESS};")

    def update_model_status(self, symbol: str, model_id: str, accuracy: float):
        """Update signal card when model is loaded"""
        if symbol in self.signal_cards:
            self.signal_cards[symbol].set_model_loaded(model_id, accuracy)

    def update_signal(self, symbol: str, signal: str, confidence: float):
        """Update signal display and log"""
        if symbol in self.signal_cards:
            self.signal_cards[symbol].update_signal(signal, confidence)
        self._add_log_entry(symbol, signal, confidence)

    def _add_log_entry(self, symbol: str, signal: str, confidence: float):
        # Increment existing ticket row indices
        for ticket in self.trade_log_tickets:
            self.trade_log_tickets[ticket] += 1
            
        self.log_table.insertRow(0)
        
        # Time
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        time_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM))
        self.log_table.setItem(0, 0, time_item)
        
        # Symbol
        symbol_item = QTableWidgetItem(symbol)
        symbol_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
        self.log_table.setItem(0, 1, symbol_item)
        
        # Signal
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
        self.log_table.setItem(0, 3, conf_item)
        
        # Placeholders
        self.log_table.setItem(0, 4, QTableWidgetItem("-")) # Action
        self.log_table.setItem(0, 5, QTableWidgetItem("-")) # P&L
        self.log_table.setItem(0, 6, QTableWidgetItem("Signal")) # Status

        # Limit rows
        while self.log_table.rowCount() > 50:
            self.log_table.removeRow(self.log_table.rowCount() - 1)

    def handle_trade_execution(self, symbol: str, signal: str, ticket: int, volume: float):
        """Update log when trade is executed"""
        if self.log_table.rowCount() > 0:
            self.trade_log_tickets[ticket] = 0
            
            action_item = QTableWidgetItem(f"#{ticket}")
            action_item.setForeground(QColor(DT.PRIMARY))
            self.log_table.setItem(0, 4, action_item)
            
            status_item = QTableWidgetItem("✅ Opened")
            status_item.setForeground(QColor(DT.SUCCESS))
            self.log_table.setItem(0, 6, status_item)

    def handle_trade_close(self, ticket: int, profit: float):
        """Update log when trade is closed"""
        if ticket not in self.trade_log_tickets:
            return
            
        row = self.trade_log_tickets[ticket]
        if row >= self.log_table.rowCount():
            return
            
        pl_item = QTableWidgetItem(f"${profit:+.2f}")
        pl_item.setForeground(QColor(DT.SUCCESS if profit >= 0 else DT.DANGER))
        self.log_table.setItem(row, 5, pl_item)
        
        status_item = QTableWidgetItem("✅ Closed" if profit >= 0 else "❌ Closed")
        self.log_table.setItem(row, 6, status_item)
        
        del self.trade_log_tickets[ticket]

    def update_statistics(self, total_trades: int, win_rate: float, total_profit: float, active_pos: int):
        """Update top status cards"""
        self.stat_cards['trades'].update_value(str(total_trades), "", True)
        self.stat_cards['winrate'].update_value(f"{win_rate:.1f}%")
        self.stat_cards['profit'].update_value(f"${total_profit:+.2f}", "", total_profit >= 0)
        self.stat_cards['positions'].update_value(str(active_pos))
