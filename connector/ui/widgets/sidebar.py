from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from ui.design_system import DesignTokens as DT, StyleSheets

class NavSidebar(QWidget):
    """
    Vertical navigation sidebar
    """
    page_changed = pyqtSignal(int)  # index
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(240)
        self.setStyleSheet(f"background: {DT.GLASS_DARK}; border-right: 1px solid {DT.BORDER_DEFAULT};")
        
        self.buttons = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_MD, DT.SPACE_XL, DT.SPACE_MD, DT.SPACE_XL)
        layout.setSpacing(DT.SPACE_SM)
        
        # Logo Area
        logo = QLabel("NEXUS")
        logo.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_2XL, DT.WEIGHT_BOLD))
        logo.setStyleSheet(f"color: {DT.PRIMARY}; padding-left: {DT.SPACE_SM}px; margin-bottom: {DT.SPACE_XL}px;")
        layout.addWidget(logo)
        
        # Navigation Items
        items = [
            ("📊", "Dashboard"),
            ("📦", "Models"),
            ("📈", "Logs"),
            ("⚙️", "Settings")
        ]
        
        for i, (icon, text) in enumerate(items):
            btn = QPushButton(f"{icon}  {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(45)
            # Default style
            btn.setStyleSheet(StyleSheets.sidebar_button(active=(i==0)))
            
            # Connect
            # We need to capture 'i' specifically
            btn.clicked.connect(lambda checked, idx=i: self._on_nav_clicked(idx))
            
            layout.addWidget(btn)
            self.buttons.append(btn)
            
        layout.addStretch()
        
        # Version info
        version = QLabel("v1.0.0")
        version.setStyleSheet(f"color: {DT.TEXT_DISABLED}; font-size: {DT.FONT_XS}px; padding: {DT.SPACE_SM}px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

    def _on_nav_clicked(self, index: int):
        self.set_active_index(index)
        self.page_changed.emit(index)

    def set_active_index(self, index: int):
        for i, btn in enumerate(self.buttons):
            btn.setStyleSheet(StyleSheets.sidebar_button(active=(i == index)))
