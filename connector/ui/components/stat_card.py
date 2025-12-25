"""
StatCard - Enhanced Statistics Display Card
Shows key metrics with icon, value, trend indicator, animated counters, and sparkline visualizations
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QColor, QLinearGradient
from ui.design_system import DesignTokens as DT, StyleSheets
from ui.animation_system import AnimationUtils, HoverAnimator
import math


class AnimatedCounter(QLabel):
    """Animated counter that smoothly transitions between values"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_value = 0.0
        self.target_value = 0.0
        self.is_currency = False
        self.is_percentage = False
        self.decimal_places = 0
        self.animation = None
        
    def set_value(self, value: float, animated: bool = True, is_currency: bool = False, 
                  is_percentage: bool = False, decimal_places: int = 0):
        """Set the counter value with optional animation"""
        self.target_value = value
        self.is_currency = is_currency
        self.is_percentage = is_percentage
        self.decimal_places = decimal_places
        
        if animated and self.current_value != self.target_value:
            self._animate_to_target()
        else:
            self.current_value = self.target_value
            self._update_display()
            
    def _animate_to_target(self):
        """Animate the counter to target value"""
        if self.animation:
            self.animation.stop()
            
        self.animation = QPropertyAnimation(self, b"current_value")
        self.animation.setDuration(DT.DURATION_SLOW)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setStartValue(self.current_value)
        self.animation.setEndValue(self.target_value)
        self.animation.valueChanged.connect(self._update_display)
        self.animation.start()
        
    def _update_display(self):
        """Update the displayed value"""
        if self.is_currency:
            if abs(self.current_value) >= 1000:
                display_value = f"${self.current_value/1000:.1f}K"
            else:
                display_value = f"${self.current_value:.{self.decimal_places}f}"
        elif self.is_percentage:
            display_value = f"{self.current_value:.{self.decimal_places}f}%"
        else:
            if abs(self.current_value) >= 1000:
                display_value = f"{self.current_value/1000:.1f}K"
            else:
                display_value = f"{self.current_value:.{self.decimal_places}f}"
                
        self.setText(display_value)


class TrendArrow(QLabel):
    """Animated trend arrow with smooth transitions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trend_direction = 0  # -1: down, 0: neutral, 1: up
        self.trend_strength = 0.0  # 0.0 to 1.0
        self.animation = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the trend arrow UI"""
        self.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_BOLD))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("—")
        self.setStyleSheet(f"color: {DT.TEXT_MUTED}; background: transparent;")
        
    def set_trend(self, direction: int, strength: float = 0.5, animated: bool = True):
        """Set trend direction and strength"""
        self.trend_direction = max(-1, min(1, direction))
        self.trend_strength = max(0.0, min(1.0, strength))
        
        if animated:
            self._animate_trend_change()
        else:
            self._update_display()
            
    def _animate_trend_change(self):
        """Animate trend change with bounce effect"""
        if self.animation:
            self.animation.stop()
            
        # Scale animation for emphasis
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(DT.DURATION_NORMAL)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        current_geo = self.geometry()
        # Slightly scale up then back to normal
        scaled_geo = current_geo.adjusted(-2, -2, 2, 2)
        
        self.animation.setStartValue(current_geo)
        self.animation.setKeyValueAt(0.5, scaled_geo)
        self.animation.setEndValue(current_geo)
        self.animation.finished.connect(self._update_display)
        self.animation.start()
        
    def _update_display(self):
        """Update the arrow display"""
        if self.trend_direction > 0:
            # Up trend
            if self.trend_strength >= 0.8:
                arrow = "⬆️"
                color = DT.SUCCESS_400
            elif self.trend_strength >= 0.5:
                arrow = "↗️"
                color = DT.SUCCESS_500
            else:
                arrow = "↑"
                color = DT.SUCCESS_600
        elif self.trend_direction < 0:
            # Down trend
            if self.trend_strength >= 0.8:
                arrow = "⬇️"
                color = DT.DANGER_400
            elif self.trend_strength >= 0.5:
                arrow = "↘️"
                color = DT.DANGER_500
            else:
                arrow = "↓"
                color = DT.DANGER_600
        else:
            # Neutral
            arrow = "—"
            color = DT.TEXT_MUTED
            
        self.setText(arrow)
        self.setStyleSheet(f"color: {color}; background: transparent;")


