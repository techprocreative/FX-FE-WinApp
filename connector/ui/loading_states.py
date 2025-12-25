"""
Loading States System
Provides various loading indicators and state management for UI components
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout,
    QGraphicsOpacityEffect, QFrame
)
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
from ui.design_system import DesignTokens as DT
from ui.animation_system import AnimationUtils, AnimationConfig, LoadingAnimator
from typing import Optional, Dict, Any, List
import math


class LoadingSpinner(QWidget):
    """
    Animated loading spinner with customizable appearance
    """
    
    def __init__(self, 
                 size: int = 32,
                 color: str = DT.PRIMARY,
                 thickness: int = 3,
                 parent=None):
        super().__init__(parent)
        
        self.size = size
        self.color = color
        self.thickness = thickness
        self.angle = 0
        self.is_spinning = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_angle)
        
        self.setFixedSize(size, size)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup spinner appearance"""
        self.setStyleSheet(f"""
            LoadingSpinner {{
                background: transparent;
            }}
        """)
        
    def start_spinning(self):
        """Start the spinning animation"""
        if not self.is_spinning:
            self.is_spinning = True
            self.timer.start(16)  # ~60 FPS
            
    def stop_spinning(self):
        """Stop the spinning animation"""
        if self.is_spinning:
            self.is_spinning = False
            self.timer.stop()
            self.angle = 0
            self.update()
            
    def _update_angle(self):
        """Update spinner angle"""
        self.angle = (self.angle + 8) % 360
        self.update()
        
    def paintEvent(self, event):
        """Paint the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up pen
        pen = painter.pen()
        pen.setWidth(self.thickness)
        pen.setColor(QColor(self.color))
        pen.setCapStyle(pen.CapStyle.RoundCap)
        painter.setPen(pen)
        
        # Calculate dimensions
        rect_size = self.size - self.thickness
        rect = self.rect().adjusted(
            self.thickness // 2, self.thickness // 2,
            -self.thickness // 2, -self.thickness // 2
        )
        
        # Draw arc
        start_angle = self.angle * 16  # Qt uses 16ths of a degree
        span_angle = 270 * 16  # 3/4 circle
        
        painter.drawArc(rect, start_angle, span_angle)


class LoadingDots(QWidget):
    """
    Animated loading dots indicator
    """
    
    def __init__(self,
                 dot_count: int = 3,
                 dot_size: int = 8,
                 color: str = DT.PRIMARY,
                 spacing: int = 4,
                 parent=None):
        super().__init__(parent)
        
        self.dot_count = dot_count
        self.dot_size = dot_size
        self.color = color
        self.spacing = spacing
        self.current_dot = 0
        self.is_animating = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_dots)
        
        total_width = (dot_count * dot_size) + ((dot_count - 1) * spacing)
        self.setFixedSize(total_width, dot_size)
        
    def start_animation(self):
        """Start the dots animation"""
        if not self.is_animating:
            self.is_animating = True
            self.timer.start(400)  # Change dot every 400ms
            
    def stop_animation(self):
        """Stop the dots animation"""
        if self.is_animating:
            self.is_animating = False
            self.timer.stop()
            self.current_dot = 0
            self.update()
            
    def _update_dots(self):
        """Update active dot"""
        self.current_dot = (self.current_dot + 1) % self.dot_count
        self.update()
        
    def paintEvent(self, event):
        """Paint the dots"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for i in range(self.dot_count):
            x = i * (self.dot_size + self.spacing)
            y = 0
            
            # Set opacity based on current active dot
            if i == self.current_dot:
                opacity = 1.0
            elif i == (self.current_dot - 1) % self.dot_count:
                opacity = 0.6
            else:
                opacity = 0.3
                
            color = QColor(self.color)
            color.setAlphaF(opacity)
            
            painter.setBrush(color)
            painter.setPen(color)
            painter.drawEllipse(x, y, self.dot_size, self.dot_size)


class LoadingProgressBar(QProgressBar):
    """
    Enhanced progress bar with smooth animations and modern styling
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.animation = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup progress bar styling"""
        self.setStyleSheet(f"""
            QProgressBar {{
                background: {DT.GLASS_DARK};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_MD}px;
                text-align: center;
                color: {DT.TEXT_PRIMARY};
                font-family: {DT.FONT_FAMILY};
                font-size: {DT.FONT_SM}px;
                font-weight: {DT.WEIGHT_MEDIUM};
                height: 24px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {DT.PRIMARY},
                    stop:1 {DT.SECONDARY}
                );
                border-radius: {DT.RADIUS_SM}px;
                margin: 2px;
            }}
        """)
        
    def animate_to_value(self, target_value: int, duration: int = DT.DURATION_SLOW):
        """Animate progress bar to target value"""
        if self.animation:
            self.animation.stop()
            
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(target_value)
        self.animation.start()


