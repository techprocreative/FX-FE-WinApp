# Enhanced Animation System Guide

This guide explains how to use the new Enhanced Animation System implemented for the NexusTrade UI modernization.

## Overview

The Enhanced Animation System provides smooth transitions, micro-interactions, hover effects, and loading animations throughout the application. It consists of several key components:

1. **Animation System Core** (`ui/animation_system.py`)
2. **Page Transitions** (`ui/page_transitions.py`)
3. **Loading States** (`ui/loading_states.py`)
4. **Modern Base Components** (updated `ui/components/modern_base.py`)

## Key Features

### ✨ Smooth Transitions
- Fade in/out animations
- Slide animations (up, down, left, right)
- Scale animations for hover effects
- Color transition animations

### 🎯 Micro-Interactions
- Button press feedback
- Success/error feedback animations
- Attention-grabbing pulse effects
- Shake animations for error states

### 🔄 Loading States
- Spinning loaders
- Animated dots
- Progress bars with smooth animations
- Loading cards with skeleton content

### 📱 Page Transitions
- Smooth transitions between pages
- Multiple transition types (fade, slide, scale)
- Navigation history management
- Loading overlays

## Quick Start

### Basic Animation Usage

```python
from ui.animation_system import animate_fade_in, animate_button_press

# Fade in a widget
animation = animate_fade_in(my_widget, duration=300)
animation.start()

# Add button press feedback
animate_button_press(my_button)
```

### Using Modern Components

The updated modern components automatically include animations:

```python
from ui.components.modern_base import ModernCard, ModernButton, ModernInput

# Create a clickable card with hover animations
card = ModernCard(preset="default", clickable=True)

# Create a button with press feedback
button = ModernButton("Click Me", variant="primary")

# Create an input with focus animations
input_field = ModernInput(placeholder="Enter text", validation_state="default")
```

### Page Transitions

```python
from ui.page_transitions import create_page_manager

# Create a page manager
stacked_widget, page_manager = create_page_manager(parent_widget)

# Register pages
page_manager.register_page("dashboard", dashboard_widget)
page_manager.register_page("settings", settings_widget)

# Set transition type
page_manager.set_transition_type("slide_left")

# Navigate with smooth transition
page_manager.navigate_to("settings")
```

### Loading States

```python
from ui.loading_states import loading_manager, show_loading_card

# Register a component for loading management
loading_manager.register_component("my_component", my_widget)

# Start loading
loading_manager.start_loading("my_component", "Processing...")

# Update progress
loading_manager.update_progress("my_component", 50)

# Stop loading
loading_manager.stop_loading("my_component")

# Or create a loading card
loading_card = show_loading_card(parent, "Loading data...", show_progress=True)
```

## Animation Configuration

### AnimationConfig

Control animation parameters with `AnimationConfig`:

```python
from ui.animation_system import AnimationConfig, AnimationUtils
from ui.design_system import DesignTokens as DT

# Create custom animation config
config = AnimationConfig(
    duration=DT.DURATION_SLOW,    # 500ms
    easing=DT.EASE_OUT_BACK,      # Bouncy easing
    delay=DT.DELAY_SHORT          # 50ms delay
)

# Use with animations
fade_anim = AnimationUtils.create_fade_animation(widget, True, config)
```

### Available Easing Curves

- `DT.EASE_LINEAR` - Linear timing
- `DT.EASE_OUT_CUBIC` - Default smooth easing
- `DT.EASE_IN_OUT_BACK` - Bouncy effect
- `DT.EASE_OUT_BOUNCE` - Bounce at the end
- And many more...

### Duration Constants

- `DT.DURATION_INSTANT` - 0ms
- `DT.DURATION_FAST` - 100ms
- `DT.DURATION_NORMAL` - 200ms (default)
- `DT.DURATION_SLOW` - 300ms
- `DT.DURATION_SLOWER` - 500ms
- `DT.DURATION_SLOWEST` - 1000ms

## Advanced Usage

### Custom Hover Effects

```python
from ui.animation_system import HoverAnimator

# Create custom hover animator
hover_animator = HoverAnimator(my_widget)
hover_animator.set_hover_effects(
    scale_factor=1.05,
    glow_enabled=True,
    glow_color=DT.PRIMARY,
    shadow_enabled=True
)
```

### Loading Animations

```python
from ui.animation_system import LoadingAnimator

# Create loading animator
loading_animator = LoadingAnimator(my_widget)

# Start different loading types
loading_animator.start_loading("fade")     # Fade in/out
loading_animator.start_loading("pulse")    # Scale pulse
loading_animator.start_loading("shimmer")  # Color shimmer

# Stop loading
loading_animator.stop_loading()
```

### Micro-Interactions

```python
from ui.animation_system import MicroInteractionAnimator

# Create micro-interaction animator
micro_animator = MicroInteractionAnimator(my_widget)

# Trigger different feedback types
micro_animator.button_press_feedback()  # Press feedback
micro_animator.success_feedback()       # Success glow
micro_animator.error_feedback()         # Error shake + glow
micro_animator.attention_pulse(3)       # 3 attention pulses
```

### Animation Manager

The global animation manager coordinates all animations:

