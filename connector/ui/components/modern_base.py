"""
Modern Component Base Classes
Enhanced base classes with glass morphism effects, hover animations, and modern styling
"""

from PyQt6.QtWidgets import (
    QFrame, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPaintEvent, QEnterEvent
from ui.design_system import DesignTokens as DT, StyleSheets
from ui.animation_system import (
    HoverAnimator, LoadingAnimator, MicroInteractionAnimator,
    animate_hover_effect, animate_button_press, animate_loading_state
)
from typing import Optional, Dict, Any
import math


class ModernCard(QFrame):
    """
    Modern card base class with glass morphism effects and hover animations
    
    Features:
    - Glass morphism background with blur effects
    - Hover animations with scale and glow effects
    - Configurable padding and corner radius
    - Built-in loading and error states
    - Responsive sizing based on screen tier
    """
    
    # Signals
    clicked = pyqtSignal()
    
    def __init__(self, 
                 preset: str = "default",
                 clickable: bool = False,
                 padding: Optional[int] = None,
                 parent=None):
        """
        Initialize modern card
        
        Args:
            preset: Glass morphism preset ("subtle", "default", "strong", "sidebar", "modal")
            clickable: Whether card should be clickable with hover effects
            padding: Custom padding (uses design system default if None)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.preset = preset
        self.clickable = clickable
        self.padding = padding or DT.SPACE_XL
        self.is_loading = False
        self.is_error = False
        self.error_message = ""
        
        # Animation components
        self.hover_animator = None
        self.loading_animator = None
        self.micro_animator = None
        
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        """Setup the card UI with glass morphism styling"""
        # Get glass morphism preset
        presets = {
            "subtle": DT.GLASS_PRESET_SUBTLE,
            "default": DT.GLASS_PRESET_DEFAULT,
            "strong": DT.GLASS_PRESET_STRONG,
            "sidebar": DT.GLASS_PRESET_SIDEBAR,
            "modal": DT.GLASS_PRESET_MODAL
        }
        
        config = presets.get(self.preset, DT.GLASS_PRESET_DEFAULT)
        
        # Apply glass morphism styling
        self.setStyleSheet(f"""
            ModernCard {{
                background: {config['background']};
                border: 1px solid {config['border']};
                border-radius: {DT.RADIUS_2XL}px;
                padding: {self.padding}px;
            }}
            ModernCard:hover {{
                border-color: {DT.BORDER_FOCUS};
            }}
        """)
        
        # Set minimum size based on screen tier
        screen_tier = DT.get_screen_tier()
        if screen_tier == 'small':
            self.setMinimumSize(200, 120)
        elif screen_tier == 'medium':
            self.setMinimumSize(240, 140)
        else:
            self.setMinimumSize(280, 160)
            
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
        # Make clickable if specified
        if self.clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            
    def _setup_animations(self):
        """Setup hover animations and effects using the new animation system"""
        if self.clickable:
            # Setup hover animator with modern effects
            self.hover_animator = HoverAnimator(self)
            self.hover_animator.set_hover_effects(
                scale_factor=1.02,
                glow_enabled=True,
                glow_color=DT.PRIMARY,
                shadow_enabled=True
            )
            
            # Setup micro-interaction animator for click feedback
            self.micro_animator = MicroInteractionAnimator(self)
            
        # Setup loading animator
        self.loading_animator = LoadingAnimator(self)
        
    def enterEvent(self, event: QEnterEvent):
        """Handle mouse enter for hover effects"""
        super().enterEvent(event)
        # Hover effects are now handled by HoverAnimator
        
    def leaveEvent(self, event):
        """Handle mouse leave for hover effects"""
        super().leaveEvent(event)
        # Hover effects are now handled by HoverAnimator
        
    def mousePressEvent(self, event):
        """Handle mouse press for click effects"""
        super().mousePressEvent(event)
        
        if self.clickable and event.button() == Qt.MouseButton.LeftButton:
            # Use micro-interaction animator for press feedback
            if self.micro_animator:
                self.micro_animator.button_press_feedback()
            self.clicked.emit()
            
    def set_loading(self, loading: bool):
        """Set loading state with smooth animations"""
        self.is_loading = loading
        
        if loading:
            # Start loading animation
            if self.loading_animator:
                self.loading_animator.start_loading("pulse")
                
            # Update styling for loading state
            self.setStyleSheet(self.styleSheet() + f"""
                ModernCard {{
                    border-color: {DT.PRIMARY_400};
                }}
            """)
            self.setCursor(Qt.CursorShape.WaitCursor)
        else:
            # Stop loading animation
            if self.loading_animator:
                self.loading_animator.stop_loading()
                
            # Reset styling
            self._setup_ui()
            if self.clickable:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
                
    def set_error(self, error: bool, message: str = ""):
        """Set error state with feedback animation"""
        self.is_error = error
        self.error_message = message
        
        if error:
            # Trigger error feedback animation
            if self.micro_animator:
                self.micro_animator.error_feedback()
                
            # Update styling for error state
            self.setStyleSheet(self.styleSheet() + f"""
                ModernCard {{
                    border-color: {DT.DANGER_400};
                    background: {DT.GLASS_DARK};
                }}
            """)
        else:
            self._setup_ui()  # Reset styling
            
    def set_success(self, success: bool = True):
        """Set success state with feedback animation"""
        if success and self.micro_animator:
            self.micro_animator.success_feedback()


class ModernButton(QPushButton):
    """
    Modern button class with multiple variants and loading states
    
    Features:
    - Multiple variants (primary, secondary, danger, ghost)
    - Loading states with spinner animations
    - Icon support with proper spacing
    - Hover and press animations
    - Accessibility features (focus indicators)
    """
    
    def __init__(self, 
                 text: str = "",
                 variant: str = "primary",
                 size: str = "md",
                 icon: str = "",
                 parent=None):
        """
        Initialize modern button
        
        Args:
            text: Button text
            variant: Button variant ("primary", "secondary", "danger", "ghost")
            size: Button size ("sm", "md", "lg")
            icon: Optional icon (emoji or text)
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        self.variant = variant
        self.size = size
        self.icon = icon
        self.is_loading = False
        self.original_text = text
        
        # Animation components
        self.hover_animator = None
        self.loading_animator = None
        self.micro_animator = None
        
        self._setup_ui()
        self._setup_animations()
        
    def _setup_ui(self):
        """Setup button UI with variant styling"""
        # Size configurations
        size_configs = {
            "sm": {
                "height": DT.BUTTON_HEIGHT_SM,
                "font_size": DT.FONT_SM,
                "padding_h": DT.SPACE_MD,
                "padding_v": DT.SPACE_SM
            },
            "md": {
                "height": DT.BUTTON_HEIGHT_MD,
                "font_size": DT.FONT_BASE,
                "padding_h": DT.SPACE_XL,
                "padding_v": DT.SPACE_MD
            },
            "lg": {
                "height": DT.BUTTON_HEIGHT_LG,
                "font_size": DT.FONT_LG,
                "padding_h": DT.SPACE_2XL,
                "padding_v": DT.SPACE_LG
            }
        }
        
        config = size_configs.get(self.size, size_configs["md"])
        
        # Apply variant styling
        if self.variant == "primary":
            self.setStyleSheet(f"""
                ModernButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DT.PRIMARY},
                        stop:1 {DT.SECONDARY}
                    );
                    border: none;
                    border-radius: {DT.RADIUS_LG}px;
                    padding: {config['padding_v']}px {config['padding_h']}px;
                    color: white;
                    font-weight: {DT.WEIGHT_SEMIBOLD};
                    font-size: {config['font_size']}px;
                    font-family: {DT.FONT_FAMILY};
                    min-height: {config['height']}px;
                }}
                ModernButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DT.PRIMARY_DARK},
                        stop:1 {DT.SECONDARY_DARK}
                    );
                }}
                ModernButton:pressed {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DT.PRIMARY_DARKER},
                        stop:1 {DT.SECONDARY_DARKER}
                    );
                }}
                ModernButton:disabled {{
                    background: {DT.GLASS_MEDIUM};
                    color: {DT.TEXT_DISABLED};
                }}
                ModernButton:focus {{
                    outline: 2px solid {DT.PRIMARY_400};
                    outline-offset: 2px;
                }}
            """)
            
        elif self.variant == "secondary":
            self.setStyleSheet(f"""
                ModernButton {{
                    background: transparent;
                    border: 2px solid {DT.PRIMARY};
                    border-radius: {DT.RADIUS_LG}px;
                    padding: {config['padding_v']}px {config['padding_h']}px;
                    color: {DT.PRIMARY};
                    font-weight: {DT.WEIGHT_SEMIBOLD};
                    font-size: {config['font_size']}px;
                    font-family: {DT.FONT_FAMILY};
                    min-height: {config['height']}px;
                }}
                ModernButton:hover {{
                    background: {DT.PRIMARY};
                    color: white;
                }}
                ModernButton:pressed {{
                    background: {DT.PRIMARY_DARK};
                    border-color: {DT.PRIMARY_DARK};
                }}
                ModernButton:disabled {{
                    background: transparent;
                    border-color: {DT.TEXT_DISABLED};
                    color: {DT.TEXT_DISABLED};
                }}
                ModernButton:focus {{
                    outline: 2px solid {DT.PRIMARY_400};
                    outline-offset: 2px;
                }}
            """)
            
        elif self.variant == "danger":
            self.setStyleSheet(f"""
                ModernButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DT.DANGER},
                        stop:1 {DT.DANGER_DARK}
                    );
                    border: none;
                    border-radius: {DT.RADIUS_LG}px;
                    padding: {config['padding_v']}px {config['padding_h']}px;
                    color: white;
                    font-weight: {DT.WEIGHT_SEMIBOLD};
                    font-size: {config['font_size']}px;
                    font-family: {DT.FONT_FAMILY};
                    min-height: {config['height']}px;
                }}
                ModernButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {DT.DANGER_DARK},
                        stop:1 {DT.DANGER_DARKER}
                    );
                }}
                ModernButton:disabled {{
                    background: {DT.GLASS_MEDIUM};
                    color: {DT.TEXT_DISABLED};
                }}
                ModernButton:focus {{
                    outline: 2px solid {DT.DANGER_400};
                    outline-offset: 2px;
                }}
            """)
            
        elif self.variant == "ghost":
            self.setStyleSheet(f"""
                ModernButton {{
                    background: transparent;
                    border: none;
                    border-radius: {DT.RADIUS_LG}px;
                    padding: {config['padding_v']}px {config['padding_h']}px;
                    color: {DT.TEXT_SECONDARY};
                    font-weight: {DT.WEIGHT_MEDIUM};
                    font-size: {config['font_size']}px;
                    font-family: {DT.FONT_FAMILY};
                    min-height: {config['height']}px;
                }}
                ModernButton:hover {{
                    background: {DT.GLASS_LOW};
                    color: {DT.TEXT_PRIMARY};
                }}
                ModernButton:pressed {{
                    background: {DT.GLASS_MEDIUM};
                }}
                ModernButton:disabled {{
                    color: {DT.TEXT_DISABLED};
                }}
                ModernButton:focus {{
                    outline: 2px solid {DT.PRIMARY_400};
                    outline-offset: 2px;
                }}
            """)
            
        # Set button text with icon if provided
        if self.icon:
            self.setText(f"{self.icon} {self.original_text}")
        else:
            self.setText(self.original_text)
            
    def _setup_animations(self):
        """Setup button animations using the new animation system"""
        # Setup hover animator with variant-specific effects
        self.hover_animator = HoverAnimator(self)
        
        # Configure hover effects based on variant
        if self.variant == "primary":
            glow_color = DT.PRIMARY
        elif self.variant == "danger":
            glow_color = DT.DANGER
        elif self.variant == "secondary":
            glow_color = DT.PRIMARY
        else:  # ghost
            glow_color = DT.TEXT_SECONDARY
            
        self.hover_animator.set_hover_effects(
            scale_factor=1.02,
            glow_enabled=True,
            glow_color=glow_color,
            shadow_enabled=True
        )
        
        # Setup micro-interaction animator for press feedback
        self.micro_animator = MicroInteractionAnimator(self)
        
        # Setup loading animator
        self.loading_animator = LoadingAnimator(self)
        
        # Connect click signal to press animation
        self.clicked.connect(self._on_button_clicked)
        
    def _on_button_clicked(self):
        """Handle button click with animation feedback"""
        if not self.is_loading and self.micro_animator:
            self.micro_animator.button_press_feedback()
    
    def set_loading(self, loading: bool):
        """Set loading state with spinner animation"""
        self.is_loading = loading
        
        if loading:
            # Start loading animation
            if self.loading_animator:
                self.loading_animator.start_loading("pulse")
                
            self.setText("⏳ Loading...")
            self.setEnabled(False)
        else:
            # Stop loading animation
            if self.loading_animator:
                self.loading_animator.stop_loading()
                
            if self.icon:
                self.setText(f"{self.icon} {self.original_text}")
            else:
                self.setText(self.original_text)
            self.setEnabled(True)
            
    def set_success_feedback(self):
        """Trigger success feedback animation"""
        if self.micro_animator:
            self.micro_animator.success_feedback()
            
    def set_error_feedback(self):
        """Trigger error feedback animation"""
        if self.micro_animator:
            self.micro_animator.error_feedback()
            
    def set_icon(self, icon: str):
        """Update button icon"""
        self.icon = icon
        if icon:
            self.setText(f"{icon} {self.original_text}")
        else:
            self.setText(self.original_text)


class ModernInput(QLineEdit):
    """
    Modern input field class with floating labels and validation states
    
    Features:
    - Floating label animations
    - Built-in validation states (error, success, warning)
    - Icon support (prefix/suffix)
    - Character count and helper text
    - Smooth focus transitions
    """
    
    # Signals
    validation_changed = pyqtSignal(str, bool)  # state, is_valid
    
    def __init__(self, 
                 placeholder: str = "",
                 label: str = "",
                 helper_text: str = "",
                 validation_state: str = "default",
                 show_character_count: bool = False,
                 max_length: int = 0,
                 prefix_icon: str = "",
                 suffix_icon: str = "",
                 parent=None):
        """
        Initialize modern input
        
        Args:
            placeholder: Placeholder text
            label: Floating label text
            helper_text: Helper text below input
            validation_state: Validation state ("default", "success", "warning", "error")
            show_character_count: Whether to show character count
            max_length: Maximum character length (0 for no limit)
            prefix_icon: Icon to show at start of input
            suffix_icon: Icon to show at end of input
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.label_text = label
        self.helper_text = helper_text
        self.validation_state = validation_state
        self.show_character_count = show_character_count
        self.prefix_icon = prefix_icon
        self.suffix_icon = suffix_icon
        
        # Floating label
        self.floating_label = None
        self.helper_label = None
        self.char_count_label = None
        
        # Animation components
        self.focus_animator = None
        self.validation_animator = None
        
        self._setup_ui()
        self._setup_animations()
        
        # Set placeholder and max length
        if placeholder:
            self.setPlaceholderText(placeholder)
        if max_length > 0:
            self.setMaxLength(max_length)
            
    def _setup_ui(self):
        """Setup input UI with modern styling"""
        # Base input styling
        self.setStyleSheet(f"""
            ModernInput {{
                background: {DT.GLASS_DARK};
                border: 2px solid {self._get_border_color()};
                border-radius: {DT.RADIUS_MD}px;
                padding: {DT.SPACE_MD}px {DT.SPACE_BASE}px;
                color: {DT.TEXT_PRIMARY};
                font-size: {DT.FONT_BASE}px;
                font-family: {DT.FONT_FAMILY};
                min-height: {DT.INPUT_HEIGHT}px;
            }}
            ModernInput:focus {{
                border-color: {self._get_focus_border_color()};
                background: {DT.GLASS_MEDIUM};
                outline: none;
            }}
            ModernInput:disabled {{
                background: {DT.GLASS_SUBTLE};
                color: {DT.TEXT_DISABLED};
                border-color: {DT.BORDER_NEUTRAL_SUBTLE};
            }}
        """)
        
        # Adjust padding for icons
        if self.prefix_icon or self.suffix_icon:
            left_padding = DT.SPACE_3XL if self.prefix_icon else DT.SPACE_BASE
            right_padding = DT.SPACE_3XL if self.suffix_icon else DT.SPACE_BASE
            
            self.setStyleSheet(self.styleSheet().replace(
                f"padding: {DT.SPACE_MD}px {DT.SPACE_BASE}px;",
                f"padding: {DT.SPACE_MD}px {right_padding}px {DT.SPACE_MD}px {left_padding}px;"
            ))
            
    def _setup_animations(self):
        """Setup input animations using the new animation system"""
        # Setup micro-interaction animator for validation feedback
        self.validation_animator = MicroInteractionAnimator(self)
        
        # Connect signals for floating label animation
        self.textChanged.connect(self._on_text_changed)
        self.focusInEvent = self._focus_in_event
        self.focusOutEvent = self._focus_out_event
        
    def _get_border_color(self) -> str:
        """Get border color based on validation state"""
        colors = {
            "default": DT.BORDER_DEFAULT,
            "success": DT.SUCCESS_400,
            "warning": DT.WARNING_400,
            "error": DT.DANGER_400
        }
        return colors.get(self.validation_state, DT.BORDER_DEFAULT)
        
    def _get_focus_border_color(self) -> str:
        """Get focus border color based on validation state"""
        colors = {
            "default": DT.BORDER_FOCUS,
            "success": DT.SUCCESS_500,
            "warning": DT.WARNING_500,
            "error": DT.DANGER_500
        }
        return colors.get(self.validation_state, DT.BORDER_FOCUS)
        
    def _focus_in_event(self, event):
        """Handle focus in event with smooth animation"""
        super().focusInEvent(event)
        self._animate_focus_in()
        
    def _focus_out_event(self, event):
        """Handle focus out event with smooth animation"""
        super().focusOutEvent(event)
        self._animate_focus_out()
        
    def _animate_focus_in(self):
        """Animate focus in effect with glow"""
        if self.validation_animator:
            # Create subtle glow effect on focus
            from ui.animation_system import AnimationUtils, AnimationConfig
            config = AnimationConfig(duration=DT.DURATION_FAST)
            glow_anim = AnimationUtils.create_glow_animation(
                self, self._get_focus_border_color(), 10, config
            )
            glow_anim.start()
        
    def _animate_focus_out(self):
        """Animate focus out effect"""
        if self.validation_animator:
            # Fade out glow effect
            from ui.animation_system import AnimationUtils, AnimationConfig
            config = AnimationConfig(duration=DT.DURATION_FAST)
            fade_glow_anim = AnimationUtils.create_glow_animation(
                self, self._get_focus_border_color(), 0, config
            )
            fade_glow_anim.start()
        
    def _on_text_changed(self, text: str):
        """Handle text change for character count and validation"""
        # Update character count if enabled
        if self.show_character_count and hasattr(self, 'char_count_label'):
            max_len = self.maxLength() if self.maxLength() > 0 else "∞"
            self.char_count_label.setText(f"{len(text)}/{max_len}")
            
        # Emit validation signal
        is_valid = self._validate_input(text)
        self.validation_changed.emit(self.validation_state, is_valid)
        
    def _validate_input(self, text: str) -> bool:
        """Validate input text (override in subclasses)"""
        # Basic validation - not empty for required fields
        return len(text.strip()) > 0 if self.validation_state != "default" else True
        
    def set_validation_state(self, state: str, message: str = ""):
        """Set validation state and update styling with animation feedback"""
        old_state = self.validation_state
        self.validation_state = state
        self.helper_text = message
        
        # Update styling
        self._setup_ui()
        
        # Trigger appropriate animation feedback
        if self.validation_animator:
            if state == "error" and old_state != "error":
                self.validation_animator.error_feedback()
            elif state == "success" and old_state != "success":
                self.validation_animator.success_feedback()
        
        # Update helper text if label exists
        if hasattr(self, 'helper_label') and self.helper_label:
            self.helper_label.setText(message)
            
            # Color code helper text
            colors = {
                "default": DT.TEXT_MUTED,
                "success": DT.SUCCESS_400,
                "warning": DT.WARNING_400,
                "error": DT.DANGER_400
            }
            color = colors.get(state, DT.TEXT_MUTED)
            self.helper_label.setStyleSheet(f"color: {color};")
            
    def set_prefix_icon(self, icon: str):
        """Set prefix icon"""
        self.prefix_icon = icon
        self._setup_ui()
        
    def set_suffix_icon(self, icon: str):
        """Set suffix icon"""
        self.suffix_icon = icon
        self._setup_ui()