class LoadingCard(QFrame):
    """
    Loading card with skeleton content and animations
    """
    
    def __init__(self,
                 title: str = "Loading...",
                 subtitle: str = "",
                 show_progress: bool = False,
                 parent=None):
        super().__init__(parent)
        
        self.title = title
        self.subtitle = subtitle
        self.show_progress = show_progress
        
        self.loading_animator = None
        self.spinner = None
        self.progress_bar = None
        
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        """Setup loading card UI"""
        self.setStyleSheet(f"""
            LoadingCard {{
                background: {DT.GLASS_MEDIUM};
                border: 1px solid {DT.BORDER_DEFAULT};
                border-radius: {DT.RADIUS_2XL}px;
                padding: {DT.SPACE_XL}px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(DT.SPACE_LG)
        
        # Header with spinner and title
        header_layout = QHBoxLayout()
        
        # Spinner
        self.spinner = LoadingSpinner(24, DT.PRIMARY, 2)
        header_layout.addWidget(self.spinner)
        
        # Title and subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(DT.SPACE_SM)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            color: {DT.TEXT_PRIMARY};
            font-family: {DT.FONT_FAMILY};
            font-size: {DT.FONT_LG}px;
            font-weight: {DT.WEIGHT_SEMIBOLD};
        """)
        text_layout.addWidget(title_label)
        
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet(f"""
                color: {DT.TEXT_SECONDARY};
                font-family: {DT.FONT_FAMILY};
                font-size: {DT.FONT_SM}px;
                font-weight: {DT.WEIGHT_NORMAL};
            """)
            text_layout.addWidget(subtitle_label)
            
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Progress bar (if enabled)
        if self.show_progress:
            self.progress_bar = LoadingProgressBar()
            layout.addWidget(self.progress_bar)
            
        # Skeleton content
        self._add_skeleton_content(layout)
        
    def _add_skeleton_content(self, layout: QVBoxLayout):
        """Add skeleton loading content"""
        # Skeleton lines
        for i in range(3):
            skeleton_line = QFrame()
            skeleton_line.setFixedHeight(12)
            
            # Vary the width for more realistic skeleton
            if i == 0:
                width_percent = 0.8
            elif i == 1:
                width_percent = 0.6
            else:
                width_percent = 0.4
                
            skeleton_line.setStyleSheet(f"""
                QFrame {{
                    background: {DT.GLASS_LIGHT};
                    border-radius: 6px;
                    max-width: {int(300 * width_percent)}px;
                }}
            """)
            
            layout.addWidget(skeleton_line)
            
    def _setup_animations(self):
        """Setup loading animations"""
        self.loading_animator = LoadingAnimator(self)
        
    def start_loading(self):
        """Start loading animations"""
        if self.spinner:
            self.spinner.start_spinning()
            
        if self.loading_animator:
            self.loading_animator.start_loading("shimmer")
            
    def stop_loading(self):
        """Stop loading animations"""
        if self.spinner:
            self.spinner.stop_spinning()
            
        if self.loading_animator:
            self.loading_animator.stop_loading()
            
    def set_progress(self, value: int):
        """Set progress bar value with animation"""
        if self.progress_bar:
            self.progress_bar.animate_to_value(value)
            
    def update_title(self, title: str):
        """Update loading title"""
        self.title = title
        # Find and update title label
        for child in self.findChildren(QLabel):
            if child.text() == self.title:
                child.setText(title)
                break
                
    def update_subtitle(self, subtitle: str):
        """Update loading subtitle"""
        self.subtitle = subtitle
        # Find and update subtitle label
        labels = self.findChildren(QLabel)
        if len(labels) > 1:
            labels[1].setText(subtitle)


