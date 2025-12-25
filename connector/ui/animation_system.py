"""
Enhanced Animation System for Modern UI
Provides smooth transitions, micro-interactions, hover effects, and loading animations
"""

from PyQt6.QtWidgets import (
    QWidget, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, 
    QGraphicsBlurEffect, QGraphicsColorizeEffect, QApplication
)
from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QTimer, QParallelAnimationGroup,
    QSequentialAnimationGroup, QAbstractAnimation, QRect, QPoint, QSize,
    pyqtSignal, QObject, QVariantAnimation
)
from PyQt6.QtGui import QColor, QPalette
from ui.design_system import DesignTokens as DT
from typing import Optional, Dict, Any, Callable, List, Union
import math


class AnimationConfig:
    """Configuration class for animation parameters"""
    
    def __init__(self,
                 duration: int = DT.DURATION_NORMAL,
                 easing: str = DT.EASE_OUT_CUBIC,
                 delay: int = DT.DELAY_NONE):
        self.duration = duration
        self.easing = easing
        self.delay = delay


class AnimationManager(QObject):
    """
    Central animation manager for coordinating UI animations
    Handles animation queuing, performance optimization, and cleanup
    """
    
    # Signals
    animation_started = pyqtSignal(str)  # animation_id
    animation_finished = pyqtSignal(str)  # animation_id
    
    def __init__(self):
        super().__init__()
        self.active_animations: Dict[str, QAbstractAnimation] = {}
        self.animation_groups: Dict[str, Union[QParallelAnimationGroup, QSequentialAnimationGroup]] = {}
        self.performance_mode = False
        
    def register_animation(self, animation_id: str, animation: QAbstractAnimation):
        """Register an animation with the manager"""
        self.active_animations[animation_id] = animation
        animation.finished.connect(lambda: self._on_animation_finished(animation_id))
        
    def start_animation(self, animation_id: str):
        """Start a registered animation"""
        if animation_id in self.active_animations:
            animation = self.active_animations[animation_id]
            if animation.state() != QAbstractAnimation.State.Running:
                animation.start()
                self.animation_started.emit(animation_id)
                
    def stop_animation(self, animation_id: str):
        """Stop a running animation"""
        if animation_id in self.active_animations:
            animation = self.active_animations[animation_id]
            if animation.state() == QAbstractAnimation.State.Running:
                animation.stop()
                
    def pause_animation(self, animation_id: str):
        """Pause a running animation"""
        if animation_id in self.active_animations:
            animation = self.active_animations[animation_id]
            if animation.state() == QAbstractAnimation.State.Running:
                animation.pause()
                
    def resume_animation(self, animation_id: str):
        """Resume a paused animation"""
        if animation_id in self.active_animations:
            animation = self.active_animations[animation_id]
            if animation.state() == QAbstractAnimation.State.Paused:
                animation.resume()
                
    def set_performance_mode(self, enabled: bool):
        """Enable/disable performance mode (reduces animation quality)"""
        self.performance_mode = enabled
        
    def cleanup_finished_animations(self):
        """Clean up finished animations to free memory"""
        finished_animations = []
        for animation_id, animation in self.active_animations.items():
            if animation.state() == QAbstractAnimation.State.Stopped:
                finished_animations.append(animation_id)
                
        for animation_id in finished_animations:
            del self.active_animations[animation_id]
            
    def _on_animation_finished(self, animation_id: str):
        """Handle animation completion"""
        self.animation_finished.emit(animation_id)
        # Clean up after a short delay to allow for any final processing
        QTimer.singleShot(100, self.cleanup_finished_animations)


# Global animation manager instance
animation_manager = AnimationManager()