class SparklineChart(QWidget):
    """Mini sparkline chart for trend visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = []
        self.max_points = 15
        self.trend_color = DT.PRIMARY_400
        self.setFixedSize(80, 30)
        
    def add_data_point(self, value: float):
        """Add a new data point"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()
        
    def set_data(self, data: list):
        """Set all data points"""
        self.data_points = data[-self.max_points:] if len(data) > self.max_points else data[:]
        self.update()
        
    def set_trend_color(self, color: str):
        """Set the trend line color"""
        self.trend_color = color
        self.update()
        
    def paintEvent(self, event):
        """Paint the sparkline"""
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
        
        # Create gradient for the line
        gradient = QLinearGradient(0, 0, width, 0)
        gradient.setColorAt(0, QColor(self.trend_color))
        gradient.setColorAt(1, QColor(DT.PRIMARY_600))
        
        # Set up pen
        pen = QPen(QColor(self.trend_color))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw the sparkline
        points = []
        for i, value in enumerate(self.data_points):
            x = 2 + (i * width / (len(self.data_points) - 1))
            y = 2 + height - ((value - min_val) / val_range * height)
            points.append((x, y))
            
        # Draw lines between points
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), 
                           int(points[i+1][0]), int(points[i+1][1]))
            
        # Draw dots at data points for emphasis
        painter.setBrush(QColor(self.trend_color))
        for x, y in points[-3:]:  # Only last 3 points
            painter.drawEllipse(int(x-1), int(y-1), 2, 2)


