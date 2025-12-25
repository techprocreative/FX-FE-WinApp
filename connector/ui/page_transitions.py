"""
Page Transition System
Provides smooth transitions between different pages/views in the application
"""

from PyQt6.QtWidgets import QWidget, QStackedWidget, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QObject
from ui.animation_system import (
    AnimationUtils, AnimationConfig, PageTransitionAnimator,
    animation_manager
)
from ui.design_system import DesignTokens as DT
from typing import Optional, Dict, Any, Callable


class ModernStackedWidget(QStackedWidget):
    """
    Enhanced QStackedWidget with smooth page transitions
    Provides various transition effects between pages
    """
    
    # Signals
    transition_started = pyqtSignal(int, int)  # from_index, to_index
    transition_finished = pyqtSignal(int)      # current_index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.transition_animator = PageTransitionAnimator(self)
        self.transition_type = "fade"
        self.transition_duration = DT.DURATION_SLOW
        self.is_transitioning = False
        
        # Connect signals
        self.transition_animator.transition_started.connect(self._on_transition_started)
        self.transition_animator.transition_finished.connect(self._on_transition_finished)
        
    def set_transition_type(self, transition_type: str):
        """
        Set the transition type for page changes
        
        Args:
            transition_type: Type of transition ("fade", "slide_left", "slide_right", 
                           "slide_up", "slide_down", "scale", "none")
        """
        self.transition_type = transition_type
        
    def set_transition_duration(self, duration: int):
        """Set transition duration in milliseconds"""
        self.transition_duration = duration
        
    def setCurrentIndex(self, index: int):
        """Override to add smooth transitions"""
        if self.is_transitioning:
            return  # Ignore if already transitioning
            
        current_index = self.currentIndex()
        
        if index == current_index or self.transition_type == "none":
            # No transition needed or disabled
            super().setCurrentIndex(index)
            return
            
        if index < 0 or index >= self.count():
            return  # Invalid index
            
        # Start transition
        self._transition_to_page(index)
        
    def setCurrentWidget(self, widget: QWidget):
        """Override to add smooth transitions"""
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)
        else:
            super().setCurrentWidget(widget)
            
    def _transition_to_page(self, new_index: int):
        """Perform transition to new page"""
        if self.is_transitioning:
            return
            
        current_index = self.currentIndex()
        current_widget = self.currentWidget()
        new_widget = self.widget(new_index)
        
        if not new_widget:
            return
            
        self.is_transitioning = True
        self.transition_started.emit(current_index, new_index)
        
        # Configure animation
        config = AnimationConfig(duration=self.transition_duration)
        
        # Determine transition direction for slide animations
        if "slide" in self.transition_type:
            if new_index > current_index:
                # Moving forward
                if self.transition_type == "slide_left":
                    direction = "left"
                elif self.transition_type == "slide_right":
                    direction = "right"
                elif self.transition_type == "slide_up":
                    direction = "up"
                else:  # slide_down
                    direction = "down"
            else:
                # Moving backward - reverse direction
                if self.transition_type == "slide_left":
                    direction = "right"
                elif self.transition_type == "slide_right":
                    direction = "left"
                elif self.transition_type == "slide_up":
                    direction = "down"
                else:  # slide_down
                    direction = "up"
        else:
            direction = "left"  # Default
            
        # Perform transition using PageTransitionAnimator
        if self.transition_type.startswith("slide"):
            self.transition_animator.transition_to_page(new_widget, direction, config)
        else:
            self.transition_animator.transition_to_page(new_widget, self.transition_type, config)
            
        # Update current index after transition
        QTimer.singleShot(self.transition_duration + 50, lambda: self._finalize_transition(new_index))
        
    def _finalize_transition(self, new_index: int):
        """Finalize the transition"""
        super().setCurrentIndex(new_index)
        
    def _on_transition_started(self):
        """Handle transition start"""
        pass  # Already handled in _transition_to_page
        
    def _on_transition_finished(self):
        """Handle transition completion"""
        self.is_transitioning = False
        self.transition_finished.emit(self.currentIndex())


