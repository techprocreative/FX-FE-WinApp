"""
ModelCard - Enhanced Model Display with Progress Bar Accuracy
Shows model info with visual accuracy indicator, status badge, and actions
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ui.design_system import DesignTokens as DT, StyleSheets


class ModelCard(QFrame):
    """Enhanced model card with progress bar accuracy visualization"""

    # Signals
    delete_clicked = pyqtSignal(str)  # model_id
    details_clicked = pyqtSignal(str)  # model_id
    load_clicked = pyqtSignal(str)  # model_id

    def __init__(self, model_info: dict, parent=None):
        """
        Args:
            model_info: Dict with keys: model_id, name, symbol, accuracy,
                       created_at, file_size, is_active (optional)
        """
        super().__init__(parent)
        self.model_info = model_info
        self._setup_ui()

    def _setup_ui(self):
        """Setup the card UI"""
        info = self.model_info

        # Card styling
        self.setStyleSheet(f"""
            QFrame {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_LG}px;
            }}
            QFrame:hover {{
                border: 1px solid {DT.BORDER_MEDIUM};
                background: {DT.GLASS_MEDIUM};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(DT.SPACE_LG, DT.SPACE_LG, DT.SPACE_LG, DT.SPACE_LG)
        layout.setSpacing(DT.SPACE_BASE)

        # Header: Icon + Name + Status
        header_layout = QHBoxLayout()
        header_layout.setSpacing(DT.SPACE_SM)

        # Icon based on symbol
        symbol = info.get('symbol', 'Unknown').upper()
        if 'BTC' in symbol:
            icon = "₿"
        elif 'XAU' in symbol or 'GOLD' in symbol:
            icon = "🥇"
        else:
            icon = "📦"

        # Name with icon
        name_text = f"{icon} {info.get('name', 'Unknown')} ({symbol})"
        name_label = QLabel(name_text)
        name_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE, DT.WEIGHT_BOLD))
        name_label.setStyleSheet(f"color: {DT.TEXT_PRIMARY};")
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        # Status badge
        is_active = info.get('is_active', False)
        status_badge = QLabel("🟢 Active" if is_active else "⚪ Idle")
        status_badge.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS, DT.WEIGHT_SEMIBOLD))
        status_color = DT.SUCCESS if is_active else DT.TEXT_DISABLED
        status_badge.setStyleSheet(f"""
            color: {status_color};
            background: {DT.GLASS_DARKEST};
            padding: {DT.SPACE_XS}px {DT.SPACE_SM}px;
            border-radius: {DT.RADIUS_SM}px;
        """)
        header_layout.addWidget(status_badge)

        layout.addLayout(header_layout)

        # Accuracy Progress Bar
        accuracy = info.get('accuracy', 0.0)
        accuracy_pct = accuracy * 100 if accuracy <= 1.0 else accuracy

        # Progress bar container
        progress_container = QHBoxLayout()
        progress_container.setSpacing(DT.SPACE_SM)

        # Custom styled progress bar
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(int(accuracy_pct))
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(8)

        # Color based on accuracy
        if accuracy_pct >= 85:
            bar_color = DT.SUCCESS
            rating = "Excellent"
        elif accuracy_pct >= 70:
            bar_color = DT.WARNING
            rating = "Very Good"
        elif accuracy_pct >= 60:
            bar_color = DT.INFO
            rating = "Good"
        else:
            bar_color = DT.DANGER
            rating = "Fair"

        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {DT.GLASS_DARKEST};
                border-radius: 4px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bar_color}, stop:1 {DT.PRIMARY}
                );
                border-radius: 4px;
            }}
        """)
        progress_container.addWidget(progress_bar, 1)

        # Accuracy percentage and rating
        accuracy_label = QLabel(f"{accuracy_pct:.1f}%")
        accuracy_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_SM, DT.WEIGHT_BOLD))
        accuracy_label.setStyleSheet(f"color: {bar_color};")
        accuracy_label.setMinimumWidth(50)
        accuracy_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        progress_container.addWidget(accuracy_label)

        layout.addLayout(progress_container)

        # Rating label
        rating_label = QLabel(f"[{rating}]")
        rating_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        rating_label.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")
        layout.addWidget(rating_label)

        # Metadata
        file_size_kb = info.get('file_size', 0) / 1024
        created_at = info.get('created_at', 'Unknown')

        # Format created_at
        if isinstance(created_at, str) and created_at != 'Unknown':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass

        metadata_text = f"Size: {file_size_kb:.1f}KB • Created: {created_at}"
        metadata_label = QLabel(metadata_text)
        metadata_label.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_XS))
        metadata_label.setStyleSheet(f"color: {DT.TEXT_MUTED};")
        layout.addWidget(metadata_label)

        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(DT.SPACE_SM)

        # Details button
        details_btn = QPushButton("📊 Details")
        details_btn.setFixedHeight(DT.BUTTON_HEIGHT_SM)
        details_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DT.GLASS_MEDIUM};
                color: {DT.TEXT_PRIMARY};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_SM}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                font-weight: {DT.WEIGHT_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {DT.GLASS_LIGHT};
                border: 1px solid {DT.BORDER_MEDIUM};
            }}
        """)
        details_btn.clicked.connect(lambda: self.details_clicked.emit(info['model_id']))
        actions_layout.addWidget(details_btn)

        # Load button (if not active)
        if not is_active:
            load_btn = QPushButton("▶ Load")
            load_btn.setFixedHeight(DT.BUTTON_HEIGHT_SM)
            load_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {StyleSheets.gradient_primary()};
                    color: white;
                    border: none;
                    border-radius: {DT.RADIUS_SM}px;
                    padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                    font-weight: {DT.WEIGHT_SEMIBOLD};
                }}
                QPushButton:hover {{
                    background: {StyleSheets.gradient_primary_hover()};
                }}
            """)
            load_btn.clicked.connect(lambda: self.load_clicked.emit(info['model_id']))
            actions_layout.addWidget(load_btn)

        actions_layout.addStretch()

        # Delete button
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setFixedHeight(DT.BUTTON_HEIGHT_SM)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                color: white;
                border: none;
                border-radius: {DT.RADIUS_SM}px;
                padding: {DT.SPACE_SM}px {DT.SPACE_BASE}px;
                font-weight: {DT.WEIGHT_SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_danger_hover()};
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(info['model_id']))
        actions_layout.addWidget(delete_btn)

        layout.addLayout(actions_layout)

    def set_active_status(self, is_active: bool):
        """Update the active status of the model"""
        self.model_info['is_active'] = is_active
        # Would need to refresh UI - for now just update model_info
