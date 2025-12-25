"""
SignalCard - Enhanced Signal Display Card
Shows current signal with model info, confidence, statistics, real-time indicators, and mini-charts
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen, QColor
from ui.design_system import DesignTokens as DT, StyleSheets
from ui.animation_system import AnimationUtils, HoverAnimator, MicroInteractionAnimator
from datetime import datetime
import math


class ConfidenceMeter(QWidget):
    """Real-time confidence meter with animated progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.confidence = 0.0
        self.target_confidence = 0.0
        self.animation = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the confidence meter UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(DT.SPACE_XS)
        
        # Label
        self.label = QLabel("Confidence")
        self.label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_MEDIUM))
        self.label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self.label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {DT.SUCCESS_400}, 
                    stop:0.7 {DT.WARNING_400}, 
                    stop:1 {DT.DANGER_400}
                );
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Percentage label
        self.percentage_label = QLabel("0%")
        self.percentage_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_SEMIBOLD))
        self.percentage_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.percentage_label)
        
    def set_confidence(self, confidence: float, animated: bool = True):
        """Set confidence value with optional animation"""
        self.target_confidence = max(0.0, min(1.0, confidence))
        
        if animated and self.confidence != self.target_confidence:
            self._animate_to_target()
        else:
            self.confidence = self.target_confidence
            self._update_display()
            
    def _animate_to_target(self):
        """Animate confidence change"""
        if self.animation:
            self.animation.stop()
            
        self.animation = QPropertyAnimation(self, b"confidence")
        self.animation.setDuration(DT.DURATION_SLOW)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setStartValue(self.confidence)
        self.animation.setEndValue(self.target_confidence)
        self.animation.valueChanged.connect(self._update_display)
        self.animation.start()
        
    def _update_display(self):
        """Update the visual display"""
        percentage = int(self.confidence * 100)
        self.progress_bar.setValue(percentage)
        self.percentage_label.setText(f"{percentage}%")
        
        # Update color based on confidence level
        if self.confidence >= 0.8:
            color = DT.SUCCESS_400
        elif self.confidence >= 0.6:
            color = DT.WARNING_400
        else:
            color = DT.DANGER_400
            
        self.percentage_label.setStyleSheet(f"color: {color}; background: transparent;")


class MiniChart(QWidget):
    """Mini sparkline chart for historical performance"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = []
        self.max_points = 20
        self.setFixedSize(120, 40)
        
    def add_data_point(self, value: float):
        """Add a new data point to the chart"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()
        
    def set_data(self, data: list):
        """Set all data points at once"""
        self.data_points = data[-self.max_points:] if len(data) > self.max_points else data[:]
        self.update()
        
    def paintEvent(self, event):
        """Paint the mini chart"""
        if not self.data_points or len(self.data_points) < 2:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width() - 4
        height = self.height() - 4
        
        # Find min/max for scaling
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Set up pen
        pen = QPen(QColor(DT.PRIMARY_400))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw the line
        points = []
        for i, value in enumerate(self.data_points):
            x = 2 + (i * width / (len(self.data_points) - 1))
            y = 2 + height - ((value - min_val) / val_range * height)
            points.append((x, y))
            
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), 
                           int(points[i+1][0]), int(points[i+1][1]))