class PageManager(QObject):
    """
    High-level page management system
    Handles page registration, navigation, and transition coordination
    """
    
    # Signals
    page_changed = pyqtSignal(str, str)  # from_page, to_page
    navigation_blocked = pyqtSignal(str)  # reason
    
    def __init__(self, stacked_widget: ModernStackedWidget, parent=None):
        super().__init__(parent)
        
        self.stacked_widget = stacked_widget
        self.pages: Dict[str, QWidget] = {}
        self.page_indices: Dict[str, int] = {}
        self.current_page_name = ""
        self.navigation_guards: Dict[str, Callable] = {}
        self.page_history: list = []
        self.max_history = 10
        
        # Connect to stacked widget signals
        self.stacked_widget.transition_finished.connect(self._on_transition_finished)
        
    def register_page(self, name: str, widget: QWidget, index: Optional[int] = None):
        """
        Register a page with the manager
        
        Args:
            name: Unique name for the page
            widget: The widget representing the page
            index: Optional specific index (if None, appends to end)
        """
        if index is not None:
            self.stacked_widget.insertWidget(index, widget)
            # Update indices for existing pages
            for page_name, page_index in self.page_indices.items():
                if page_index >= index:
                    self.page_indices[page_name] = page_index + 1
            self.page_indices[name] = index
        else:
            index = self.stacked_widget.addWidget(widget)
            self.page_indices[name] = index
            
        self.pages[name] = widget
        
        # Set as current page if it's the first one
        if len(self.pages) == 1:
            self.current_page_name = name
            
    def unregister_page(self, name: str):
        """Unregister a page from the manager"""
        if name in self.pages:
            widget = self.pages[name]
            index = self.page_indices[name]
            
            self.stacked_widget.removeWidget(widget)
            
            # Update indices for remaining pages
            for page_name, page_index in self.page_indices.items():
                if page_index > index:
                    self.page_indices[page_name] = page_index - 1
                    
            del self.pages[name]
            del self.page_indices[name]
            
            # Remove from history
            self.page_history = [p for p in self.page_history if p != name]
            
    def navigate_to(self, page_name: str, force: bool = False) -> bool:
        """
        Navigate to a specific page
        
        Args:
            page_name: Name of the page to navigate to
            force: Whether to force navigation (bypass guards)
            
        Returns:
            bool: True if navigation was successful, False if blocked
        """
        if page_name not in self.pages:
            self.navigation_blocked.emit(f"Page '{page_name}' not found")
            return False
            
        if page_name == self.current_page_name:
            return True  # Already on this page
            
        # Check navigation guard
        if not force and self.current_page_name in self.navigation_guards:
            guard = self.navigation_guards[self.current_page_name]
            if not guard(self.current_page_name, page_name):
                self.navigation_blocked.emit(f"Navigation blocked by guard")
                return False
                
        # Add current page to history
        if self.current_page_name and self.current_page_name != page_name:
            self.page_history.append(self.current_page_name)
            
            # Limit history size
            if len(self.page_history) > self.max_history:
                self.page_history.pop(0)
                
        # Perform navigation
        old_page = self.current_page_name
        self.current_page_name = page_name
        
        index = self.page_indices[page_name]
        self.stacked_widget.setCurrentIndex(index)
        
        self.page_changed.emit(old_page, page_name)
        return True
        
    def go_back(self) -> bool:
        """
        Navigate back to the previous page in history
        
        Returns:
            bool: True if navigation was successful, False if no history
        """
        if not self.page_history:
            return False
            
        previous_page = self.page_history.pop()
        return self.navigate_to(previous_page, force=True)
        
    def set_navigation_guard(self, page_name: str, guard_func: Callable[[str, str], bool]):
        """
        Set a navigation guard for a page
        
        Args:
            page_name: Name of the page to guard
            guard_func: Function that takes (from_page, to_page) and returns bool
        """
        self.navigation_guards[page_name] = guard_func
        
    def remove_navigation_guard(self, page_name: str):
        """Remove navigation guard for a page"""
        if page_name in self.navigation_guards:
            del self.navigation_guards[page_name]
            
    def get_current_page(self) -> Optional[QWidget]:
        """Get the current page widget"""
        if self.current_page_name in self.pages:
            return self.pages[self.current_page_name]
        return None
        
    def get_current_page_name(self) -> str:
        """Get the current page name"""
        return self.current_page_name
        
    def get_page_history(self) -> list:
        """Get the page navigation history"""
        return self.page_history.copy()
        
    def clear_history(self):
        """Clear the page navigation history"""
        self.page_history.clear()
        
    def set_transition_type(self, transition_type: str):
        """Set transition type for all page changes"""
        self.stacked_widget.set_transition_type(transition_type)
        
    def set_transition_duration(self, duration: int):
        """Set transition duration for all page changes"""
        self.stacked_widget.set_transition_duration(duration)
        
    def _on_transition_finished(self, index: int):
        """Handle transition completion"""
        # Find page name by index
        for name, page_index in self.page_indices.items():
            if page_index == index:
                self.current_page_name = name
                break


