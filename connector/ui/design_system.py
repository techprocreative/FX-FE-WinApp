"""
NexusTrade Design System
Centralized design tokens for consistent UI across all windows
Enhanced with modern color palettes, typography scales, shadow systems,
animation timing curves, and glass morphism utilities.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen
from PyQt6.QtCore import QEasingCurve
from typing import Dict, Tuple, Any
import math


class DesignTokens:
    """Design tokens - single source of truth for all UI styling"""

    # ============================================
    # SCREEN-AWARE DIMENSIONS
    # ============================================

    @staticmethod
    def get_screen_size():
        """Get primary screen size"""
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                geometry = screen.availableGeometry()
                return geometry.width(), geometry.height()
        # Fallback for common HD resolution
        return 1920, 1080

    @classmethod
    def get_screen_tier(cls):
        """
        Determine screen size tier for responsive layouts

        Returns:
            str: 'small' (≤1024), 'medium' (1025-1600), or 'large' (>1600)
        """
        screen_w, screen_h = cls.get_screen_size()

        if screen_w <= 1024:
            return 'small'
        elif screen_w <= 1600:
            return 'medium'
        else:
            return 'large'

    @classmethod
    def get_responsive_window_size(cls):
        """Calculate responsive window size based on screen tier"""
        screen_w, screen_h = cls.get_screen_size()
        tier = cls.get_screen_tier()

        if tier == 'small':
            # For 1024x768 and similar - use almost full screen
            target_w = int(screen_w * 0.95)  # 95% to leave some taskbar space
            target_h = int(screen_h * 0.90)

            # Minimum for small screens
            min_w = 960   # Reduced from 1200
            min_h = 650   # Reduced from 700

            # Maximum for small screens
            max_w = 1024
            max_h = 768

        elif tier == 'medium':
            # For 1366x768, 1440x900 - use comfortable percentage
            target_w = int(screen_w * 0.90)
            target_h = int(screen_h * 0.88)

            # Minimum/Maximum for medium screens
            min_w = 1100
            min_h = 680
            max_w = 1600
            max_h = 1000

        else:  # large
            # For 1920x1080 and larger - use smaller percentage
            target_w = int(screen_w * 0.75)  # Don't need full screen on large monitors
            target_h = int(screen_h * 0.80)

            # Minimum/Maximum for large screens
            min_w = 1400
            min_h = 800
            max_w = 1920
            max_h = 1200

        # Clamp values
        width = max(min_w, min(target_w, max_w))
        height = max(min_h, min(target_h, max_h))

        return width, height

    @classmethod
    def get_responsive_sidebar_width(cls):
        """Get sidebar width based on screen tier"""
        tier = cls.get_screen_tier()

        if tier == 'small':
            return 220  # Narrower sidebar for small screens
        elif tier == 'medium':
            return 250
        else:
            return 280  # Original width for large screens

    @classmethod
    def get_responsive_card_sizes(cls):
        """
        Get responsive card minimum sizes based on screen tier

        Returns:
            dict: {'stat_card': (width, height), 'signal_card': (width, height)}
        """
        tier = cls.get_screen_tier()

        if tier == 'small':
            return {
                'stat_card': (150, 100),     # Smaller cards
                'signal_card': (260, 240)     # Reduced from 320x280
            }
        elif tier == 'medium':
            return {
                'stat_card': (170, 110),
                'signal_card': (300, 260)
            }
        else:  # large
            return {
                'stat_card': (180, 120),     # Original sizes
                'signal_card': (320, 280)
            }

    @classmethod
    def get_responsive_spacing(cls):
        """Get responsive spacing multiplier based on screen tier"""
        tier = cls.get_screen_tier()

        if tier == 'small':
            return 0.75  # Reduce spacing by 25% on small screens
        elif tier == 'medium':
            return 0.9   # Reduce spacing by 10% on medium screens
        else:
            return 1.0   # Original spacing on large screens

    # ============================================
    # ENHANCED COLOR PALETTE
    # ============================================

    # Primary Colors - Enhanced with more variants
    PRIMARY = "#06b6d4"          # Cyan
    PRIMARY_50 = "#ecfeff"       # Very light cyan
    PRIMARY_100 = "#cffafe"      # Light cyan
    PRIMARY_200 = "#a5f3fc"      # Lighter cyan
    PRIMARY_300 = "#67e8f9"      # Light cyan
    PRIMARY_400 = "#22d3ee"      # Medium cyan
    PRIMARY_500 = "#06b6d4"      # Base primary
    PRIMARY_600 = "#0891b2"      # Dark cyan
    PRIMARY_700 = "#0e7490"      # Darker cyan
    PRIMARY_800 = "#155e75"      # Very dark cyan
    PRIMARY_900 = "#164e63"      # Darkest cyan
    
    # Legacy aliases for backward compatibility
    PRIMARY_DARK = "#0891b2"
    PRIMARY_DARKER = "#0e7490"
    PRIMARY_LIGHT = "#22d3ee"
    PRIMARY_HOVER = "#0ea5e9"

    # Secondary Colors - Enhanced teal palette
    SECONDARY = "#14b8a6"        # Teal
    SECONDARY_50 = "#f0fdfa"     # Very light teal
    SECONDARY_100 = "#ccfbf1"    # Light teal
    SECONDARY_200 = "#99f6e4"    # Lighter teal
    SECONDARY_300 = "#5eead4"    # Light teal
    SECONDARY_400 = "#2dd4bf"    # Medium teal
    SECONDARY_500 = "#14b8a6"    # Base secondary
    SECONDARY_600 = "#0d9488"    # Dark teal
    SECONDARY_700 = "#0f766e"    # Darker teal
    SECONDARY_800 = "#115e59"    # Very dark teal
    SECONDARY_900 = "#134e4a"    # Darkest teal
    
    # Legacy aliases
    SECONDARY_DARK = "#0d9488"
    SECONDARY_DARKER = "#0f766e"

    # Semantic Colors - Enhanced with full palettes
    SUCCESS = "#10b981"          # Green
    SUCCESS_50 = "#ecfdf5"
    SUCCESS_100 = "#d1fae5"
    SUCCESS_200 = "#a7f3d0"
    SUCCESS_300 = "#6ee7b7"
    SUCCESS_400 = "#34d399"
    SUCCESS_500 = "#10b981"
    SUCCESS_600 = "#059669"
    SUCCESS_700 = "#047857"
    SUCCESS_800 = "#065f46"
    SUCCESS_900 = "#064e3b"
    SUCCESS_DARK = "#059669"     # Legacy alias

    DANGER = "#f43f5e"           # Rose
    DANGER_50 = "#fff1f2"
    DANGER_100 = "#ffe4e6"
    DANGER_200 = "#fecdd3"
    DANGER_300 = "#fda4af"
    DANGER_400 = "#fb7185"
    DANGER_500 = "#f43f5e"
    DANGER_600 = "#e11d48"
    DANGER_700 = "#be123c"
    DANGER_800 = "#9f1239"
    DANGER_900 = "#881337"
    DANGER_DARK = "#e11d48"      # Legacy alias
    DANGER_DARKER = "#be123c"    # Legacy alias

    WARNING = "#fbbf24"          # Amber
    WARNING_50 = "#fffbeb"
    WARNING_100 = "#fef3c7"
    WARNING_200 = "#fde68a"
    WARNING_300 = "#fcd34d"
    WARNING_400 = "#fbbf24"
    WARNING_500 = "#f59e0b"
    WARNING_600 = "#d97706"
    WARNING_700 = "#b45309"
    WARNING_800 = "#92400e"
    WARNING_900 = "#78350f"

    INFO = "#3b82f6"             # Blue
    INFO_50 = "#eff6ff"
    INFO_100 = "#dbeafe"
    INFO_200 = "#bfdbfe"
    INFO_300 = "#93c5fd"
    INFO_400 = "#60a5fa"
    INFO_500 = "#3b82f6"
    INFO_600 = "#2563eb"
    INFO_700 = "#1d4ed8"
    INFO_800 = "#1e40af"
    INFO_900 = "#1e3a8a"

    # Enhanced Neutral Palette
    NEUTRAL_50 = "#f8fafc"       # Slate 50
    NEUTRAL_100 = "#f1f5f9"      # Slate 100
    NEUTRAL_200 = "#e2e8f0"      # Slate 200
    NEUTRAL_300 = "#cbd5e1"      # Slate 300
    NEUTRAL_400 = "#94a3b8"      # Slate 400
    NEUTRAL_500 = "#64748b"      # Slate 500
    NEUTRAL_600 = "#475569"      # Slate 600
    NEUTRAL_700 = "#334155"      # Slate 700
    NEUTRAL_800 = "#1e293b"      # Slate 800
    NEUTRAL_900 = "#0f172a"      # Slate 900
    NEUTRAL_950 = "#020617"      # Slate 950

    # Background Colors - Enhanced with more options
    BG_DARKEST = "#0f172a"       # Slate 950
    BG_DARKER = "#020617"        # Slate 950 (even darker)
    BG_DARK = "#1e293b"          # Slate 900
    BG_MEDIUM = "#1e3a8a"        # Blue 900 (for gradients)
    BG_CARD = "#334155"          # Slate 700
    BG_SURFACE = "#475569"       # Slate 600
    BG_ELEVATED = "#64748b"      # Slate 500
    
    # Legacy aliases
    BACKGROUND_DARK = "#0f172a"

    # Enhanced Glass/Transparent Backgrounds
    GLASS_DARKEST = "rgba(15, 23, 42, 0.95)"
    GLASS_DARKER = "rgba(2, 6, 23, 0.9)"
    GLASS_DARK = "rgba(15, 23, 42, 0.8)"
    GLASS_MEDIUM = "rgba(30, 41, 59, 0.6)"
    GLASS_LIGHT = "rgba(51, 65, 85, 0.4)"
    GLASS_LIGHTER = "rgba(71, 85, 105, 0.3)"
    GLASS_LOW = "rgba(51, 65, 85, 0.2)"
    GLASS_SUBTLE = "rgba(100, 116, 139, 0.1)"

    # Text Colors - Enhanced hierarchy
    TEXT_PRIMARY = "#f8fafc"     # Slate 50
    TEXT_SECONDARY = "#e2e8f0"   # Slate 200
    TEXT_TERTIARY = "#cbd5e1"    # Slate 300
    TEXT_MUTED = "#94a3b8"       # Slate 400
    TEXT_DISABLED = "#64748b"    # Slate 500
    TEXT_PLACEHOLDER = "#475569" # Slate 600
    TEXT_INVERSE = "#0f172a"     # Dark text for light backgrounds

    # Border Colors - Enhanced with more variants
    BORDER_SUBTLE = "rgba(6, 182, 212, 0.1)"
    BORDER_DEFAULT = "rgba(6, 182, 212, 0.2)"
    BORDER_MEDIUM = "rgba(6, 182, 212, 0.3)"
    BORDER_STRONG = "rgba(6, 182, 212, 0.4)"
    BORDER_FOCUS = "rgba(6, 182, 212, 0.5)"
    BORDER_ACTIVE = "#06b6d4"
    
    # Neutral borders
    BORDER_NEUTRAL_SUBTLE = "rgba(148, 163, 184, 0.1)"
    BORDER_NEUTRAL_DEFAULT = "rgba(148, 163, 184, 0.2)"
    BORDER_NEUTRAL_MEDIUM = "rgba(148, 163, 184, 0.3)"
    BORDER_NEUTRAL_STRONG = "rgba(148, 163, 184, 0.4)"

    # ============================================
    # SPACING SCALE
    # ============================================

    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_BASE = 16
    SPACE_LG = 20
    SPACE_XL = 24
    SPACE_2XL = 32
    SPACE_3XL = 40
    SPACE_4XL = 48

    # ============================================
    # ENHANCED TYPOGRAPHY SYSTEM
    # ============================================

    # Font Families
    FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, sans-serif"
    FONT_FAMILY_MONO = "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace"
    FONT_FAMILY_DISPLAY = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, sans-serif"

    # Enhanced Font Size Scale (based on 1.125 ratio)
    FONT_2XS = 10
    FONT_XS = 11
    FONT_SM = 12
    FONT_BASE = 14
    FONT_LG = 16
    FONT_XL = 18
    FONT_2XL = 20
    FONT_3XL = 24
    FONT_4XL = 28
    FONT_5XL = 32
    FONT_6XL = 36
    FONT_7XL = 48
    FONT_8XL = 64
    FONT_9XL = 96

    # Font Weights - Enhanced with more options
    WEIGHT_THIN = 100
    WEIGHT_EXTRALIGHT = 200
    WEIGHT_LIGHT = 300
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    WEIGHT_EXTRABOLD = 800
    WEIGHT_BLACK = 900

    # Line Heights - Relative to font size
    LEADING_NONE = 1.0
    LEADING_TIGHT = 1.25
    LEADING_SNUG = 1.375
    LEADING_NORMAL = 1.5
    LEADING_RELAXED = 1.625
    LEADING_LOOSE = 2.0

    # Letter Spacing
    TRACKING_TIGHTER = -0.05
    TRACKING_TIGHT = -0.025
    TRACKING_NORMAL = 0
    TRACKING_WIDE = 0.025
    TRACKING_WIDER = 0.05
    TRACKING_WIDEST = 0.1

    # ============================================
    # ENHANCED BORDER RADIUS SCALE
    # ============================================

    RADIUS_NONE = 0
    RADIUS_XS = 2
    RADIUS_SM = 4
    RADIUS_DEFAULT = 6
    RADIUS_MD = 8
    RADIUS_LG = 10
    RADIUS_XL = 12
    RADIUS_2XL = 16
    RADIUS_3XL = 24
    RADIUS_FULL = 9999

    # ============================================
    # COMPREHENSIVE SHADOW SYSTEM
    # ============================================

    # Elevation Shadows - For layering UI elements
    SHADOW_NONE = "none"
    SHADOW_XS = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    SHADOW_SM = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)"
    SHADOW_DEFAULT = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
    SHADOW_MD = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)"
    SHADOW_LG = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"
    SHADOW_XL = "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
    SHADOW_2XL = "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
    SHADOW_INNER = "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)"

    # Colored Shadows - For emphasis and branding
    SHADOW_PRIMARY = "0 10px 15px -3px rgba(6, 182, 212, 0.1), 0 4px 6px -2px rgba(6, 182, 212, 0.05)"
    SHADOW_SECONDARY = "0 10px 15px -3px rgba(20, 184, 166, 0.1), 0 4px 6px -2px rgba(20, 184, 166, 0.05)"
    SHADOW_SUCCESS = "0 10px 15px -3px rgba(16, 185, 129, 0.1), 0 4px 6px -2px rgba(16, 185, 129, 0.05)"
    SHADOW_DANGER = "0 10px 15px -3px rgba(244, 63, 94, 0.1), 0 4px 6px -2px rgba(244, 63, 94, 0.05)"
    SHADOW_WARNING = "0 10px 15px -3px rgba(251, 191, 36, 0.1), 0 4px 6px -2px rgba(251, 191, 36, 0.05)"

    # Glow Effects - For interactive elements
    GLOW_NONE = "none"
    GLOW_SM = "0 0 5px rgba(6, 182, 212, 0.3)"
    GLOW_DEFAULT = "0 0 10px rgba(6, 182, 212, 0.4)"
    GLOW_MD = "0 0 15px rgba(6, 182, 212, 0.5)"
    GLOW_LG = "0 0 20px rgba(6, 182, 212, 0.6)"
    GLOW_XL = "0 0 30px rgba(6, 182, 212, 0.7)"
    
    # Legacy glow aliases
    GLOW_PRIMARY = "0 0 20px rgba(6, 182, 212, 0.4)"
    GLOW_SUCCESS = "0 0 20px rgba(16, 185, 129, 0.4)"
    GLOW_DANGER = "0 0 20px rgba(244, 63, 94, 0.4)"

    # Glass Morphism Shadows - For translucent elements
    SHADOW_GLASS_SM = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(255, 255, 255, 0.05)"
    SHADOW_GLASS_DEFAULT = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(255, 255, 255, 0.05)"
    SHADOW_GLASS_LG = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(255, 255, 255, 0.04)"

    # ============================================
    # ANIMATION TIMING SYSTEM
    # ============================================

    # Duration Scale (in milliseconds)
    DURATION_INSTANT = 0
    DURATION_FAST = 100
    DURATION_NORMAL = 200
    DURATION_SLOW = 300
    DURATION_SLOWER = 500
    DURATION_SLOWEST = 1000

    # Easing Curves - CSS-style timing functions
    EASE_LINEAR = "linear"
    EASE_DEFAULT = "ease"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    
    # Custom easing curves (cubic-bezier values)
    EASE_IN_SINE = "cubic-bezier(0.12, 0, 0.39, 0)"
    EASE_OUT_SINE = "cubic-bezier(0.61, 1, 0.88, 1)"
    EASE_IN_OUT_SINE = "cubic-bezier(0.37, 0, 0.63, 1)"
    
    EASE_IN_QUAD = "cubic-bezier(0.11, 0, 0.5, 0)"
    EASE_OUT_QUAD = "cubic-bezier(0.5, 1, 0.89, 1)"
    EASE_IN_OUT_QUAD = "cubic-bezier(0.45, 0, 0.55, 1)"
    
    EASE_IN_CUBIC = "cubic-bezier(0.32, 0, 0.67, 0)"
    EASE_OUT_CUBIC = "cubic-bezier(0.33, 1, 0.68, 1)"
    EASE_IN_OUT_CUBIC = "cubic-bezier(0.65, 0, 0.35, 1)"
    
    EASE_IN_QUART = "cubic-bezier(0.5, 0, 0.75, 0)"
    EASE_OUT_QUART = "cubic-bezier(0.25, 1, 0.5, 1)"
    EASE_IN_OUT_QUART = "cubic-bezier(0.76, 0, 0.24, 1)"
    
    EASE_IN_BACK = "cubic-bezier(0.36, 0, 0.66, -0.56)"
    EASE_OUT_BACK = "cubic-bezier(0.34, 1.56, 0.64, 1)"
    EASE_IN_OUT_BACK = "cubic-bezier(0.68, -0.6, 0.32, 1.6)"

    # Animation Delays
    DELAY_NONE = 0
    DELAY_SHORT = 50
    DELAY_MEDIUM = 100
    DELAY_LONG = 200

    # ============================================
    # GLASS MORPHISM UTILITIES
    # ============================================

    # Backdrop Blur Levels
    BLUR_NONE = 0
    BLUR_SM = 4
    BLUR_DEFAULT = 8
    BLUR_MD = 12
    BLUR_LG = 16
    BLUR_XL = 24
    BLUR_2XL = 40
    BLUR_3XL = 64

    # Glass Morphism Presets
    GLASS_PRESET_SUBTLE = {
        'background': GLASS_SUBTLE,
        'border': BORDER_NEUTRAL_SUBTLE,
        'blur': BLUR_SM,
        'shadow': SHADOW_GLASS_SM
    }
    
    GLASS_PRESET_DEFAULT = {
        'background': GLASS_LIGHT,
        'border': BORDER_DEFAULT,
        'blur': BLUR_DEFAULT,
        'shadow': SHADOW_GLASS_DEFAULT
    }
    
    GLASS_PRESET_STRONG = {
        'background': GLASS_MEDIUM,
        'border': BORDER_MEDIUM,
        'blur': BLUR_LG,
        'shadow': SHADOW_GLASS_LG
    }
    
    GLASS_PRESET_SIDEBAR = {
        'background': GLASS_DARK,
        'border': BORDER_SUBTLE,
        'blur': BLUR_MD,
        'shadow': SHADOW_LG
    }
    
    GLASS_PRESET_MODAL = {
        'background': GLASS_DARKER,
        'border': BORDER_STRONG,
        'blur': BLUR_XL,
        'shadow': SHADOW_2XL
    }

    # ============================================
    # DIMENSIONS
    # ============================================

    # Layout
    SIDEBAR_WIDTH = 280
    SIDEBAR_LOGO_HEIGHT = 100
    NAV_BUTTON_HEIGHT = 52

    # Windows - Responsive sizing (use get_responsive_window_size() for actual values)
    # These are kept for backward compatibility but should use dynamic sizing
    LOGIN_WIDTH = 600
    LOGIN_HEIGHT = 680

    # Main window sizes - will be calculated dynamically
    # Minimum sizes are screen-percentage based (see get_responsive_window_size)
    MAIN_MIN_WIDTH = 1200   # Absolute minimum
    MAIN_MIN_HEIGHT = 700   # Absolute minimum

    # Components
    BUTTON_HEIGHT_SM = 36
    BUTTON_HEIGHT_MD = 44
    BUTTON_HEIGHT_LG = 52

    INPUT_HEIGHT = 44
    CARD_MIN_HEIGHT = 120

    # ============================================
    # Z-INDEX SCALE
    # ============================================

    Z_DROPDOWN = 1000
    Z_STICKY = 1020
    Z_FIXED = 1030
    Z_MODAL_BACKDROP = 1040
    Z_MODAL = 1050
    Z_POPOVER = 1060
    Z_TOOLTIP = 1070
    Z_TOAST = 1080


class StyleSheets:
    """Enhanced stylesheet generators with modern effects and utilities"""

    # ============================================
    # ADVANCED GRADIENT GENERATORS
    # ============================================

    @staticmethod
    def gradient_primary() -> str:
        """Primary gradient (cyan to teal)"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.PRIMARY},
            stop:1 {DesignTokens.SECONDARY}
        )"""

    @staticmethod
    def gradient_primary_hover() -> str:
        """Primary gradient hover state"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.PRIMARY_DARK},
            stop:1 {DesignTokens.SECONDARY_DARK}
        )"""

    @staticmethod
    def gradient_primary_pressed() -> str:
        """Primary gradient pressed state"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.PRIMARY_DARKER},
            stop:1 {DesignTokens.SECONDARY_DARKER}
        )"""

    @staticmethod
    def gradient_danger() -> str:
        """Danger gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.DANGER},
            stop:1 {DesignTokens.DANGER_DARK}
        )"""

    @staticmethod
    def gradient_danger_hover() -> str:
        """Danger gradient hover state"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.DANGER_DARK},
            stop:1 {DesignTokens.DANGER_DARKER}
        )"""

    @staticmethod
    def gradient_success() -> str:
        """Success gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.SUCCESS_500},
            stop:1 {DesignTokens.SUCCESS_600}
        )"""

    @staticmethod
    def gradient_warning() -> str:
        """Warning gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.WARNING_400},
            stop:1 {DesignTokens.WARNING_500}
        )"""

    @staticmethod
    def gradient_info() -> str:
        """Info gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {DesignTokens.INFO_500},
            stop:1 {DesignTokens.INFO_600}
        )"""

    @staticmethod
    def gradient_background() -> str:
        """Main window background gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {DesignTokens.BG_DARKEST},
            stop:1 {DesignTokens.BG_MEDIUM}
        )"""

    @staticmethod
    def gradient_sidebar() -> str:
        """Sidebar background gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:0, y2:1,
            stop:0 {DesignTokens.GLASS_DARKEST},
            stop:1 {DesignTokens.GLASS_DARK}
        )"""

    @staticmethod
    def gradient_card() -> str:
        """Card background gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {DesignTokens.GLASS_MEDIUM},
            stop:1 {DesignTokens.GLASS_LIGHT}
        )"""

    @staticmethod
    def gradient_subtle() -> str:
        """Subtle background gradient"""
        return f"""qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {DesignTokens.GLASS_SUBTLE},
            stop:1 {DesignTokens.GLASS_LOW}
        )"""

    @staticmethod
    def gradient_radial_glow(color: str, opacity: float = 0.3) -> str:
        """Radial glow gradient for emphasis"""
        return f"""qradialgradient(
            cx:0.5, cy:0.5, radius:1,
            stop:0 rgba({color.replace('#', '')}, {opacity}),
            stop:1 rgba({color.replace('#', '')}, 0)
        )"""

    @staticmethod
    def gradient_custom(color1: str, color2: str, direction: str = "horizontal") -> str:
        """Custom gradient generator"""
        if direction == "vertical":
            return f"""qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {color1},
                stop:1 {color2}
            )"""
        elif direction == "diagonal":
            return f"""qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {color1},
                stop:1 {color2}
            )"""
        else:  # horizontal
            return f"""qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {color1},
                stop:1 {color2}
            )"""

    # ============================================
    # GLASS MORPHISM UTILITIES
    # ============================================

    @staticmethod
    def glass_card(preset: str = "default") -> str:
        """Glass morphism card with configurable presets"""
        presets = {
            "subtle": DesignTokens.GLASS_PRESET_SUBTLE,
            "default": DesignTokens.GLASS_PRESET_DEFAULT,
            "strong": DesignTokens.GLASS_PRESET_STRONG,
            "sidebar": DesignTokens.GLASS_PRESET_SIDEBAR,
            "modal": DesignTokens.GLASS_PRESET_MODAL
        }
        
        config = presets.get(preset, DesignTokens.GLASS_PRESET_DEFAULT)
        
        return f"""
            background: {config['background']};
            border: 1px solid {config['border']};
            border-radius: {DesignTokens.RADIUS_2XL}px;
            backdrop-filter: blur({config['blur']}px);
            -webkit-backdrop-filter: blur({config['blur']}px);
        """

    @staticmethod
    def glass_button(variant: str = "primary") -> str:
        """Glass morphism button with variants"""
        if variant == "primary":
            bg = DesignTokens.GLASS_MEDIUM
            border = DesignTokens.BORDER_FOCUS
            hover_bg = DesignTokens.GLASS_LIGHT
        elif variant == "secondary":
            bg = DesignTokens.GLASS_LIGHT
            border = DesignTokens.BORDER_DEFAULT
            hover_bg = DesignTokens.GLASS_MEDIUM
        else:  # ghost
            bg = DesignTokens.GLASS_SUBTLE
            border = DesignTokens.BORDER_SUBTLE
            hover_bg = DesignTokens.GLASS_LOW

        return f"""
            QPushButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: {DesignTokens.TEXT_PRIMARY};
                font-weight: {DesignTokens.WEIGHT_SEMIBOLD};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
                backdrop-filter: blur({DesignTokens.BLUR_SM}px);
                -webkit-backdrop-filter: blur({DesignTokens.BLUR_SM}px);
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border-color: {DesignTokens.BORDER_STRONG};
            }}
            QPushButton:pressed {{
                background: {DesignTokens.GLASS_DARK};
                transform: translateY(1px);
            }}
            QPushButton:disabled {{
                background: {DesignTokens.GLASS_SUBTLE};
                color: {DesignTokens.TEXT_DISABLED};
                border-color: {DesignTokens.BORDER_NEUTRAL_SUBTLE};
            }}
        """

    @staticmethod
    def glass_input() -> str:
        """Glass morphism input field"""
        return f"""
            background: {DesignTokens.GLASS_DARK};
            border: 1px solid {DesignTokens.BORDER_DEFAULT};
            border-radius: {DesignTokens.RADIUS_MD}px;
            padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_BASE}px;
            color: {DesignTokens.TEXT_PRIMARY};
            font-size: {DesignTokens.FONT_BASE}px;
            font-family: {DesignTokens.FONT_FAMILY};
            backdrop-filter: blur({DesignTokens.BLUR_SM}px);
            -webkit-backdrop-filter: blur({DesignTokens.BLUR_SM}px);
        """

    # ============================================
    # ENHANCED COMPONENT STYLES
    # ============================================

    @staticmethod
    def primary_button() -> str:
        """Enhanced primary button with animations"""
        return f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                border: none;
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: white;
                font-weight: {DesignTokens.WEIGHT_SEMIBOLD};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
                min-height: {DesignTokens.BUTTON_HEIGHT_MD}px;
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_primary_hover()};
            }}
            QPushButton:pressed {{
                background: {StyleSheets.gradient_primary_pressed()};
            }}
            QPushButton:disabled {{
                background: {DesignTokens.GLASS_MEDIUM};
                color: {DesignTokens.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def secondary_button() -> str:
        """Enhanced secondary button"""
        return f"""
            QPushButton {{
                background: transparent;
                border: 2px solid {DesignTokens.PRIMARY};
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: {DesignTokens.PRIMARY};
                font-weight: {DesignTokens.WEIGHT_SEMIBOLD};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
                min-height: {DesignTokens.BUTTON_HEIGHT_MD}px;
            }}
            QPushButton:hover {{
                background: {DesignTokens.PRIMARY};
                color: white;
            }}
            QPushButton:pressed {{
                background: {DesignTokens.PRIMARY_DARK};
                border-color: {DesignTokens.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background: transparent;
                border-color: {DesignTokens.TEXT_DISABLED};
                color: {DesignTokens.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def danger_button() -> str:
        """Enhanced danger button"""
        return f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                border: none;
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: white;
                font-weight: {DesignTokens.WEIGHT_SEMIBOLD};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
                min-height: {DesignTokens.BUTTON_HEIGHT_MD}px;
            }}
            QPushButton:hover {{
                background: {StyleSheets.gradient_danger_hover()};
            }}
            QPushButton:disabled {{
                background: {DesignTokens.GLASS_MEDIUM};
                color: {DesignTokens.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def ghost_button() -> str:
        """Ghost button variant"""
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: {DesignTokens.TEXT_SECONDARY};
                font-weight: {DesignTokens.WEIGHT_MEDIUM};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
                min-height: {DesignTokens.BUTTON_HEIGHT_MD}px;
            }}
            QPushButton:hover {{
                background: {DesignTokens.GLASS_LOW};
                color: {DesignTokens.TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background: {DesignTokens.GLASS_MEDIUM};
            }}
            QPushButton:disabled {{
                color: {DesignTokens.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def input_field() -> str:
        """Enhanced input field with focus states"""
        return f"""
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background: {DesignTokens.GLASS_DARK};
                border: 2px solid {DesignTokens.BORDER_DEFAULT};
                border-radius: {DesignTokens.RADIUS_MD}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_BASE}px;
                color: {DesignTokens.TEXT_PRIMARY};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
                min-height: {DesignTokens.INPUT_HEIGHT}px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {DesignTokens.BORDER_FOCUS};
                background: {DesignTokens.GLASS_MEDIUM};
            }}
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
                background: {DesignTokens.GLASS_SUBTLE};
                color: {DesignTokens.TEXT_DISABLED};
                border-color: {DesignTokens.BORDER_NEUTRAL_SUBTLE};
            }}
        """

    @staticmethod
    def modern_card(elevation: str = "default") -> str:
        """Modern card with configurable elevation"""
        shadows = {
            "none": DesignTokens.SHADOW_NONE,
            "sm": DesignTokens.SHADOW_SM,
            "default": DesignTokens.SHADOW_DEFAULT,
            "md": DesignTokens.SHADOW_MD,
            "lg": DesignTokens.SHADOW_LG,
            "xl": DesignTokens.SHADOW_XL
        }
        
        shadow = shadows.get(elevation, DesignTokens.SHADOW_DEFAULT)
        
        return f"""
            background: {StyleSheets.gradient_card()};
            border: 1px solid {DesignTokens.BORDER_DEFAULT};
            border-radius: {DesignTokens.RADIUS_2XL}px;
            padding: {DesignTokens.SPACE_XL}px;
        """

    @staticmethod
    def sidebar_button(active: bool = False) -> str:
        """Enhanced sidebar button with better states"""
        if active:
            bg = StyleSheets.gradient_primary()
            text = "white"
            hover_bg = StyleSheets.gradient_primary_hover()
        else:
            bg = "transparent"
            text = DesignTokens.TEXT_SECONDARY
            hover_bg = DesignTokens.GLASS_LOW
        
        return f"""
            QPushButton {{
                background: {bg};
                color: {text};
                border: none;
                border-radius: {DesignTokens.RADIUS_MD}px;
                padding: {DesignTokens.SPACE_MD}px;
                font-family: {DesignTokens.FONT_FAMILY};
                font-weight: {DesignTokens.WEIGHT_MEDIUM};
                text-align: left;
                min-height: {DesignTokens.NAV_BUTTON_HEIGHT}px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: white;
            }}
        """

    @staticmethod
    def title_bar_button(is_close: bool = False) -> str:
        """Enhanced title bar button"""
        hover_bg = DesignTokens.DANGER if is_close else DesignTokens.GLASS_LOW
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {DesignTokens.RADIUS_SM}px;
                color: {DesignTokens.TEXT_SECONDARY};
                font-family: {DesignTokens.FONT_FAMILY};
                font-size: {DesignTokens.FONT_SM}px;
                font-weight: {DesignTokens.WEIGHT_MEDIUM};
                padding: {DesignTokens.SPACE_SM}px {DesignTokens.SPACE_MD}px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: white;
            }}
        """

    # ============================================
    # UTILITY FUNCTIONS
    # ============================================

    @staticmethod
    def get_semantic_color(variant: str, shade: int = 500) -> str:
        """Get semantic color by variant and shade"""
        color_map = {
            "primary": {
                50: DesignTokens.PRIMARY_50, 100: DesignTokens.PRIMARY_100,
                200: DesignTokens.PRIMARY_200, 300: DesignTokens.PRIMARY_300,
                400: DesignTokens.PRIMARY_400, 500: DesignTokens.PRIMARY_500,
                600: DesignTokens.PRIMARY_600, 700: DesignTokens.PRIMARY_700,
                800: DesignTokens.PRIMARY_800, 900: DesignTokens.PRIMARY_900
            },
            "secondary": {
                50: DesignTokens.SECONDARY_50, 100: DesignTokens.SECONDARY_100,
                200: DesignTokens.SECONDARY_200, 300: DesignTokens.SECONDARY_300,
                400: DesignTokens.SECONDARY_400, 500: DesignTokens.SECONDARY_500,
                600: DesignTokens.SECONDARY_600, 700: DesignTokens.SECONDARY_700,
                800: DesignTokens.SECONDARY_800, 900: DesignTokens.SECONDARY_900
            },
            "success": {
                50: DesignTokens.SUCCESS_50, 100: DesignTokens.SUCCESS_100,
                200: DesignTokens.SUCCESS_200, 300: DesignTokens.SUCCESS_300,
                400: DesignTokens.SUCCESS_400, 500: DesignTokens.SUCCESS_500,
                600: DesignTokens.SUCCESS_600, 700: DesignTokens.SUCCESS_700,
                800: DesignTokens.SUCCESS_800, 900: DesignTokens.SUCCESS_900
            },
            "danger": {
                50: DesignTokens.DANGER_50, 100: DesignTokens.DANGER_100,
                200: DesignTokens.DANGER_200, 300: DesignTokens.DANGER_300,
                400: DesignTokens.DANGER_400, 500: DesignTokens.DANGER_500,
                600: DesignTokens.DANGER_600, 700: DesignTokens.DANGER_700,
                800: DesignTokens.DANGER_800, 900: DesignTokens.DANGER_900
            },
            "warning": {
                50: DesignTokens.WARNING_50, 100: DesignTokens.WARNING_100,
                200: DesignTokens.WARNING_200, 300: DesignTokens.WARNING_300,
                400: DesignTokens.WARNING_400, 500: DesignTokens.WARNING_500,
                600: DesignTokens.WARNING_600, 700: DesignTokens.WARNING_700,
                800: DesignTokens.WARNING_800, 900: DesignTokens.WARNING_900
            },
            "info": {
                50: DesignTokens.INFO_50, 100: DesignTokens.INFO_100,
                200: DesignTokens.INFO_200, 300: DesignTokens.INFO_300,
                400: DesignTokens.INFO_400, 500: DesignTokens.INFO_500,
                600: DesignTokens.INFO_600, 700: DesignTokens.INFO_700,
                800: DesignTokens.INFO_800, 900: DesignTokens.INFO_900
            }
        }
        
        return color_map.get(variant, {}).get(shade, DesignTokens.PRIMARY_500)

    @staticmethod
    def rgba_from_hex(hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba with alpha"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        return hex_color

    @staticmethod
    def create_hover_effect(base_color: str, intensity: float = 0.1) -> str:
        """Create a hover effect by lightening/darkening a color"""
        # This is a simplified version - in a real implementation,
        # you might want to use a color manipulation library
        return base_color  # Placeholder for now


class AnimationUtils:
    """Animation utilities for smooth UI transitions"""

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
        }
        return QEasingCurve(curve_map.get(curve_type, QEasingCurve.Type.OutCubic))

    @staticmethod
    def create_fade_animation(widget, duration: int = 200, fade_in: bool = True):
        """Create fade in/out animation for widgets"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if fade_in:
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
        else:
            animation.setStartValue(1.0)
            animation.setEndValue(0.0)
            
        return animation

    @staticmethod
    def create_slide_animation(widget, duration: int = 300, direction: str = "up"):
        """Create slide animation for widgets"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Implementation would depend on specific widget geometry
        return animation

    @staticmethod
    def create_scale_animation(widget, duration: int = 200, scale_factor: float = 1.05):
        """Create scale animation for hover effects"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        # This would require custom implementation for PyQt6
        # as it doesn't have built-in scale transforms like CSS
        pass


class ColorUtils:
    """Modern color scheme generators and utilities"""

    @staticmethod
    def generate_dark_theme_palette() -> Dict[str, str]:
        """Generate optimized dark theme color palette"""
        return {
            # Background layers
            "bg-app": DesignTokens.BG_DARKEST,
            "bg-surface": DesignTokens.BG_DARK,
            "bg-card": DesignTokens.BG_CARD,
            "bg-elevated": DesignTokens.BG_SURFACE,
            
            # Glass layers
            "glass-subtle": DesignTokens.GLASS_SUBTLE,
            "glass-light": DesignTokens.GLASS_LIGHT,
            "glass-medium": DesignTokens.GLASS_MEDIUM,
            "glass-strong": DesignTokens.GLASS_DARK,
            
            # Text hierarchy
            "text-primary": DesignTokens.TEXT_PRIMARY,
            "text-secondary": DesignTokens.TEXT_SECONDARY,
            "text-tertiary": DesignTokens.TEXT_TERTIARY,
            "text-muted": DesignTokens.TEXT_MUTED,
            
            # Interactive elements
            "interactive-primary": DesignTokens.PRIMARY_500,
            "interactive-secondary": DesignTokens.SECONDARY_500,
            "interactive-hover": DesignTokens.PRIMARY_400,
            "interactive-active": DesignTokens.PRIMARY_600,
            
            # Status colors
            "status-success": DesignTokens.SUCCESS_500,
            "status-warning": DesignTokens.WARNING_500,
            "status-danger": DesignTokens.DANGER_500,
            "status-info": DesignTokens.INFO_500,
        }

    @staticmethod
    def generate_trading_colors() -> Dict[str, str]:
        """Generate colors optimized for trading interfaces"""
        return {
            # P&L Colors
            "profit": DesignTokens.SUCCESS_400,
            "profit-strong": DesignTokens.SUCCESS_500,
            "loss": DesignTokens.DANGER_400,
            "loss-strong": DesignTokens.DANGER_500,
            "neutral": DesignTokens.NEUTRAL_400,
            
            # Signal Colors
            "signal-buy": DesignTokens.SUCCESS_500,
            "signal-sell": DesignTokens.DANGER_500,
            "signal-hold": DesignTokens.WARNING_500,
            "signal-strong": DesignTokens.PRIMARY_500,
            
            # Market Colors
            "market-up": DesignTokens.SUCCESS_400,
            "market-down": DesignTokens.DANGER_400,
            "market-sideways": DesignTokens.NEUTRAL_400,
            
            # Risk Colors
            "risk-low": DesignTokens.SUCCESS_300,
            "risk-medium": DesignTokens.WARNING_400,
            "risk-high": DesignTokens.DANGER_400,
            "risk-critical": DesignTokens.DANGER_600,
        }

    @staticmethod
    def get_contrast_color(background_color: str) -> str:
        """Get appropriate text color for given background"""
        # Simplified implementation - in production, you'd calculate luminance
        dark_backgrounds = [
            DesignTokens.BG_DARKEST, DesignTokens.BG_DARK, DesignTokens.BG_CARD,
            DesignTokens.PRIMARY_700, DesignTokens.PRIMARY_800, DesignTokens.PRIMARY_900,
            DesignTokens.SECONDARY_700, DesignTokens.SECONDARY_800, DesignTokens.SECONDARY_900
        ]
        
        if background_color in dark_backgrounds:
            return DesignTokens.TEXT_PRIMARY
        else:
            return DesignTokens.TEXT_INVERSE

    @staticmethod
    def lighten_color(hex_color: str, amount: float = 0.1) -> str:
        """Lighten a hex color by a given amount (0.0 to 1.0)"""
        # Remove the hash if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Lighten each component
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def darken_color(hex_color: str, amount: float = 0.1) -> str:
        """Darken a hex color by a given amount (0.0 to 1.0)"""
        # Remove the hash if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Darken each component
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def create_color_scale(base_color: str, steps: int = 9) -> Dict[int, str]:
        """Create a color scale from a base color"""
        scale = {}
        
        # Generate lighter shades (50-400)
        for i in range(5):
            shade = (i + 1) * 100 - 50  # 50, 100, 200, 300, 400
            lightness = 0.8 - (i * 0.15)  # Decreasing lightness
            scale[shade] = ColorUtils.lighten_color(base_color, lightness)
        
        # Base color (500)
        scale[500] = base_color
        
        # Generate darker shades (600-900)
        for i in range(4):
            shade = 600 + (i * 100)  # 600, 700, 800, 900
            darkness = 0.2 + (i * 0.15)  # Increasing darkness
            scale[shade] = ColorUtils.darken_color(base_color, darkness)
        
        return scale


class ResponsiveUtils:
    """Utilities for responsive design calculations"""

    @staticmethod
    def get_responsive_font_size(base_size: int, screen_tier: str = None) -> int:
        """Get responsive font size based on screen tier"""
        if screen_tier is None:
            screen_tier = DesignTokens.get_screen_tier()
        
        multipliers = {
            'small': 0.9,
            'medium': 0.95,
            'large': 1.0
        }
        
        return int(base_size * multipliers.get(screen_tier, 1.0))

    @staticmethod
    def get_responsive_spacing(base_spacing: int, screen_tier: str = None) -> int:
        """Get responsive spacing based on screen tier"""
        if screen_tier is None:
            screen_tier = DesignTokens.get_screen_tier()
        
        multipliers = {
            'small': 0.75,
            'medium': 0.9,
            'large': 1.0
        }
        
        return int(base_spacing * multipliers.get(screen_tier, 1.0))

    @staticmethod
    def get_responsive_border_radius(base_radius: int, screen_tier: str = None) -> int:
        """Get responsive border radius based on screen tier"""
        if screen_tier is None:
            screen_tier = DesignTokens.get_screen_tier()
        
        multipliers = {
            'small': 0.8,
            'medium': 0.9,
            'large': 1.0
        }
        
        return int(base_radius * multipliers.get(screen_tier, 1.0))


class AccessibilityUtils:
    """Accessibility utilities for better UX"""

    @staticmethod
    def calculate_contrast_ratio(color1: str, color2: str) -> float:
        """Calculate contrast ratio between two colors (simplified)"""
        # This is a simplified implementation
        # In production, you'd use proper luminance calculations
        return 4.5  # Placeholder - meets WCAG AA standard

    @staticmethod
    def ensure_minimum_contrast(text_color: str, bg_color: str, min_ratio: float = 4.5) -> str:
        """Ensure text color meets minimum contrast ratio"""
        current_ratio = AccessibilityUtils.calculate_contrast_ratio(text_color, bg_color)
        
        if current_ratio >= min_ratio:
            return text_color
        
        # If contrast is insufficient, return high contrast alternative
        if bg_color in [DesignTokens.BG_DARKEST, DesignTokens.BG_DARK]:
            return DesignTokens.TEXT_PRIMARY
        else:
            return DesignTokens.TEXT_INVERSE

    @staticmethod
    def get_focus_ring_style() -> str:
        """Get consistent focus ring styling"""
        return f"""
            outline: 2px solid {DesignTokens.PRIMARY_400};
            outline-offset: 2px;
        """

    @staticmethod
    def get_reduced_motion_styles() -> Dict[str, str]:
        """Get styles for users who prefer reduced motion"""
        return {
            "transition": "none",
            "animation": "none",
            "transform": "none"
        }