class SignalCard(QFrame):
    """Enhanced signal card with real-time indicators, confidence meters, and mini-charts"""

    load_model_clicked = pyqtSignal(str)  # symbol

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.model_loaded = False
        self.model_info = {}
        self.signal_data = {}
        self.performance_history = []
        
        # Animation components
        self.hover_animator = None
        self.micro_animator = None
        
        self._setup_ui()
        self._setup_animations()
        self._setup_timers()

    def _setup_ui(self):
        """Setup the enhanced card UI"""
        # Get responsive card sizes
        card_sizes = DT.get_responsive_card_sizes()
        min_w, min_h = card_sizes['signal_card']

        # Enhanced card styling with glass morphism
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {DT.GLASS_MEDIUM}, stop:1 {DT.GLASS_DARKEST}
                );
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_2XL}px;
                backdrop-filter: blur({DT.BLUR_SM}px);
            }}
        """)
        self.setMinimumWidth(min_w)
        self.setMinimumHeight(min_h + 60)  # Extra height for new components

        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_XL, DT.SPACE_XL, DT.SPACE_XL, DT.SPACE_XL)
        layout.setSpacing(DT.SPACE_BASE)

        # Header: Symbol with real-time indicator
        header_layout = QHBoxLayout()

        # Icon based on symbol
        if 'BTC' in self.symbol:
            icon = "₿"
            accent_color = DT.WARNING_400
        elif 'XAU' in self.symbol or 'GOLD' in self.symbol:
            icon = "🥇"
            accent_color = DT.WARNING_500
        else:
            icon = "📊"
            accent_color = DT.PRIMARY_400

        sym_label = QLabel(f"{icon} {self.symbol}")
        sym_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL, DT.WEIGHT_BOLD))
        sym_label.setStyleSheet(f"color: {accent_color}; background: transparent;")
        header_layout.addWidget(sym_label)
        
        # Real-time status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM))
        self.status_indicator.setStyleSheet(f"color: {DT.TEXT_DISABLED}; background: transparent;")
        header_layout.addWidget(self.status_indicator)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Model info with enhanced styling
        self.model_name_label = QLabel("No model loaded")
        self.model_name_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_MEDIUM))
        self.model_name_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(self.model_name_label)

        self.model_accuracy_label = QLabel("")
        self.model_accuracy_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        self.model_accuracy_label.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.model_accuracy_label)

        # Signal indicator with enhanced styling and timing
        signal_container = QFrame()
        signal_container.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARKEST};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: {DT.RADIUS_XL}px;
                padding: {DT.SPACE_LG}px;
            }}
        """)
        signal_layout = QVBoxLayout(signal_container)
        signal_layout.setContentsMargins(DT.SPACE_MD, DT.SPACE_MD, DT.SPACE_MD, DT.SPACE_MD)
        signal_layout.setSpacing(DT.SPACE_SM)
        
        self.signal_label = QLabel("WAITING")
        self.signal_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        self.signal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signal_label.setStyleSheet(f"color: {DT.TEXT_PLACEHOLDER}; background: transparent;")
        signal_layout.addWidget(self.signal_label)
        
        # Signal timing info
        self.signal_timing_label = QLabel("")
        self.signal_timing_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        self.signal_timing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signal_timing_label.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        signal_layout.addWidget(self.signal_timing_label)
        
        layout.addWidget(signal_container)

        # Confidence meter
        self.confidence_meter = ConfidenceMeter()
        layout.addWidget(self.confidence_meter)

        # Mini performance chart
        chart_container = QFrame()
        chart_container.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_SUBTLE};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_SM}px;
            }}
        """)
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(DT.SPACE_SM, DT.SPACE_SM, DT.SPACE_SM, DT.SPACE_SM)
        chart_layout.setSpacing(DT.SPACE_XS)
        
        chart_label = QLabel("Performance")
        chart_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_MEDIUM))
        chart_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        chart_layout.addWidget(chart_label)
        
        self.mini_chart = MiniChart()
        chart_layout.addWidget(self.mini_chart, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(chart_container)

        # Statistics with enhanced layout
        self.stats_label = QLabel("")
        self.stats_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        layout.addWidget(self.stats_label)

        # Enhanced load model button
        self.load_btn = QPushButton(f"🔄 Load {self.symbol} Model")
        self.load_btn.setFixedHeight(DT.BUTTON_HEIGHT_SM)
        self.load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                color: white;
                border: none;
                border-radius: {DT.RADIUS_SM}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                font-weight: {DT.WEIGHT_SEMIBOLD};
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
            QPushButton:pressed {{
                background: {StyleSheets.gradient_primary_pressed()};
            }}
        """)
        self.load_btn.clicked.connect(lambda: self.load_model_clicked.emit(self.symbol))
        layout.addWidget(self.load_btn)

        layout.addStretch()
        
    def _setup_animations(self):
        """Setup hover and micro-interaction animations"""
        # Hover animation
        self.hover_animator = HoverAnimator(self)
        self.hover_animator.set_hover_effects(
            scale_factor=1.02,
            glow_enabled=True,
            glow_color=DT.PRIMARY_400,
            shadow_enabled=True
        )
        
        # Micro-interaction animator
        self.micro_animator = MicroInteractionAnimator(self)
        
    def _setup_timers(self):
        """Setup timers for real-time updates"""
        # Status indicator animation timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._animate_status_indicator)
        
        # Time update timer
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_last_signal_time)
        self.time_timer.start(30000)  # Update every 30 seconds
        
    def _animate_status_indicator(self):
        """Animate the status indicator for real-time feel"""
        if self.model_loaded:
            # Pulse animation for active status
            current_color = self.status_indicator.styleSheet()
            if DT.SUCCESS_400 in current_color:
                self.status_indicator.setStyleSheet(f"color: {DT.SUCCESS_600}; background: transparent;")
            else:
                self.status_indicator.setStyleSheet(f"color: {DT.SUCCESS_400}; background: transparent;")

    def set_model_loaded(self, model_name: str, accuracy: float):
        """Update UI when model is loaded with enhanced feedback"""
        self.model_loaded = True
        self.model_info = {'name': model_name, 'accuracy': accuracy}

        # Enhanced model info display
        self.model_name_label.setText(f"Model: {model_name}")
        self.model_accuracy_label.setText(f"Accuracy: {accuracy:.1%}")
        self.model_accuracy_label.setStyleSheet(f"color: {DT.SUCCESS_400}; background: transparent;")

        # Update signal to LOADED with animation
        self.signal_label.setText("LOADED")
        self.signal_label.setStyleSheet(f"color: {DT.SUCCESS_400}; background: transparent;")
        
        # Start status indicator animation
        self.status_indicator.setStyleSheet(f"color: {DT.SUCCESS_400}; background: transparent;")
        self.status_timer.start(1000)  # Pulse every second

        # Hide load button with fade animation
        fade_out = AnimationUtils.create_fade_animation(self.load_btn, False)
        fade_out.finished.connect(self.load_btn.hide)
        fade_out.start()
        
        # Success feedback
        self.micro_animator.success_feedback()

    def update_signal(self, signal: str, confidence: float, timing_info: str = ""):
        """Update the current signal with enhanced visual feedback"""
        self.signal_data = {
            'signal': signal,
            'confidence': confidence,
            'time': datetime.now(),
            'timing': timing_info
        }

        # Update signal label with enhanced styling
        signal_upper = signal.upper()

        # Enhanced color coding and emojis
        if signal_upper == 'BUY':
            signal_color = DT.SUCCESS_400
            signal_emoji = "🟢"
            glow_color = DT.SUCCESS_400
        elif signal_upper == 'SELL':
            signal_color = DT.DANGER_400
            signal_emoji = "🔴"
            glow_color = DT.DANGER_400
        else:  # HOLD
            signal_color = DT.WARNING_400
            signal_emoji = "⚪"
            glow_color = DT.WARNING_400

        self.signal_label.setText(f"{signal_upper} {signal_emoji}")
        self.signal_label.setStyleSheet(f"color: {signal_color}; background: transparent;")
        
        # Update timing information
        if timing_info:
            self.signal_timing_label.setText(timing_info)
        else:
            self.signal_timing_label.setText("Signal generated")

        # Update confidence meter with animation
        self.confidence_meter.set_confidence(confidence, animated=True)
        
        # Add to performance history and update chart
        self.performance_history.append(confidence)
        self.mini_chart.add_data_point(confidence)

        # Update last signal time
        self.update_last_signal_time()
        
        # Visual feedback based on signal strength
        if confidence >= 0.8:
            self.micro_animator.success_feedback()
        elif confidence < 0.4:
            self.micro_animator.attention_pulse(2)

    def update_statistics(self, win_rate: float, total_trades: int, avg_confidence: float = 0.0):
        """Update trading statistics with enhanced display"""
        stats_text = f"Win Rate: {win_rate:.1f}% • {total_trades} trades"
        if avg_confidence > 0:
            stats_text += f" • Avg Confidence: {avg_confidence:.1f}%"
        self.stats_label.setText(stats_text)

    def update_last_signal_time(self):
        """Update the 'last signal' time display with enhanced formatting"""
        if not self.signal_data:
            return

        signal_time = self.signal_data.get('time')
        if not signal_time:
            return

        # Calculate time ago with more precise formatting
        time_diff = datetime.now() - signal_time
        seconds = int(time_diff.total_seconds())

        if seconds < 60:
            time_text = f"Last: {seconds}s ago"
            color = DT.SUCCESS_400  # Recent signal
        elif seconds < 3600:
            minutes = seconds // 60
            time_text = f"Last: {minutes}m ago"
            color = DT.WARNING_400  # Moderate age
        else:
            hours = seconds // 3600
            time_text = f"Last: {hours}h ago"
            color = DT.DANGER_400  # Old signal

        # Update with color coding
        timing_label = getattr(self, 'signal_timing_label', None)
        if timing_label:
            timing_label.setText(time_text)
            timing_label.setStyleSheet(f"color: {color}; background: transparent;")
            
    def set_real_time_status(self, is_active: bool):
        """Set real-time connection status"""
        if is_active:
            self.status_indicator.setStyleSheet(f"color: {DT.SUCCESS_400}; background: transparent;")
            if not self.status_timer.isActive():
                self.status_timer.start(1000)
        else:
            self.status_indicator.setStyleSheet(f"color: {DT.DANGER_400}; background: transparent;")
            self.status_timer.stop()