class LoadingOverlay(QWidget):
    """
    Loading overlay with smooth animations
    Can be used during page transitions or data loading
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.loading_animator = None
        self.is_visible = False
        
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        """Setup the loading overlay UI"""
        self.setStyleSheet(f"""
            LoadingOverlay {{
                background: {DT.GLASS_DARKER};
                border-radius: {DT.RADIUS_2XL}px;
            }}
        """)
        
        # Initially hidden
        self.hide()
        
    def _setup_animations(self):
        """Setup loading animations"""
        from ui.animation_system import LoadingAnimator
        self.loading_animator = LoadingAnimator(self)
        
    def show_loading(self, animation_type: str = "fade"):
        """Show loading overlay with animation"""
        if self.is_visible:
            return
            
        self.is_visible = True
        self.show()
        
        # Start loading animation
        if self.loading_animator:
            self.loading_animator.start_loading(animation_type)
            
        # Fade in the overlay
        from ui.animation_system import animate_fade_in
        fade_anim = animate_fade_in(self, DT.DURATION_NORMAL)
        fade_anim.start()
        
    def hide_loading(self):
        """Hide loading overlay with animation"""
        if not self.is_visible:
            return
            
        self.is_visible = False
        
        # Stop loading animation
        if self.loading_animator:
            self.loading_animator.stop_loading()
            
        # Fade out the overlay
        from ui.animation_system import animate_fade_out
        fade_anim = animate_fade_out(self, DT.DURATION_NORMAL)
        fade_anim.finished.connect(self.hide)
        fade_anim.start()
        
    def resizeEvent(self, event):
        """Handle resize to cover parent"""
        super().resizeEvent(event)
        if self.parent():
            self.resize(self.parent().size())


# Convenience functions for easy page management
def create_page_manager(parent_widget: QWidget) -> tuple[ModernStackedWidget, PageManager]:
    """
    Create a page manager with stacked widget
    
    Returns:
        tuple: (ModernStackedWidget, PageManager)
    """
    stacked_widget = ModernStackedWidget(parent_widget)
    page_manager = PageManager(stacked_widget)
    
    return stacked_widget, page_manager


def setup_smooth_transitions(stacked_widget: QStackedWidget, 
                           transition_type: str = "fade",
                           duration: int = DT.DURATION_SLOW) -> ModernStackedWidget:
    """
    Convert a regular QStackedWidget to use smooth transitions
    
    Args:
        stacked_widget: Existing QStackedWidget
        transition_type: Type of transition to use
        duration: Transition duration in milliseconds
        
    Returns:
        ModernStackedWidget: New widget with transitions enabled
    """
    parent = stacked_widget.parent()
    geometry = stacked_widget.geometry()
    
    # Create new modern stacked widget
    modern_widget = ModernStackedWidget(parent)
    modern_widget.setGeometry(geometry)
    modern_widget.set_transition_type(transition_type)
    modern_widget.set_transition_duration(duration)
    
    # Move all widgets from old to new
    while stacked_widget.count() > 0:
        widget = stacked_widget.widget(0)
        stacked_widget.removeWidget(widget)
        modern_widget.addWidget(widget)
        
    # Replace in layout if needed
    if parent and hasattr(parent, 'layout') and parent.layout():
        layout = parent.layout()
        layout.replaceWidget(stacked_widget, modern_widget)
        
    stacked_widget.deleteLater()
    
    return modern_widget