```python
from ui.animation_system import animation_manager

# Register animations for management
animation_manager.register_animation("my_anim", my_animation)

# Control animations
animation_manager.start_animation("my_anim")
animation_manager.pause_animation("my_anim")
animation_manager.stop_animation("my_anim")

# Performance mode (reduces animation quality)
animation_manager.set_performance_mode(True)
```

## Component Integration

### ModernCard

```python
card = ModernCard(preset="default", clickable=True)

# Loading states
card.set_loading(True)   # Shows pulse animation
card.set_loading(False)  # Stops animation

# Feedback states
card.set_error(True, "Error message")  # Shows error animation
card.set_success(True)                 # Shows success animation
```

### ModernButton

```python
button = ModernButton("Submit", variant="primary")

# Loading state
button.set_loading(True)   # Shows loading spinner
button.set_loading(False)  # Restores normal state

# Feedback animations
button.set_success_feedback()  # Success glow
button.set_error_feedback()    # Error shake
```

### ModernInput

```python
input_field = ModernInput(placeholder="Email")

# Validation with animations
input_field.set_validation_state("error", "Invalid email")    # Error shake
input_field.set_validation_state("success", "Email valid")   # Success glow
input_field.set_validation_state("default", "")              # Reset
```

## Page Transitions

### Available Transition Types

- `"fade"` - Fade between pages
- `"slide_left"` - Slide left
- `"slide_right"` - Slide right
- `"slide_up"` - Slide up
- `"slide_down"` - Slide down
- `"scale"` - Scale transition
- `"none"` - No transition

### Navigation Guards

```python
def confirm_navigation(from_page, to_page):
    """Guard function to confirm navigation"""
    if from_page == "unsaved_form":
        # Show confirmation dialog
        return user_confirmed_navigation()
    return True

# Set navigation guard
page_manager.set_navigation_guard("unsaved_form", confirm_navigation)
```

## Loading States

### Loading Spinner

```python
from ui.loading_states import LoadingSpinner

spinner = LoadingSpinner(size=32, color=DT.PRIMARY, thickness=3)
spinner.start_spinning()
# ... later
spinner.stop_spinning()
```

### Loading Dots

```python
from ui.loading_states import LoadingDots

dots = LoadingDots(dot_count=3, color=DT.PRIMARY)
dots.start_animation()
# ... later
dots.stop_animation()
```

### Loading Cards

```python
from ui.loading_states import LoadingCard

card = LoadingCard(
    title="Loading data...",
    subtitle="Please wait",
    show_progress=True
)
card.start_loading()
card.set_progress(50)  # Update progress
card.stop_loading()
```

## Performance Considerations

### Animation Performance

- Animations automatically adjust for screen size
- Performance mode available for low-end devices
- Animations can be disabled for accessibility

```python
# Enable performance mode
animation_manager.set_performance_mode(True)

# Check if reduced motion is preferred (accessibility)
from ui.design_system import AccessibilityUtils
reduced_motion_styles = AccessibilityUtils.get_reduced_motion_styles()
```

### Memory Management

- Animations are automatically cleaned up when finished
- Use the animation manager for complex animation coordination
- Loading states are properly managed to prevent memory leaks

## Best Practices

### 1. Use Appropriate Durations

```python
# Quick feedback
animate_button_press(button)  # Uses DURATION_FAST (100ms)

# Page transitions
page_manager.set_transition_duration(DT.DURATION_SLOW)  # 300ms

# Loading states
loading_animator.start_loading("fade")  # Uses DURATION_NORMAL (200ms)
```

### 2. Choose Appropriate Easing

```python
# Smooth, natural feeling
config = AnimationConfig(easing=DT.EASE_OUT_CUBIC)

# Bouncy, playful
config = AnimationConfig(easing=DT.EASE_OUT_BACK)

# Sharp, precise
config = AnimationConfig(easing=DT.EASE_IN_OUT_QUAD)
```

### 3. Provide Feedback

```python
# Always provide feedback for user actions
button.clicked.connect(lambda: button.set_success_feedback())

# Show loading states for long operations
loading_manager.start_loading("data_fetch", "Loading...")
# ... perform operation
loading_manager.stop_loading("data_fetch")
```

### 4. Respect Accessibility

```python
# Check for reduced motion preferences
if user_prefers_reduced_motion():
    page_manager.set_transition_type("none")
    animation_manager.set_performance_mode(True)
```

## Troubleshooting

### Common Issues

1. **Animations not starting**: Check that the widget is visible and has proper parent
2. **Jerky animations**: Enable performance mode or reduce animation complexity
3. **Memory leaks**: Ensure animations are properly cleaned up using the animation manager
4. **Accessibility issues**: Provide options to disable animations

### Debug Mode

```python
# Enable animation debugging
animation_manager.debug_mode = True

# Check animation states
print(f"Active animations: {len(animation_manager.active_animations)}")
print(f"Performance mode: {animation_manager.performance_mode}")
```

## Examples

See the test files for complete examples:
- `test_modern_components.py` - Basic component usage
- `validate_animation_system.py` - System validation
- Property tests in `tests/property/` - Advanced usage patterns

## Requirements Validation

This animation system fulfills the following requirements:

- **4.1**: Smooth transitions for data updates ✅
- **4.2**: Fluid page transitions ✅  
- **4.3**: Immediate visual feedback on hover ✅
- **4.4**: Elegant loading states and progress indicators ✅

The system provides comprehensive animation support while maintaining performance and accessibility standards.