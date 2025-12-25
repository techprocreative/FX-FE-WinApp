"""
NexusTrade Error Dialog Component
Provides styled error dialogs for critical errors with actionable guidance.

Requirements: 8.1, 8.3
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.design_system import DesignTokens as DT, StyleSheets
from core.errors import ErrorInfo, ErrorSeverity, get_error_info


class ErrorDialog(QDialog):
    """
    Styled error dialog for displaying errors with user-friendly messages.
    
    Supports different severity levels with appropriate styling:
    - INFO: Blue accent
    - WARNING: Amber accent  
    - ERROR: Red accent
    - CRITICAL: Red accent with stronger emphasis
    """
    
    def __init__(
        self, 
        error_info: ErrorInfo,
        parent: Optional[QWidget] = None,
        show_details: bool = False,
        details: Optional[str] = None
    ):
        super().__init__(parent)
        self.error_info = error_info
        self.show_details = show_details
        self.details = details
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle(self._get_title())
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setMaximumWidth(600)
        
        # Remove default window frame for custom styling
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main container with styling
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {DT.BG_DARKEST};
                border: 1px solid {self._get_accent_color()};
                border-radius: {DT.RADIUS_XL}px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        # Content layout
        content_layout = QVBoxLayout(container)
        content_layout.setContentsMargins(
            DT.SPACE_2XL, DT.SPACE_2XL, 
            DT.SPACE_2XL, DT.SPACE_2XL
        )
        content_layout.setSpacing(DT.SPACE_LG)
        
        # Header with icon and title
        header = QHBoxLayout()
        header.setSpacing(DT.SPACE_MD)
        
        # Icon
        icon_label = QLabel(self._get_icon())
        icon_label.setStyleSheet(f"""
            font-size: 28px;
            color: {self._get_accent_color()};
        """)
        header.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self._get_title())
        title_font = QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XL, DT.WEIGHT_BOLD)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"""
            color: {self._get_accent_color()};
        """)
        header.addWidget(title_label)
        header.addStretch()
        
        content_layout.addLayout(header)
        
        # User message
        message_label = QLabel(self.error_info.user_message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            color: {DT.TEXT_PRIMARY};
            font-size: {DT.FONT_LG}px;
            font-family: {DT.FONT_FAMILY};
            font-weight: {DT.WEIGHT_MEDIUM};
            padding: {DT.SPACE_SM}px 0;
        """)
        content_layout.addWidget(message_label)
        
        # Guidance box
        guidance_frame = QFrame()
        guidance_frame.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_MD}px;
            }}
        """)
        guidance_layout = QVBoxLayout(guidance_frame)
        guidance_layout.setContentsMargins(
            DT.SPACE_BASE, DT.SPACE_BASE,
            DT.SPACE_BASE, DT.SPACE_BASE
        )
        
        guidance_title = QLabel("💡 What to do:")
        guidance_title.setStyleSheet(f"""
            color: {DT.TEXT_SECONDARY};
            font-size: {DT.FONT_SM}px;
            font-family: {DT.FONT_FAMILY};
            font-weight: {DT.WEIGHT_SEMIBOLD};
        """)
        guidance_layout.addWidget(guidance_title)
        
        guidance_text = QLabel(self.error_info.guidance)
        guidance_text.setWordWrap(True)
        guidance_text.setStyleSheet(f"""
            color: {DT.TEXT_MUTED};
            font-size: {DT.FONT_BASE}px;
            font-family: {DT.FONT_FAMILY};
        """)
        guidance_layout.addWidget(guidance_text)
        
        content_layout.addWidget(guidance_frame)
        
        # Technical details (optional, collapsible)
        if self.show_details and self.details:
            details_frame = QFrame()
            details_frame.setStyleSheet(f"""
                QFrame {{
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid {DT.BORDER_SUBTLE};
                    border-radius: {DT.RADIUS_SM}px;
                }}
            """)
            details_layout = QVBoxLayout(details_frame)
            details_layout.setContentsMargins(
                DT.SPACE_MD, DT.SPACE_MD,
                DT.SPACE_MD, DT.SPACE_MD
            )
            
            details_title = QLabel("Technical Details:")
            details_title.setStyleSheet(f"""
                color: {DT.TEXT_DISABLED};
                font-size: {DT.FONT_XS}px;
                font-family: {DT.FONT_FAMILY};
            """)
            details_layout.addWidget(details_title)
            
            details_text = QLabel(self.details)
            details_text.setWordWrap(True)
            details_text.setStyleSheet(f"""
                color: {DT.TEXT_DISABLED};
                font-size: {DT.FONT_XS}px;
                font-family: monospace;
            """)
            details_layout.addWidget(details_text)
            
            content_layout.addWidget(details_frame)
        
        # Error code (small, bottom)
        code_label = QLabel(f"Error Code: {self.error_info.code}")
        code_label.setStyleSheet(f"""
            color: {DT.TEXT_DISABLED};
            font-size: {DT.FONT_XS}px;
            font-family: {DT.FONT_FAMILY};
        """)
        content_layout.addWidget(code_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(DT.SPACE_MD)
        button_layout.addStretch()
        
        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        ok_btn.setMinimumWidth(100)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        
        if self.error_info.severity == ErrorSeverity.CRITICAL:
            ok_btn.setStyleSheet(StyleSheets.danger_button())
        else:
            ok_btn.setStyleSheet(StyleSheets.primary_button())
        
        button_layout.addWidget(ok_btn)
        content_layout.addLayout(button_layout)
    
    def _get_title(self) -> str:
        """Get dialog title based on severity"""
        severity_titles = {
            ErrorSeverity.INFO: "Information",
            ErrorSeverity.WARNING: "Warning",
            ErrorSeverity.ERROR: "Error",
            ErrorSeverity.CRITICAL: "Critical Error",
        }
        return severity_titles.get(self.error_info.severity, "Error")
    
    def _get_icon(self) -> str:
        """Get icon based on severity"""
        severity_icons = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🚨",
        }
        return severity_icons.get(self.error_info.severity, "❌")
    
    def _get_accent_color(self) -> str:
        """Get accent color based on severity"""
        severity_colors = {
            ErrorSeverity.INFO: DT.INFO,
            ErrorSeverity.WARNING: DT.WARNING,
            ErrorSeverity.ERROR: DT.DANGER,
            ErrorSeverity.CRITICAL: DT.DANGER,
        }
        return severity_colors.get(self.error_info.severity, DT.DANGER)


def show_error_dialog(
    error_code: str,
    parent: Optional[QWidget] = None,
    details: Optional[str] = None,
    show_details: bool = False
) -> None:
    """
    Show an error dialog for the given error code.
    
    Args:
        error_code: The error code to display
        parent: Parent widget for the dialog
        details: Optional technical details to show
        show_details: Whether to show technical details section
    """
    error_info = get_error_info(error_code)
    dialog = ErrorDialog(
        error_info=error_info,
        parent=parent,
        show_details=show_details,
        details=details
    )
    dialog.exec()


def show_critical_error(
    error_code: str,
    parent: Optional[QWidget] = None,
    details: Optional[str] = None
) -> None:
    """
    Show a critical error dialog that requires user acknowledgment.
    Always shows technical details for critical errors.
    
    Args:
        error_code: The error code to display
        parent: Parent widget for the dialog
        details: Optional technical details to show
    """
    error_info = get_error_info(error_code)
    dialog = ErrorDialog(
        error_info=error_info,
        parent=parent,
        show_details=True,
        details=details or error_info.technical_message
    )
    dialog.exec()