class LoadingStateManager(QObject):
    """
    Centralized loading state management for the entire application
    """
    
    # Signals
    loading_started = pyqtSignal(str)  # component_id
    loading_finished = pyqtSignal(str)  # component_id
    loading_progress = pyqtSignal(str, int)  # component_id, progress
    
    def __init__(self):
        super().__init__()
        
        self.loading_states: Dict[str, bool] = {}
        self.loading_components: Dict[str, QWidget] = {}
        self.loading_messages: Dict[str, str] = {}
        self.loading_progress: Dict[str, int] = {}
        
    def register_component(self, component_id: str, widget: QWidget):
        """Register a component for loading state management"""
        self.loading_components[component_id] = widget
        self.loading_states[component_id] = False
        
    def unregister_component(self, component_id: str):
        """Unregister a component"""
        if component_id in self.loading_components:
            del self.loading_components[component_id]
            del self.loading_states[component_id]
            
        if component_id in self.loading_messages:
            del self.loading_messages[component_id]
            
        if component_id in self.loading_progress:
            del self.loading_progress[component_id]
            
    def start_loading(self, 
                     component_id: str, 
                     message: str = "Loading...",
                     show_progress: bool = False):
        """Start loading state for a component"""
        if component_id not in self.loading_components:
            return
            
        self.loading_states[component_id] = True
        self.loading_messages[component_id] = message
        
        widget = self.loading_components[component_id]
        
        # Apply loading state based on widget type
        if hasattr(widget, 'set_loading'):
            widget.set_loading(True)
        elif hasattr(widget, 'start_loading'):
            widget.start_loading()
        else:
            # Generic loading state - disable widget
            widget.setEnabled(False)
            
        self.loading_started.emit(component_id)
        
    def stop_loading(self, component_id: str):
        """Stop loading state for a component"""
        if component_id not in self.loading_components:
            return
            
        self.loading_states[component_id] = False
        
        widget = self.loading_components[component_id]
        
        # Remove loading state
        if hasattr(widget, 'set_loading'):
            widget.set_loading(False)
        elif hasattr(widget, 'stop_loading'):
            widget.stop_loading()
        else:
            # Generic loading state - re-enable widget
            widget.setEnabled(True)
            
        # Clean up
        if component_id in self.loading_messages:
            del self.loading_messages[component_id]
        if component_id in self.loading_progress:
            del self.loading_progress[component_id]
            
        self.loading_finished.emit(component_id)
        
    def update_progress(self, component_id: str, progress: int):
        """Update loading progress for a component"""
        if component_id not in self.loading_components:
            return
            
        self.loading_progress[component_id] = progress
        
        widget = self.loading_components[component_id]
        
        # Update progress if widget supports it
        if hasattr(widget, 'set_progress'):
            widget.set_progress(progress)
            
        self.loading_progress.emit(component_id, progress)
        
    def update_message(self, component_id: str, message: str):
        """Update loading message for a component"""
        if component_id not in self.loading_components:
            return
            
        self.loading_messages[component_id] = message
        
        widget = self.loading_components[component_id]
        
        # Update message if widget supports it
        if hasattr(widget, 'update_title'):
            widget.update_title(message)
            
    def is_loading(self, component_id: str) -> bool:
        """Check if a component is in loading state"""
        return self.loading_states.get(component_id, False)
        
    def get_loading_components(self) -> List[str]:
        """Get list of components currently in loading state"""
        return [cid for cid, state in self.loading_states.items() if state]
        
    def is_any_loading(self) -> bool:
        """Check if any component is in loading state"""
        return any(self.loading_states.values())
        
    def stop_all_loading(self):
        """Stop loading state for all components"""
        for component_id in list(self.loading_states.keys()):
            if self.loading_states[component_id]:
                self.stop_loading(component_id)


# Global loading state manager instance
loading_manager = LoadingStateManager()


# Convenience functions for easy loading state management
def show_loading_spinner(parent: QWidget, 
                        size: int = 32, 
                        color: str = DT.PRIMARY) -> LoadingSpinner:
    """Create and show a loading spinner"""
    spinner = LoadingSpinner(size, color, parent=parent)
    spinner.start_spinning()
    return spinner


def show_loading_dots(parent: QWidget,
                     dot_count: int = 3,
                     color: str = DT.PRIMARY) -> LoadingDots:
    """Create and show loading dots"""
    dots = LoadingDots(dot_count=dot_count, color=color, parent=parent)
    dots.start_animation()
    return dots


def show_loading_card(parent: QWidget,
                     title: str = "Loading...",
                     subtitle: str = "",
                     show_progress: bool = False) -> LoadingCard:
    """Create and show a loading card"""
    card = LoadingCard(title, subtitle, show_progress, parent)
    card.start_loading()
    return card


def create_loading_overlay(parent: QWidget) -> QWidget:
    """Create a loading overlay for a widget"""
    overlay = QWidget(parent)
    overlay.setStyleSheet(f"""
        QWidget {{
            background: {DT.GLASS_DARKER};
            border-radius: {DT.RADIUS_2XL}px;
        }}
    """)
    
    layout = QVBoxLayout(overlay)
    layout.setAlignment(layout.alignment() | layout.alignment().AlignCenter)
    
    # Add spinner
    spinner = LoadingSpinner(48, DT.PRIMARY)
    spinner.start_spinning()
    layout.addWidget(spinner, alignment=layout.alignment().AlignCenter)
    
    # Add loading text
    label = QLabel("Loading...")
    label.setStyleSheet(f"""
        color: {DT.TEXT_PRIMARY};
        font-family: {DT.FONT_FAMILY};
        font-size: {DT.FONT_LG}px;
        font-weight: {DT.WEIGHT_MEDIUM};
        margin-top: {DT.SPACE_MD}px;
    """)
    layout.addWidget(label, alignment=layout.alignment().AlignCenter)
    
    # Initially hidden
    overlay.hide()
    
    return overlay