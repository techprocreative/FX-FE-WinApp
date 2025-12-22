"""
SignalCard - Enhanced Signal Display Card
Shows current signal with model info, confidence, statistics
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ui.design_system import DesignTokens as DT
from datetime import datetime


class SignalCard(QFrame):
    """Enhanced signal card with detailed model and performance info"""

    load_model_clicked = pyqtSignal(str)  # symbol

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.model_loaded = False
        self.model_info = {}
        self.signal_data = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the card UI"""
        # Get responsive card sizes
        card_sizes = DT.get_responsive_card_sizes()
        min_w, min_h = card_sizes['signal_card']

        # Card styling
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {DT.GLASS_MEDIUM}, stop:1 {DT.GLASS_DARKEST}
                );
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_2XL}px;
            }}
        """)
        self.setMinimumWidth(min_w)
        self.setMinimumHeight(min_h)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_XL, DT.SPACE_XL, DT.SPACE_XL, DT.SPACE_XL)
        layout.setSpacing(DT.SPACE_BASE)

        # Header: Symbol
        header_layout = QHBoxLayout()

        # Icon based on symbol
        if 'BTC' in self.symbol:
            icon = "₿"
        elif 'XAU' in self.symbol or 'GOLD' in self.symbol:
            icon = "🥇"
        else:
            icon = "📊"

        sym_label = QLabel(f"{icon} {self.symbol}")
        sym_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL, DT.WEIGHT_BOLD))
        sym_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        header_layout.addWidget(sym_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Model info
        self.model_name_label = QLabel("No model loaded")
        self.model_name_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM))
        self.model_name_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self.model_name_label)

        self.model_accuracy_label = QLabel("")
        self.model_accuracy_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        self.model_accuracy_label.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.model_accuracy_label)

        # Signal indicator (large)
        self.signal_label = QLabel("WAITING")
        self.signal_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_4XL, DT.WEIGHT_BOLD))
        self.signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signal_label.setStyleSheet(f"""
            color: {DT.TEXT_PLACEHOLDER};
            background: {DT.GLASS_DARKEST};
            border-radius: {DT.RADIUS_XL}px;
            padding: {DT.SPACE_XL}px;
        """)
        layout.addWidget(self.signal_label)

        # Confidence indicator
        self.confidence_label = QLabel("")
        self.confidence_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
        self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confidence_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self.confidence_label)

        # Last signal time
        self.last_signal_label = QLabel("")
        self.last_signal_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        self.last_signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_signal_label.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.last_signal_label)

        # Statistics
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.stats_label)

        # Load model button (initially visible)
        self.load_btn = QPushButton(f"🔄 Load {self.symbol} Model")
        self.load_btn.setFixedHeight(DT.BUTTON_HEIGHT_SM)
        self.load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.PRIMARY};
                color: white;
                border: none;
                border-radius: {DT.RADIUS_SM}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                font-weight: {DT.WEIGHT_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {DT.PRIMARY_DARK};
            }}
        """)
        self.load_btn.clicked.connect(lambda: self.load_model_clicked.emit(self.symbol))
        layout.addWidget(self.load_btn)

        layout.addStretch()

    def set_model_loaded(self, model_name: str, accuracy: float):
        """Update UI when model is loaded"""
        self.model_loaded = True
        self.model_info = {'name': model_name, 'accuracy': accuracy}

        self.model_name_label.setText(f"Model: {model_name}")
        self.model_accuracy_label.setText(f"Accuracy: {accuracy:.1%}")
        self.model_accuracy_label.setStyleSheet(f"color: {DT.SUCCESS};")

        # Update signal to LOADED
        self.signal_label.setText("LOADED")
        self.signal_label.setStyleSheet(f"""
            color: {DT.SUCCESS};
            background: {DT.GLASS_DARKEST};
            border-radius: {DT.RADIUS_XL}px;
            padding: {DT.SPACE_XL}px;
        """)

        # Hide load button
        self.load_btn.hide()

    def update_signal(self, signal: str, confidence: float):
        """Update the current signal and confidence"""
        self.signal_data = {
            'signal': signal,
            'confidence': confidence,
            'time': datetime.now()
        }

        # Update signal label
        signal_upper = signal.upper()

        # Color coding
        if signal_upper == 'BUY':
            signal_color = DT.SUCCESS
            signal_emoji = "🟢"
        elif signal_upper == 'SELL':
            signal_color = DT.DANGER
            signal_emoji = "🔴"
        else:  # HOLD
            signal_color = DT.TEXT_PLACEHOLDER
            signal_emoji = "⚪"

        self.signal_label.setText(f"{signal_upper} {signal_emoji}")
        self.signal_label.setStyleSheet(f"""
            color: {signal_color};
            background: {DT.GLASS_DARKEST};
            border-radius: {DT.RADIUS_XL}px;
            padding: {DT.SPACE_XL}px;
        """)

        # Update confidence
        conf_pct = confidence * 100
        self.confidence_label.setText(f"Confidence: {conf_pct:.0f}%")

        # Update last signal time
        self.last_signal_label.setText(f"Last: just now")

    def update_statistics(self, win_rate: float, total_trades: int):
        """Update trading statistics for this symbol"""
        self.stats_label.setText(f"Win Rate: {win_rate:.1f}% ({total_trades} trades)")

    def update_last_signal_time(self):
        """Update the 'last signal' time display (call periodically)"""
        if not self.signal_data:
            return

        signal_time = self.signal_data.get('time')
        if not signal_time:
            return

        # Calculate time ago
        time_diff = datetime.now() - signal_time
        seconds = int(time_diff.total_seconds())

        if seconds < 60:
            time_text = f"Last: {seconds}s ago"
        elif seconds < 3600:
            minutes = seconds // 60
            time_text = f"Last: {minutes}m ago"
        else:
            hours = seconds // 3600
            time_text = f"Last: {hours}h ago"

        self.last_signal_label.setText(time_text)
