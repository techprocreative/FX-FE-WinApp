from typing import Optional, List, Set, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.design_system import DesignTokens as DT, StyleSheets
from ui.components.stat_card import StatCard
from ui.components.model_card import ModelCard
from loguru import logger

class ModelsPage(QWidget):
    """
    Models Page
    Manage ML models: list, load, delete, and train.
    """
    load_model_requested = pyqtSignal(str)  # model_id
    delete_model_requested = pyqtSignal(str) # model_id
    train_model_requested = pyqtSignal()
    
    def __init__(self, model_security: Any, auto_trader: Optional[Any] = None):
        super().__init__()
        self.model_security = model_security
        self.auto_trader = auto_trader
        
        self.loaded_models: Set[str] = set()
        self._refresh_loaded_models()
        self._setup_ui()
        self.refresh()

    def _refresh_loaded_models(self):
        """Update cache of loaded models from auto_trader"""
        self.loaded_models.clear()
        if self.auto_trader and hasattr(self.auto_trader, 'models'):
            for _, model_info in self.auto_trader.models.items():
                if hasattr(model_info, 'model_id'):
                    self.loaded_models.add(model_info.model_id)

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        spacing_mult = DT.get_responsive_spacing()
        margin = int(DT.SPACE_2XL * spacing_mult)
        spacing = int(DT.SPACE_LG * spacing_mult)
        
        self.layout.setContentsMargins(margin, margin, margin, margin)
        self.layout.setSpacing(spacing)

        # --- Header ---
        header_layout = QHBoxLayout()
        header = QLabel("Active Models")
        header.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_3XL, DT.WEIGHT_BOLD))
        header.setStyleSheet(f"color: {DT.TEXT_PRIMARY}; font-family: {DT.FONT_FAMILY};")
        header_layout.addWidget(header)
        header_layout.addStretch()

        # Train Button
        train_btn = QPushButton("➕ Train New Model")
        train_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        train_btn.setFixedHeight(DT.BUTTON_HEIGHT_MD)
        train_btn.setStyleSheet(f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                color: white;
                padding: {DT.SPACE_MD}px {DT.SPACE_LG}px;
                border-radius: {DT.RADIUS_MD}px;
                font-weight: {DT.WEIGHT_BOLD};
                border: none;
                font-family: {DT.FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
        """)
        train_btn.clicked.connect(self.train_model_requested.emit)
        header_layout.addWidget(train_btn)
        self.layout.addLayout(header_layout)

        # Content Area (Stats + Grid)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(spacing)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.content_widget)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.layout.addWidget(scroll)

    def refresh(self):
        """Refresh the models list and stats"""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively delete layout items if needed, but simple separate logic usually enough
                pass

        self._refresh_loaded_models()
        models = self.model_security.list_models_with_metadata()
        
        if not models:
            self._show_empty_state()
            return
            
        spacing = int(DT.SPACE_LG * DT.get_responsive_spacing())
            
        # --- Statistics ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(spacing)
        
        total_card = StatCard("📦", "TOTAL MODELS", str(len(models)))
        stats_layout.addWidget(total_card)

        avg_accuracy = sum(m.get('accuracy', 0) for m in models) / len(models)
        avg_accuracy_pct = avg_accuracy * 100 if avg_accuracy <= 1.0 else avg_accuracy
        accuracy_card = StatCard("🎯", "AVG ACCURACY", f"{avg_accuracy_pct:.1f}%")
        stats_layout.addWidget(accuracy_card)

        active_count = sum(1 for m in models if m.get('model_id') in self.loaded_models)
        active_card = StatCard("🟢", "ACTIVE", str(active_count))
        stats_layout.addWidget(active_card)
        
        stats_layout.addStretch()
        self.content_layout.addLayout(stats_layout)

        # --- Models Grid ---
        models_group = QGroupBox("Your Models")
        models_inner_layout = QVBoxLayout(models_group)
        models_inner_layout.setSpacing(DT.SPACE_BASE)

        for model_info in models:
            is_active = model_info.get('model_id') in self.loaded_models
            model_info['is_active'] = is_active
            
            card = ModelCard(model_info)
            card.load_clicked.connect(lambda mid=model_info['model_id']: self.load_model_requested.emit(mid))
            card.delete_clicked.connect(lambda mid=model_info['model_id']: self.delete_model_requested.emit(mid))
            card.details_clicked.connect(lambda mid=model_info['model_id']: self._show_details(mid))
            
            models_inner_layout.addWidget(card)
            
        models_inner_layout.addStretch()
        self.content_layout.addWidget(models_group)
        self.content_layout.addStretch()

    def _show_empty_state(self):
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(DT.SPACE_LG)

        empty_icon = QLabel("📦")
        empty_icon.setFont(QFont(DT.FONT_FAMILY.strip("'"), 72))
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("No Models Found")
        empty_title.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_2XL, DT.WEIGHT_BOLD))
        empty_title.setStyleSheet(f"color: {DT.TEXT_PRIMARY};")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel("Train your first ML model to start automated trading")
        empty_desc.setFont(QFont(DT.FONT_FAMILY.strip("'"), DT.FONT_BASE))
        empty_desc.setStyleSheet(f"color: {DT.TEXT_SECONDARY};")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)
        
        self.content_layout.addWidget(empty_widget)
        self.content_layout.addStretch()

    def _show_details(self, model_id: str):
        # Find model info
        models = self.model_security.list_models_with_metadata()
        model_info = next((m for m in models if m['model_id'] == model_id), None)
        
        if not model_info:
            return

        details = "\n".join([
            f"ID: {model_info.get('model_id')}",
            f"Name: {model_info.get('name')}",
            f"Symbol: {model_info.get('symbol')}",
            f"Accuracy: {model_info.get('accuracy', 0):.2%}",
            f"Created: {model_info.get('created_at')}",
            f"Version: {model_info.get('version', '1.0.0')}",
        ])
        
        QMessageBox.information(self, "Model Details", details)