class StatCard(QFrame):
    """Enhanced statistics card with animated counters, trend arrows, and sparkline visualizations"""
    
    # Signal for when card is clicked (for drill-down functionality)
    clicked = pyqtSignal(str)  # stat_type

    def __init__(self, icon: str, title: str, value: str, trend: str = "",
                 trend_positive: bool = True, stat_type: str = "", parent=None):
        """
        Args:
            icon: Emoji icon for the stat
            title: Stat title (e.g., "TOTAL TRADES")
            value: Main value to display (e.g., "8")
            trend: Trend indicator (e.g., "+3", "-2", "")
            trend_positive: Whether trend is positive (green) or negative (red)
            stat_type: Type identifier for the statistic
        """
        super().__init__(parent)
        self.title_text = title
        self.icon_text = icon
        self.stat_type = stat_type
        self.trend_history = []
        self.hover_animator = None
        
        self._setup_ui(icon, title, value, trend, trend_positive)
        self._setup_animations()

    def _setup_ui(self, icon: str, title: str, value: str, trend: str, trend_positive: bool):
        """Setup the enhanced card UI"""
        # Get responsive card sizes
        card_sizes = DT.get_responsive_card_sizes()
        min_w, min_h = card_sizes['stat_card']

        # Enhanced card styling with glass morphism and hover effects
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DT.GLASS_DARK}, stop:1 {DT.GLASS_DARKEST}
                );
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_LG}px;
                backdrop-filter: blur({DT.BLUR_SM}px);
            }}
            QFrame:hover {{
                border-color: {DT.BORDER_FOCUS};
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DT.GLASS_MEDIUM}, stop:1 {DT.GLASS_DARK}
                );
            }}
        """)
        self.setMinimumWidth(min_w)
        self.setMinimumHeight(min_h + 20)  # Extra height for sparkline
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_BASE, DT.SPACE_BASE, DT.SPACE_BASE, DT.SPACE_BASE)
        layout.setSpacing(DT.SPACE_SM)

        # Header: Icon + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(DT.SPACE_SM)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL))
        icon_label.setStyleSheet("background: transparent;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_SEMIBOLD))
        title_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Value + Trend layout
        value_trend_layout = QHBoxLayout()
        value_trend_layout.setSpacing(DT.SPACE_SM)

        # Animated counter
        self.animated_counter = AnimatedCounter()
        self.animated_counter.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        self.animated_counter.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; background: transparent;")
        
        # Parse initial value
        self._parse_and_set_value(value)
        value_trend_layout.addWidget(self.animated_counter)

        # Trend arrow
        self.trend_arrow = TrendArrow()
        if trend:
            trend_direction = 1 if trend_positive else -1
            trend_strength = min(1.0, abs(float(trend.replace('+', '').replace('-', '').replace('%', '').replace('$', ''))) / 10.0)
            self.trend_arrow.set_trend(trend_direction, trend_strength, animated=False)
        value_trend_layout.addWidget(self.trend_arrow)

        value_trend_layout.addStretch()
        layout.addLayout(value_trend_layout)

        # Sparkline chart
        self.sparkline = SparklineChart()
        # Set color based on stat type
        if 'profit' in title.lower() or 'p&l' in title.lower():
            self.sparkline.set_trend_color(DT.SUCCESS_400)
        elif 'loss' in title.lower():
            self.sparkline.set_trend_color(DT.DANGER_400)
        else:
            self.sparkline.set_trend_color(DT.PRIMARY_400)
            
        layout.addWidget(self.sparkline, alignment=Qt.AlignmentFlag.AlignCenter)

        # Trend percentage (if applicable)
        if trend:
            self.trend_label = QLabel(trend)
            self.trend_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_MEDIUM))
            trend_color = DT.SUCCESS_400 if trend_positive else DT.DANGER_400
            self.trend_label.setStyleSheet(f"color: {trend_color}; background: transparent;")
            self.trend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.trend_label)
        else:
            self.trend_label = None

        layout.addStretch()
        
    def _setup_animations(self):
        """Setup hover animations"""
        self.hover_animator = HoverAnimator(self)
        self.hover_animator.set_hover_effects(
            scale_factor=1.03,
            glow_enabled=True,
            glow_color=DT.PRIMARY_400,
            shadow_enabled=True
        )

    def _parse_and_set_value(self, value_str: str):
        """Parse value string and set up animated counter"""
        # Remove common formatting
        clean_value = value_str.replace(',', '').replace('$', '').replace('%', '').replace('K', '000')
        
        try:
            numeric_value = float(clean_value)
            is_currency = '$' in value_str
            is_percentage = '%' in value_str
            is_thousands = 'K' in value_str
            
            if is_thousands:
                numeric_value *= 1000
                
            decimal_places = 2 if is_currency else (1 if is_percentage else 0)
            
            self.animated_counter.set_value(
                numeric_value, 
                animated=False, 
                is_currency=is_currency,
                is_percentage=is_percentage,
                decimal_places=decimal_places
            )
        except ValueError:
            # If parsing fails, just set as text
            self.animated_counter.setText(value_str)

    def update_value(self, value: str, trend: str = "", trend_positive: bool = True, animated: bool = True):
        """Update the card value and trend with enhanced animations"""
        # Parse and update the animated counter
        clean_value = value.replace(',', '').replace('$', '').replace('%', '').replace('K', '000')
        
        try:
            numeric_value = float(clean_value)
            is_currency = '$' in value
            is_percentage = '%' in value
            is_thousands = 'K' in value
            
            if is_thousands:
                numeric_value *= 1000
                
            decimal_places = 2 if is_currency else (1 if is_percentage else 0)
            
            # Add to trend history for sparkline
            self.trend_history.append(numeric_value)
            self.sparkline.add_data_point(numeric_value)
            
            self.animated_counter.set_value(
                numeric_value, 
                animated=animated, 
                is_currency=is_currency,
                is_percentage=is_percentage,
                decimal_places=decimal_places
            )
        except ValueError:
            self.animated_counter.setText(value)

        # Update trend arrow
        if trend:
            trend_direction = 1 if trend_positive else -1
            try:
                trend_value = abs(float(trend.replace('+', '').replace('-', '').replace('%', '').replace('$', '')))
                trend_strength = min(1.0, trend_value / 10.0)
            except ValueError:
                trend_strength = 0.5
                
            self.trend_arrow.set_trend(trend_direction, trend_strength, animated=animated)
            
            # Update trend label
            if self.trend_label:
                trend_color = DT.SUCCESS_400 if trend_positive else DT.DANGER_400
                self.trend_label.setText(trend)
                self.trend_label.setStyleSheet(f"color: {trend_color}; background: transparent;")
        elif self.trend_label:
            # Hide trend label if no trend
            self.trend_label.setText("")

    def mousePressEvent(self, event):
        """Handle mouse press for drill-down functionality"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.stat_type)
        super().mousePressEvent(event)
        
    def set_sparkline_data(self, data: list):
        """Set historical data for sparkline"""
        self.sparkline.set_data(data)
        self.trend_history = data[-10:] if len(data) > 10 else data[:]
        
    def pulse_highlight(self):
        """Pulse the card to draw attention (for significant changes)"""
        # Create a temporary glow effect
        from ui.animation_system import MicroInteractionAnimator
        micro_animator = MicroInteractionAnimator(self)
        micro_animator.attention_pulse(2)
