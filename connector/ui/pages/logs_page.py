from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QHeaderView
)
from PyQt6.QtGui import QFont

from ui.design_system import DesignTokens as DT

class LogsPage(QWidget):
    """
    Logs Page
    Detailed trade history and application logs.
    """
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        spacing_mult = DT.get_responsive_spacing()
        margin = int(DT.SPACE_2XL * spacing_mult)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        
        header = QLabel("Trade Logs")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)
        
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Module", "Message", "Details"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.log_table)
