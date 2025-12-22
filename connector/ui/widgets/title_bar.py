from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QIcon

from ui.design_system import DesignTokens as DT, StyleSheets

class ModernTitleBar(QWidget):
    """
    Custom frameless title bar with drag support and window controls
    """
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    
    def __init__(self, title: str = "NexusTrade"):
        super().__init__()
        self.setFixedHeight(40)
        self.setStyleSheet(f"background: {DT.GLASS_DARK}; border-bottom: 1px solid {DT.BORDER_default};")
        self._setup_ui(title)
        
        # Dragging state
        self._is_dragging = False
        self._drag_pos = QPoint()

    def _setup_ui(self, title: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_BOLD))
        self.title_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY}; border: none; background: transparent;")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Window Controls
        # Minimize
        btn_min = QPushButton("—")
        btn_min.setFixedSize(40, 40)
        btn_min.setStyleSheet(StyleSheets.title_bar_button())
        btn_min.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(btn_min)
        
        # Maximize/Restore
        btn_max = QPushButton("▢")
        btn_max.setFixedSize(40, 40)
        btn_max.setStyleSheet(StyleSheets.title_bar_button())
        btn_max.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(btn_max)
        
        # Close
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(40, 40)
        btn_close.setStyleSheet(StyleSheets.title_bar_button(is_close=True))
        btn_close.clicked.connect(self.close_clicked.emit)
        layout.addWidget(btn_close)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
