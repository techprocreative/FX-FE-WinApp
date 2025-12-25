"""
NexusTrade Logs Page
Displays application logs with filtering and auto-refresh capabilities.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Optional
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QPushButton,
    QCheckBox, QFrame
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer

from ui.design_system import DesignTokens as DT, StyleSheets


class LogEntry:
    """Represents a parsed log entry"""
    
    def __init__(self, timestamp: str, level: str, module: str, message: str):
        self.timestamp = timestamp
        self.level = level.upper().strip()
        self.module = module
        self.message = message
    
    @classmethod
    def parse_line(cls, line: str) -> Optional['LogEntry']:
        """
        Parse a log line in loguru format:
        {time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}
        """
        # Pattern for loguru format
        pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| ([^-]+) - (.*)$'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp, level, module, message = match.groups()
            return cls(timestamp, level.strip(), module.strip(), message.strip())
        
        return None


class LogsPage(QWidget):
    """
    Logs Page
    Detailed trade history and application logs with filtering and auto-refresh.
    """
    
    # Log level colors
    LEVEL_COLORS = {
        'DEBUG': DT.TEXT_MUTED,
        'INFO': DT.PRIMARY,
        'WARNING': DT.WARNING,
        'ERROR': DT.DANGER,
        'CRITICAL': DT.DANGER_DARK,
        'SUCCESS': DT.SUCCESS,
    }
    
    def __init__(self):
        super().__init__()
        self._log_entries: List[LogEntry] = []
        self._current_filter = "ALL"
        self._auto_refresh = True
        self._refresh_timer: Optional[QTimer] = None
        self._log_dir = Path("./logs")
        self._current_log_file: Optional[Path] = None
        self._last_read_position = 0
        
        self._setup_ui()
        self._setup_refresh_timer()
        self._load_logs()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        spacing_mult = DT.get_responsive_spacing()
        margin = int(DT.SPACE_2XL * spacing_mult)
        
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(int(DT.SPACE_LG * spacing_mult))
        
        # Header
        header = QLabel("Application Logs")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        layout.addWidget(header)
        
        # Controls bar
        controls_layout = self._create_controls_bar()
        layout.addLayout(controls_layout)
        
        # Log table
        self._setup_log_table()
        layout.addWidget(self.log_table)
    
    def _create_controls_bar(self) -> QHBoxLayout:
        """Create the controls bar with filter and refresh options"""
        controls = QHBoxLayout()
        controls.setSpacing(DT.SPACE_MD)
        
        # Filter label
        filter_label = QLabel("Filter by Level:")
        filter_label.setStyleSheet(f"""
            color: {DT.TEXT_SECONDARY};
            font-family: {DT.FONT_FAMILY};
            font-size: {DT.FONT_BASE}px;
        """)
        controls.addWidget(filter_label)
        
        # Level filter dropdown
        self.level_filter = QComboBox()
        self.level_filter.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("ALL")
        self.level_filter.currentTextChanged.connect(self._on_filter_changed)
        self.level_filter.setStyleSheet(f"""
            QComboBox {{
                {StyleSheets.input_field()}
                min-width: 120px;
                padding: {DT.SPACE_SM}px {DT.SPACE_MD}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {DT.TEXT_SECONDARY};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {DT.BG_DARK};
                border: 1px solid {DT.BORDER_MEDIUM};
                color: {DT.TEXT_PRIMARY};
                selection-background-color: {DT.PRIMARY};
            }}
        """)
        controls.addWidget(self.level_filter)
        
        # Spacer
        controls.addStretch()
        
        # Auto-refresh checkbox
        self.auto_refresh_check = QCheckBox("Auto-refresh")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(self._on_auto_refresh_changed)
        self.auto_refresh_check.setStyleSheet(f"""
            QCheckBox {{
                color: {DT.TEXT_SECONDARY};
                font-family: {DT.FONT_FAMILY};
                font-size: {DT.FONT_BASE}px;
                spacing: {DT.SPACE_SM}px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {DT.BORDER_MEDIUM};
                background: {DT.GLASS_DARK};
            }}
            QCheckBox::indicator:checked {{
                background: {DT.PRIMARY};
                border-color: {DT.PRIMARY};
            }}
        """)
        controls.addWidget(self.auto_refresh_check)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self._load_logs)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.GLASS_MEDIUM};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                color: {DT.TEXT_PRIMARY};
                font-family: {DT.FONT_FAMILY};
                font-size: {DT.FONT_BASE}px;
            }}
            QPushButton:hover {{
                background: {DT.GLASS_LIGHT};
                border-color: {DT.PRIMARY};
            }}
        """)
        controls.addWidget(self.refresh_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear View")
        self.clear_btn.clicked.connect(self._clear_logs)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.GLASS_MEDIUM};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                color: {DT.TEXT_SECONDARY};
                font-family: {DT.FONT_FAMILY};
                font-size: {DT.FONT_BASE}px;
            }}
            QPushButton:hover {{
                background: {DT.GLASS_LIGHT};
                border-color: {DT.DANGER};
                color: {DT.DANGER};
            }}
        """)
        controls.addWidget(self.clear_btn)
        
        return controls
    
    def _setup_log_table(self):
        """Setup the log table widget"""
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Time", "Level", "Module", "Message"])
        
        # Configure header
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Style the table
        self.log_table.setStyleSheet(f"""
            QTableWidget {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
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
                background: {DT.PRIMARY};
                color: white;
            }}
            QHeaderView::section {{
                background: {DT.BG_DARK};
                color: {DT.TEXT_SECONDARY};
                font-weight: {DT.WEIGHT_SEMIBOLD};
                padding: {DT.SPACE_SM}px;
                border: none;
                border-bottom: 1px solid {DT.BORDER_DEFAULT};
            }}
            QScrollBar:vertical {{
                background: {DT.GLASS_DARK};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {DT.GLASS_LIGHT};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {DT.PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Disable editing
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Enable selection
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Show alternating row colors
        self.log_table.setAlternatingRowColors(True)
    
    def _setup_refresh_timer(self):
        """Setup the auto-refresh timer"""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._check_for_new_logs)
        self._refresh_timer.start(2000)  # Check every 2 seconds
    
    def _find_latest_log_file(self) -> Optional[Path]:
        """Find the most recent log file in the logs directory"""
        if not self._log_dir.exists():
            return None
        
        log_files = list(self._log_dir.glob("nexustrade_*.log"))
        if not log_files:
            return None
        
        # Sort by modification time, newest first
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return log_files[0]
    
    def _load_logs(self):
        """Load logs from the log file"""
        self._current_log_file = self._find_latest_log_file()
        
        if not self._current_log_file or not self._current_log_file.exists():
            self._log_entries = []
            self._update_table()
            return
        
        try:
            with open(self._current_log_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                self._last_read_position = f.tell()
            
            self._log_entries = []
            for line in lines:
                entry = LogEntry.parse_line(line)
                if entry:
                    self._log_entries.append(entry)
            
            self._update_table()
            
        except Exception as e:
            print(f"Error loading logs: {e}")
    
    def _check_for_new_logs(self):
        """Check for new log entries (called by timer)"""
        if not self._auto_refresh:
            return
        
        # Check if there's a newer log file
        latest_file = self._find_latest_log_file()
        if latest_file != self._current_log_file:
            self._load_logs()
            return
        
        if not self._current_log_file or not self._current_log_file.exists():
            return
        
        try:
            # Check if file has grown
            current_size = self._current_log_file.stat().st_size
            if current_size <= self._last_read_position:
                return
            
            # Read new content
            with open(self._current_log_file, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self._last_read_position)
                new_lines = f.readlines()
                self._last_read_position = f.tell()
            
            # Parse new entries
            new_entries = []
            for line in new_lines:
                entry = LogEntry.parse_line(line)
                if entry:
                    new_entries.append(entry)
            
            if new_entries:
                self._log_entries.extend(new_entries)
                self._update_table()
                
                # Scroll to bottom to show new entries
                self.log_table.scrollToBottom()
                
        except Exception as e:
            print(f"Error checking for new logs: {e}")
    
    def _update_table(self):
        """Update the table with filtered log entries"""
        # Filter entries based on current filter
        if self._current_filter == "ALL":
            filtered_entries = self._log_entries
        else:
            filtered_entries = [
                e for e in self._log_entries 
                if e.level == self._current_filter
            ]
        
        # Update table
        self.log_table.setRowCount(len(filtered_entries))
        
        for row, entry in enumerate(filtered_entries):
            # Time column
            time_item = QTableWidgetItem(entry.timestamp)
            time_item.setForeground(QColor(DT.TEXT_MUTED))
            self.log_table.setItem(row, 0, time_item)
            
            # Level column with color
            level_item = QTableWidgetItem(entry.level)
            level_color = self.LEVEL_COLORS.get(entry.level, DT.TEXT_PRIMARY)
            level_item.setForeground(QColor(level_color))
            level_item.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_BOLD))
            self.log_table.setItem(row, 1, level_item)
            
            # Module column
            module_item = QTableWidgetItem(entry.module)
            module_item.setForeground(QColor(DT.TEXT_SECONDARY))
            self.log_table.setItem(row, 2, module_item)
            
            # Message column
            message_item = QTableWidgetItem(entry.message)
            message_item.setForeground(QColor(DT.TEXT_PRIMARY))
            self.log_table.setItem(row, 3, message_item)
    
    def _on_filter_changed(self, level: str):
        """Handle filter dropdown change"""
        self._current_filter = level
        self._update_table()
    
    def _on_auto_refresh_changed(self, state: int):
        """Handle auto-refresh checkbox change"""
        self._auto_refresh = state == Qt.CheckState.Checked.value
    
    def _clear_logs(self):
        """Clear the log view (not the file)"""
        self._log_entries = []
        self._update_table()
    
    def showEvent(self, event):
        """Called when the page is shown"""
        super().showEvent(event)
        # Reload logs when page becomes visible
        self._load_logs()
    
    def hideEvent(self, event):
        """Called when the page is hidden"""
        super().hideEvent(event)
