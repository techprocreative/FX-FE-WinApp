"""
StatCard - Enhanced Statistics Display Card
Shows key metrics with icon, value, trend indicator, and color coding
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.design_system import DesignTokens as DT


class StatCard(QFrame):
    """Enhanced statistics card with icon, value, and trend"""

    def __init__(self, icon: str, title: str, value: str, trend: str = "",
                 trend_positive: bool = True, parent=None):
        """
        Args:
            icon: Emoji icon for the stat
            title: Stat title (e.g., "TOTAL TRADES")
            value: Main value to display (e.g., "8")
            trend: Trend indicator (e.g., "+3", "-2", "")
            trend_positive: Whether trend is positive (green) or negative (red)
        """
        super().__init__(parent)
        self.title_text = title
        self.icon_text = icon
        self._setup_ui(icon, title, value, trend, trend_positive)

    def _setup_ui(self, icon: str, title: str, value: str, trend: str, trend_positive: bool):
        """Setup the card UI"""
        # Card styling
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {DT.GLASS_DARK}, stop:1 {DT.GLASS_DARKEST}
                );
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
                padding: {DT.SPACE_LG}px;
            }}
        """)
        self.setMinimumWidth(180)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_BASE, DT.SPACE_BASE, DT.SPACE_BASE, DT.SPACE_BASE)
        layout.setSpacing(DT.SPACE_SM)

        # Header: Icon + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(DT.SPACE_SM)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL))
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_SEMIBOLD))
        title_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Value + Trend
        value_layout = QHBoxLayout()

        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_4XL, DT.WEIGHT_BOLD))
        self.value_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY};")
        value_layout.addWidget(self.value_label)

        if trend:
            trend_color = DT.SUCCESS if trend_positive else DT.DANGER
            self.trend_label = QLabel(trend)
            self.trend_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_SEMIBOLD))
            self.trend_label.setStyleSheet(f"color: {trend_color};")
            value_layout.addWidget(self.trend_label)
        else:
            self.trend_label = None

        value_layout.addStretch()
        layout.addLayout(value_layout)

        layout.addStretch()

    def update_value(self, value: str, trend: str = "", trend_positive: bool = True):
        """Update the card value and trend"""
        self.value_label.setText(value)

        if self.trend_label and trend:
            trend_color = DT.SUCCESS if trend_positive else DT.DANGER
            self.trend_label.setText(trend)
            self.trend_label.setStyleSheet(f"color: {trend_color};")
        elif trend and not self.trend_label:
            # Create trend label if it doesn't exist
            trend_color = DT.SUCCESS if trend_positive else DT.DANGER
            self.trend_label = QLabel(trend)
            self.trend_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_LG, DT.WEIGHT_SEMIBOLD))
            self.trend_label.setStyleSheet(f"color: {trend_color};")
            # Add to layout (would need to refactor layout access)
