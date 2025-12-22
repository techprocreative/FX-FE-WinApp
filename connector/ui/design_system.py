"""
NexusTrade Design System
Centralized design tokens for consistent UI across all windows
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen


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
    # COLOR PALETTE
    # ============================================

    # Primary Colors
    PRIMARY = "#06b6d4"          # Cyan
    PRIMARY_DARK = "#0891b2"
    PRIMARY_DARKER = "#0e7490"
    PRIMARY_LIGHT = "#22d3ee"
    PRIMARY_HOVER = "#0ea5e9"       # Hover state for primary

    SECONDARY = "#14b8a6"        # Teal
    SECONDARY_DARK = "#0d9488"
    SECONDARY_DARKER = "#0f766e"

    # Semantic Colors
    SUCCESS = "#10b981"          # Green
    SUCCESS_DARK = "#059669"

    DANGER = "#f43f5e"           # Rose
    DANGER_DARK = "#e11d48"
    DANGER_DARKER = "#be123c"

    WARNING = "#fbbf24"          # Amber
    INFO = "#3b82f6"             # Blue

    # Neutral Backgrounds
    BG_DARKEST = "#0f172a"       # Slate 950
    BG_DARK = "#1e293b"          # Slate 900
    BG_MEDIUM = "#1e3a8a"        # Blue 900 (for gradients)
    BG_CARD = "#334155"          # Slate 700
    
    # Aliases for backward compatibility
    BACKGROUND_DARK = "#0f172a"  # Same as BG_DARKEST

    # Glass/Transparent Backgrounds
    GLASS_DARKEST = "rgba(15, 23, 42, 0.95)"
    GLASS_DARK = "rgba(15, 23, 42, 0.8)"
    GLASS_MEDIUM = "rgba(30, 41, 59, 0.6)"
    GLASS_LIGHT = "rgba(51, 65, 85, 0.4)"
    GLASS_LOW = "rgba(51, 65, 85, 0.2)"    # Very subtle glass

    # Text Colors
    TEXT_PRIMARY = "#f8fafc"     # Slate 50
    TEXT_SECONDARY = "#e2e8f0"   # Slate 200
    TEXT_MUTED = "#cbd5e1"       # Slate 300
    TEXT_DISABLED = "#94a3b8"    # Slate 400
    TEXT_PLACEHOLDER = "#64748b" # Slate 500

    # Border Colors
    BORDER_SUBTLE = "rgba(6, 182, 212, 0.1)"
    BORDER_DEFAULT = "rgba(6, 182, 212, 0.2)"
    BORDER_MEDIUM = "rgba(6, 182, 212, 0.3)"
    BORDER_FOCUS = "rgba(6, 182, 212, 0.5)"
    BORDER_STRONG = "#06b6d4"

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
    # TYPOGRAPHY
    # ============================================

    FONT_FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, system-ui, sans-serif"

    # Font Sizes
    FONT_XS = 11
    FONT_SM = 12
    FONT_BASE = 14
    FONT_LG = 16
    FONT_XL = 18
    FONT_2XL = 20
    FONT_3XL = 24
    FONT_4XL = 28
    FONT_5XL = 32

    # Font Weights
    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    WEIGHT_BLACK = 900

    # ============================================
    # BORDER RADIUS
    # ============================================

    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 10
    RADIUS_XL = 12
    RADIUS_2XL = 16
    RADIUS_FULL = 9999

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
    # SHADOWS & EFFECTS
    # ============================================

    SHADOW_SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    SHADOW_MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    SHADOW_LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
    SHADOW_XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1)"

    # Glow effects
    GLOW_PRIMARY = "0 0 20px rgba(6, 182, 212, 0.4)"
    GLOW_SUCCESS = "0 0 20px rgba(16, 185, 129, 0.4)"
    GLOW_DANGER = "0 0 20px rgba(244, 63, 94, 0.4)"


class StyleSheets:
    """Pre-built stylesheet generators"""

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
    def primary_button() -> str:
        """Primary button stylesheet"""
        return f"""
            QPushButton {{
                background: {StyleSheets.gradient_primary()};
                border: none;
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: white;
                font-weight: {DesignTokens.WEIGHT_BOLD};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
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
    def danger_button() -> str:
        """Danger button stylesheet"""
        return f"""
            QPushButton {{
                background: {StyleSheets.gradient_danger()};
                border: none;
                border-radius: {DesignTokens.RADIUS_LG}px;
                padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_XL}px;
                color: white;
                font-weight: {DesignTokens.WEIGHT_BOLD};
                font-size: {DesignTokens.FONT_BASE}px;
                font-family: {DesignTokens.FONT_FAMILY};
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
    def input_field() -> str:
        """Input field stylesheet (LineEdit, SpinBox, ComboBox)"""
        return f"""
            background: {DesignTokens.GLASS_DARK};
            border: 1px solid {DesignTokens.BORDER_MEDIUM};
            border-radius: {DesignTokens.RADIUS_MD}px;
            padding: {DesignTokens.SPACE_MD}px {DesignTokens.SPACE_BASE}px;
            color: {DesignTokens.TEXT_PRIMARY};
            font-size: {DesignTokens.FONT_BASE}px;
            font-family: {DesignTokens.FONT_FAMILY};
        """

    @staticmethod
    def glass_card() -> str:
        """Glass morphism card stylesheet"""
        return f"""
            background: {DesignTokens.GLASS_MEDIUM};
            border: 1px solid {DesignTokens.BORDER_DEFAULT};
            border-radius: {DesignTokens.RADIUS_2XL}px;
            padding: {DesignTokens.SPACE_XL}px;
        """

    @staticmethod
    def sidebar_button(active: bool = False) -> str:
        bg = DesignTokens.PRIMARY if active else "transparent"
        text = "white" if active else DesignTokens.TEXT_SECONDARY
        hover_bg = DesignTokens.PRIMARY_HOVER if active else DesignTokens.GLASS_LOW
        
        return f"""
            QPushButton {{
                background: {bg};
                color: {text};
                border: none;
                border-radius: {DesignTokens.RADIUS_MD}px;
                padding: {DesignTokens.SPACE_MD}px;
                font-family: {DesignTokens.FONT_FAMILY};
                font-weight: {DesignTokens.WEIGHT_BOLD};
                text-align: left;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: white;
            }}
        """

    @staticmethod
    def title_bar_button(is_close: bool = False) -> str:
        hover_bg = DesignTokens.DANGER if is_close else DesignTokens.GLASS_LOW
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 0px;
                color: {DesignTokens.TEXT_SECONDARY};
                font-family: {DesignTokens.FONT_FAMILY};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                color: white;
            }}
        """