class AnimationUtils:
    """Enhanced animation utilities for smooth UI transitions and micro-interactions"""
    
    @staticmethod
    def get_easing_curve(curve_type: str) -> QEasingCurve:
        """Get QEasingCurve from string identifier"""
        curve_map = {
            "linear": QEasingCurve.Type.Linear,
            "ease": QEasingCurve.Type.OutCubic,
            "ease-in": QEasingCurve.Type.InCubic,
            "ease-out": QEasingCurve.Type.OutCubic,
            "ease-in-out": QEasingCurve.Type.InOutCubic,
            "ease-in-sine": QEasingCurve.Type.InSine,
            "ease-out-sine": QEasingCurve.Type.OutSine,
            "ease-in-out-sine": QEasingCurve.Type.InOutSine,
            "ease-in-quad": QEasingCurve.Type.InQuad,
            "ease-out-quad": QEasingCurve.Type.OutQuad,
            "ease-in-out-quad": QEasingCurve.Type.InOutQuad,
            "ease-in-quart": QEasingCurve.Type.InQuart,
            "ease-out-quart": QEasingCurve.Type.OutQuart,
            "ease-in-out-quart": QEasingCurve.Type.InOutQuart,
            "ease-in-back": QEasingCurve.Type.InBack,
            "ease-out-back": QEasingCurve.Type.OutBack,
            "ease-in-out-back": QEasingCurve.Type.InOutBack,
            "ease-in-bounce": QEasingCurve.Type.InBounce,
            "ease-out-bounce": QEasingCurve.Type.OutBounce,
            "ease-in-out-bounce": QEasingCurve.Type.InOutBounce,
        }
        return QEasingCurve(curve_map.get(curve_type, QEasingCurve.Type.OutCubic))
    
    @staticmethod
    def create_fade_animation(widget: QWidget, 
                            fade_in: bool = True,
                            config: Optional[AnimationConfig] = None) -> QPropertyAnimation:
        """Create smooth fade in/out animation"""
        if config is None:
            config = AnimationConfig()
            
        # Create or get opacity effect
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(config.duration)
        animation.setEasingCurve(AnimationUtils.get_easing_curve(config.easing))
        
        if fade_in:
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
        else:
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
            
        # Add delay if specified
        if config.delay > 0:
            QTimer.singleShot(config.delay, animation.start)
        
        return animation
    
    @staticmethod
    def create_slide_animation(widget: QWidget,
                             direction: str = "up",
                             distance: int = 50,
                             config: Optional[AnimationConfig] = None) -> QPropertyAnimation:
        """Create smooth slide animation"""
        if config is None:
            config = AnimationConfig(duration=DT.DURATION_SLOW)
            
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(config.duration)
        animation.setEasingCurve(AnimationUtils.get_easing_curve(config.easing))
        
        current_geometry = widget.geometry()
        
        # Calculate start and end positions based on direction
        if direction == "up":
            start_geometry = QRect(current_geometry.x(), current_geometry.y() + distance,
                                 current_geometry.width(), current_geometry.height())
            end_geometry = current_geometry
        elif direction == "down":
            start_geometry = current_geometry
            end_geometry = QRect(current_geometry.x(), current_geometry.y() + distance,
                               current_geometry.width(), current_geometry.height())
        elif direction == "left":
            start_geometry = QRect(current_geometry.x() + distance, current_geometry.y(),
                                 current_geometry.width(), current_geometry.height())
            end_geometry = current_geometry
        elif direction == "right":
            start_geometry = current_geometry
            end_geometry = QRect(current_geometry.x() + distance, current_geometry.y(),
                               current_geometry.width(), current_geometry.height())
        else:
            start_geometry = current_geometry
            end_geometry = current_geometry
            
        animation.setStartValue(start_geometry)
        animation.setEndValue(end_geometry)
        
        return animation
    
    @staticmethod
    def create_scale_animation(widget: QWidget,
                             scale_factor: float = 1.05,
                             config: Optional[AnimationConfig] = None) -> QVariantAnimation:
        """Create scale animation using custom variant animation"""
        if config is None:
            config = AnimationConfig(duration=DT.DURATION_FAST)
            
        animation = QVariantAnimation()
        animation.setDuration(config.duration)
        animation.setEasingCurve(AnimationUtils.get_easing_curve(config.easing))
        animation.setStartValue(1.0)
        animation.setEndValue(scale_factor)
        
        original_size = widget.size()
        original_pos = widget.pos()
        
        def update_scale(value):
            scale = value
            new_width = int(original_size.width() * scale)
            new_height = int(original_size.height() * scale)
            
            # Center the scaling
            offset_x = (new_width - original_size.width()) // 2
            offset_y = (new_height - original_size.height()) // 2
            
            new_x = original_pos.x() - offset_x
            new_y = original_pos.y() - offset_y
            
            widget.setGeometry(new_x, new_y, new_width, new_height)
            
        animation.valueChanged.connect(update_scale)
        
        return animation
    
    @staticmethod
    def create_glow_animation(widget: QWidget,
                            glow_color: str = DT.PRIMARY,
                            max_blur: int = 20,
                            config: Optional[AnimationConfig] = None) -> QPropertyAnimation:
        """Create glow effect animation using drop shadow"""
        if config is None:
            config = AnimationConfig(duration=DT.DURATION_NORMAL)
            
        # Create or get shadow effect
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsDropShadowEffect):
            effect = QGraphicsDropShadowEffect()
            effect.setColor(QColor(glow_color))
            effect.setOffset(0, 0)
            widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"blurRadius")
        animation.setDuration(config.duration)
        animation.setEasingCurve(AnimationUtils.get_easing_curve(config.easing))
        animation.setStartValue(0)
        animation.setEndValue(max_blur)
        
        return animation
    
    @staticmethod
    def create_color_animation(widget: QWidget,
                             start_color: str,
                             end_color: str,
                             config: Optional[AnimationConfig] = None) -> QVariantAnimation:
        """Create color transition animation"""
        if config is None:
            config = AnimationConfig()
            
        animation = QVariantAnimation()
        animation.setDuration(config.duration)
        animation.setEasingCurve(AnimationUtils.get_easing_curve(config.easing))
        animation.setStartValue(QColor(start_color))
        animation.setEndValue(QColor(end_color))
        
        def update_color(color):
            # Update widget background color
            palette = widget.palette()
            palette.setColor(QPalette.ColorRole.Window, color)
            widget.setPalette(palette)
            
        animation.valueChanged.connect(update_color)
        
        return animation
    
    @staticmethod
    def create_bounce_animation(widget: QWidget,
                              bounce_height: int = 10,
                              config: Optional[AnimationConfig] = None) -> QSequentialAnimationGroup:
        """Create bounce animation effect"""
        if config is None:
            config = AnimationConfig(duration=DT.DURATION_SLOW)
            
        group = QSequentialAnimationGroup()
        
        # Bounce up
        up_animation = AnimationUtils.create_slide_animation(
            widget, "up", bounce_height, 
            AnimationConfig(config.duration // 2, DT.EASE_OUT_QUAD)
        )
        
        # Bounce down
        down_animation = AnimationUtils.create_slide_animation(
            widget, "down", bounce_height,
            AnimationConfig(config.duration // 2, DT.EASE_IN_QUAD)
        )
        
        group.addAnimation(up_animation)
        group.addAnimation(down_animation)
        
        return group
    
    @staticmethod
    def create_shake_animation(widget: QWidget,
                             shake_distance: int = 5,
                             shake_count: int = 3,
                             config: Optional[AnimationConfig] = None) -> QSequentialAnimationGroup:
        """Create shake animation for error states"""
        if config is None:
            config = AnimationConfig(duration=DT.DURATION_SLOW)
            
        group = QSequentialAnimationGroup()
        single_shake_duration = config.duration // (shake_count * 2)
        
        for i in range(shake_count):
            # Shake right
            right_animation = AnimationUtils.create_slide_animation(
                widget, "right", shake_distance,
                AnimationConfig(single_shake_duration, DT.EASE_IN_OUT_SINE)
            )
            
            # Shake left
            left_animation = AnimationUtils.create_slide_animation(
                widget, "left", shake_distance * 2,  # Double distance to return to center
                AnimationConfig(single_shake_duration, DT.EASE_IN_OUT_SINE)
            )
            
            group.addAnimation(right_animation)
            group.addAnimation(left_animation)
            
        return group


class HoverAnimator(QObject):
    """
    Specialized class for handling hover animations on interactive elements
    Provides smooth hover in/out effects with proper state management
    """
    
    def __init__(self, widget: QWidget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.hover_in_animation = None
        self.hover_out_animation = None
        self.is_hovering = False
        self.animation_config = AnimationConfig(duration=DT.DURATION_FAST)
        
        # Install event filter to capture hover events
        self.widget.installEventFilter(self)
        
    def set_hover_effects(self,
                         scale_factor: float = 1.02,
                         glow_enabled: bool = True,
                         glow_color: str = DT.PRIMARY,
                         shadow_enabled: bool = True):
        """Configure hover effects"""
        self.scale_factor = scale_factor
        self.glow_enabled = glow_enabled
        self.glow_color = glow_color
        self.shadow_enabled = shadow_enabled
        
        self._setup_animations()
        
    def _setup_animations(self):
        """Setup hover in and out animations"""
        # Hover in animation group
        self.hover_in_group = QParallelAnimationGroup()
        
        # Scale animation
        if hasattr(self, 'scale_factor'):
            scale_anim = AnimationUtils.create_scale_animation(
                self.widget, self.scale_factor, self.animation_config
            )
            self.hover_in_group.addAnimation(scale_anim)
        
        # Glow animation
        if hasattr(self, 'glow_enabled') and self.glow_enabled:
            glow_anim = AnimationUtils.create_glow_animation(
                self.widget, self.glow_color, 15, self.animation_config
            )
            self.hover_in_group.addAnimation(glow_anim)
            
        # Hover out animation group
        self.hover_out_group = QParallelAnimationGroup()
        
        # Scale back animation
        if hasattr(self, 'scale_factor'):
            scale_back_anim = AnimationUtils.create_scale_animation(
                self.widget, 1.0, self.animation_config
            )
            self.hover_out_group.addAnimation(scale_back_anim)
            
        # Glow fade animation
        if hasattr(self, 'glow_enabled') and self.glow_enabled:
            glow_fade_anim = AnimationUtils.create_glow_animation(
                self.widget, self.glow_color, 0, self.animation_config
            )
            self.hover_out_group.addAnimation(glow_fade_anim)
    
    def eventFilter(self, obj, event):
        """Filter hover events"""
        if obj == self.widget:
            if event.type() == event.Type.Enter and not self.is_hovering:
                self.start_hover_in()
            elif event.type() == event.Type.Leave and self.is_hovering:
                self.start_hover_out()
                
        return super().eventFilter(obj, event)
    
    def start_hover_in(self):
        """Start hover in animation"""
        if self.hover_out_group and self.hover_out_group.state() == QAbstractAnimation.State.Running:
            self.hover_out_group.stop()
            
        if self.hover_in_group:
            self.hover_in_group.start()
            
        self.is_hovering = True
        
    def start_hover_out(self):
        """Start hover out animation"""
        if self.hover_in_group and self.hover_in_group.state() == QAbstractAnimation.State.Running:
            self.hover_in_group.stop()
            
        if self.hover_out_group:
            self.hover_out_group.start()
            
        self.is_hovering = False


class LoadingAnimator(QObject):
    """
    Specialized class for loading state animations
    Provides various loading indicators and state transitions
    """
    
    def __init__(self, widget: QWidget, parent=None):
        super().__init__(parent)
        self.widget = widget
        self.loading_animation = None
        self.is_loading = False
        self.original_opacity = 1.0
        
    def start_loading(self, animation_type: str = "fade"):
        """Start loading animation"""
        if self.is_loading:
            return
            
        self.is_loading = True
        
        if animation_type == "fade":
            self._start_fade_loading()
        elif animation_type == "pulse":
            self._start_pulse_loading()
        elif animation_type == "shimmer":
            self._start_shimmer_loading()
        elif animation_type == "spin":
            self._start_spin_loading()
            
    def stop_loading(self):
        """Stop loading animation and restore normal state"""
        if not self.is_loading:
            return
            
        self.is_loading = False
        
        if self.loading_animation:
            self.loading_animation.stop()
            
        # Restore original state
        self._restore_original_state()
        
    def _start_fade_loading(self):
        """Start fade loading animation"""
        config = AnimationConfig(duration=DT.DURATION_SLOW)
        self.loading_animation = AnimationUtils.create_fade_animation(
            self.widget, False, config
        )
        
        def on_fade_finished():
            if self.is_loading:
                # Fade back in
                fade_in = AnimationUtils.create_fade_animation(
                    self.widget, True, config
                )
                fade_in.finished.connect(lambda: self._start_fade_loading() if self.is_loading else None)
                fade_in.start()
                
        self.loading_animation.finished.connect(on_fade_finished)
        self.loading_animation.start()
        
    def _start_pulse_loading(self):
        """Start pulse loading animation"""
        config = AnimationConfig(duration=DT.DURATION_NORMAL)
        self.loading_animation = AnimationUtils.create_scale_animation(
            self.widget, 1.05, config
        )
        
        def on_pulse_finished():
            if self.is_loading:
                # Scale back down
                scale_down = AnimationUtils.create_scale_animation(
                    self.widget, 1.0, config
                )
                scale_down.finished.connect(lambda: self._start_pulse_loading() if self.is_loading else None)
                scale_down.start()
                
        self.loading_animation.finished.connect(on_pulse_finished)
        self.loading_animation.start()
        
    def _start_shimmer_loading(self):
        """Start shimmer loading animation"""
        # Create a shimmer effect using color animation
        config = AnimationConfig(duration=DT.DURATION_SLOWER)
        self.loading_animation = AnimationUtils.create_color_animation(
            self.widget, DT.GLASS_MEDIUM, DT.GLASS_LIGHT, config
        )
        
        def on_shimmer_finished():
            if self.is_loading:
                # Shimmer back
                shimmer_back = AnimationUtils.create_color_animation(
                    self.widget, DT.GLASS_LIGHT, DT.GLASS_MEDIUM, config
                )
                shimmer_back.finished.connect(lambda: self._start_shimmer_loading() if self.is_loading else None)
                shimmer_back.start()
                
        self.loading_animation.finished.connect(on_shimmer_finished)
        self.loading_animation.start()
        
    def _start_spin_loading(self):
        """Start spin loading animation (for circular elements)"""
        # This would require custom rotation implementation
        # For now, use scale animation as placeholder
        self._start_pulse_loading()
        
    def _restore_original_state(self):
        """Restore widget to original state"""
        # Reset opacity
        effect = self.widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            effect.setOpacity(self.original_opacity)
            
        # Reset size and position
        # This would need to store original geometry
        pass


class PageTransitionAnimator(QObject):
    """
    Specialized class for page transition animations
    Handles smooth transitions between different pages/views
    """
    
    # Signals
    transition_started = pyqtSignal()
    transition_finished = pyqtSignal()
    
    def __init__(self, container_widget: QWidget, parent=None):
        super().__init__(parent)
        self.container = container_widget
        self.current_page = None
        self.transition_animation = None
        
    def transition_to_page(self, 
                          new_page: QWidget,
                          transition_type: str = "slide_left",
                          config: Optional[AnimationConfig] = None):
        """Transition to a new page with animation"""
        if config is None:
            config = AnimationConfig(duration=DT.DURATION_SLOW)
            
        if self.current_page == new_page:
            return
            
        self.transition_started.emit()
        
        if transition_type == "slide_left":
            self._slide_transition(new_page, "left", config)
        elif transition_type == "slide_right":
            self._slide_transition(new_page, "right", config)
        elif transition_type == "slide_up":
            self._slide_transition(new_page, "up", config)
        elif transition_type == "slide_down":
            self._slide_transition(new_page, "down", config)
        elif transition_type == "fade":
            self._fade_transition(new_page, config)
        elif transition_type == "scale":
            self._scale_transition(new_page, config)
        else:
            # Default to fade
            self._fade_transition(new_page, config)
            
    def _slide_transition(self, new_page: QWidget, direction: str, config: AnimationConfig):
        """Perform slide transition"""
        if self.current_page:
            # Slide out current page
            out_animation = AnimationUtils.create_slide_animation(
                self.current_page, direction, self.container.width(), config
            )
            out_animation.finished.connect(lambda: self.current_page.hide())
            out_animation.start()
            
        # Slide in new page
        new_page.show()
        in_animation = AnimationUtils.create_slide_animation(
            new_page, self._opposite_direction(direction), self.container.width(), config
        )
        in_animation.finished.connect(self._on_transition_finished)
        in_animation.start()
        
        self.current_page = new_page
        
    def _fade_transition(self, new_page: QWidget, config: AnimationConfig):
        """Perform fade transition"""
        group = QSequentialAnimationGroup()
        
        if self.current_page:
            # Fade out current page
            fade_out = AnimationUtils.create_fade_animation(
                self.current_page, False, config
            )
            fade_out.finished.connect(lambda: self.current_page.hide())
            group.addAnimation(fade_out)
            
        # Fade in new page
        new_page.show()
        fade_in = AnimationUtils.create_fade_animation(
            new_page, True, config
        )
        group.addAnimation(fade_in)
        
        group.finished.connect(self._on_transition_finished)
        group.start()
        
        self.current_page = new_page
        
    def _scale_transition(self, new_page: QWidget, config: AnimationConfig):
        """Perform scale transition"""
        if self.current_page:
            # Scale down current page
            scale_out = AnimationUtils.create_scale_animation(
                self.current_page, 0.8, config
            )
            scale_out.finished.connect(lambda: self.current_page.hide())
            scale_out.start()
            
        # Scale up new page
        new_page.show()
        scale_in = AnimationUtils.create_scale_animation(
            new_page, 1.0, config
        )
        scale_in.finished.connect(self._on_transition_finished)
        scale_in.start()
        
        self.current_page = new_page
        
    def _opposite_direction(self, direction: str) -> str:
        """Get opposite direction for slide animations"""
        opposites = {
            "left": "right",
            "right": "left",
            "up": "down",
            "down": "up"
        }
        return opposites.get(direction, "left")
        
    def _on_transition_finished(self):
        """Handle transition completion"""
        self.transition_finished.emit()


class MicroInteractionAnimator(QObject):
    """
    Specialized class for micro-interactions
    Handles small, delightful animations that provide feedback
    """
    
    def __init__(self, widget: QWidget, parent=None):
        super().__init__(parent)
        self.widget = widget
        
    def button_press_feedback(self):
        """Provide visual feedback for button press"""
        config = AnimationConfig(duration=DT.DURATION_FAST)
        
        # Quick scale down then back up
        group = QSequentialAnimationGroup()
        
        scale_down = AnimationUtils.create_scale_animation(
            self.widget, 0.95, config
        )
        
        scale_up = AnimationUtils.create_scale_animation(
            self.widget, 1.0, config
        )
        
        group.addAnimation(scale_down)
        group.addAnimation(scale_up)
        group.start()
        
    def success_feedback(self):
        """Provide success feedback animation"""
        config = AnimationConfig(duration=DT.DURATION_NORMAL)
        
        # Green glow effect
        glow_animation = AnimationUtils.create_glow_animation(
            self.widget, DT.SUCCESS_400, 20, config
        )
        
        # Fade out glow after delay
        def fade_glow():
            fade_config = AnimationConfig(duration=DT.DURATION_SLOW)
            fade_glow_anim = AnimationUtils.create_glow_animation(
                self.widget, DT.SUCCESS_400, 0, fade_config
            )
            fade_glow_anim.start()
            
        glow_animation.finished.connect(lambda: QTimer.singleShot(500, fade_glow))
        glow_animation.start()
        
    def error_feedback(self):
        """Provide error feedback animation"""
        # Shake animation with red glow
        shake_anim = AnimationUtils.create_shake_animation(self.widget)
        
        config = AnimationConfig(duration=DT.DURATION_NORMAL)
        glow_anim = AnimationUtils.create_glow_animation(
            self.widget, DT.DANGER_400, 15, config
        )
        
        # Start both animations
        shake_anim.start()
        glow_anim.start()
        
        # Fade out glow after shake completes
        def fade_glow():
            fade_config = AnimationConfig(duration=DT.DURATION_SLOW)
            fade_glow_anim = AnimationUtils.create_glow_animation(
                self.widget, DT.DANGER_400, 0, fade_config
            )
            fade_glow_anim.start()
            
        shake_anim.finished.connect(lambda: QTimer.singleShot(200, fade_glow))
        
    def attention_pulse(self, pulse_count: int = 3):
        """Create attention-grabbing pulse animation"""
        config = AnimationConfig(duration=DT.DURATION_NORMAL)
        
        def create_pulse():
            if pulse_count > 0:
                pulse_anim = AnimationUtils.create_scale_animation(
                    self.widget, 1.1, config
                )
                
                def pulse_back():
                    back_anim = AnimationUtils.create_scale_animation(
                        self.widget, 1.0, config
                    )
                    back_anim.finished.connect(lambda: QTimer.singleShot(100, create_pulse))
                    back_anim.start()
                    
                pulse_anim.finished.connect(pulse_back)
                pulse_anim.start()
                
        create_pulse()


# Convenience functions for easy animation creation
def animate_fade_in(widget: QWidget, duration: int = DT.DURATION_NORMAL) -> QPropertyAnimation:
    """Convenience function for fade in animation"""
    config = AnimationConfig(duration=duration)
    return AnimationUtils.create_fade_animation(widget, True, config)


def animate_fade_out(widget: QWidget, duration: int = DT.DURATION_NORMAL) -> QPropertyAnimation:
    """Convenience function for fade out animation"""
    config = AnimationConfig(duration=duration)
    return AnimationUtils.create_fade_animation(widget, False, config)


def animate_slide_in(widget: QWidget, direction: str = "up", duration: int = DT.DURATION_SLOW) -> QPropertyAnimation:
    """Convenience function for slide in animation"""
    config = AnimationConfig(duration=duration)
    return AnimationUtils.create_slide_animation(widget, direction, 50, config)


def animate_hover_effect(widget: QWidget) -> HoverAnimator:
    """Convenience function to add hover effects to a widget"""
    hover_animator = HoverAnimator(widget)
    hover_animator.set_hover_effects(
        scale_factor=1.02,
        glow_enabled=True,
        glow_color=DT.PRIMARY,
        shadow_enabled=True
    )
    return hover_animator


def animate_button_press(widget: QWidget):
    """Convenience function for button press feedback"""
    micro_animator = MicroInteractionAnimator(widget)
    micro_animator.button_press_feedback()


def animate_loading_state(widget: QWidget, animation_type: str = "fade") -> LoadingAnimator:
    """Convenience function to add loading animation to a widget"""
    loading_animator = LoadingAnimator(widget)
    loading_animator.start_loading(animation_type)
    return loading_animator


def animate_success_feedback(widget: QWidget):
    """Convenience function for success feedback"""
    micro_animator = MicroInteractionAnimator(widget)
    micro_animator.success_feedback()


def animate_error_feedback(widget: QWidget):
    """Convenience function for error feedback"""
    micro_animator = MicroInteractionAnimator(widget)
    micro_animator.error_feedback()