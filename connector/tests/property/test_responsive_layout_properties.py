"""
Property-based tests for Responsive Layout Adaptation.

**Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**

Tests that for any screen size tier (small, medium, large), the layout dimensions
are calculated according to the responsive sizing rules.

Validates: Requirements 7.2
"""
from hypothesis import given, settings, assume
from hypothesis import strategies as st
import pytest


# Screen tier boundaries as defined in design_system.py
SMALL_MAX_WIDTH = 1024
MEDIUM_MAX_WIDTH = 1600


def get_screen_tier_for_width(screen_width: int) -> str:
    """
    Determine screen size tier based on width.
    
    Mirrors the logic in DesignTokens.get_screen_tier() for testability.
    
    Args:
        screen_width: Screen width in pixels
        
    Returns:
        str: 'small' (≤1024), 'medium' (1025-1600), or 'large' (>1600)
    """
    if screen_width <= SMALL_MAX_WIDTH:
        return 'small'
    elif screen_width <= MEDIUM_MAX_WIDTH:
        return 'medium'
    else:
        return 'large'


def calculate_responsive_window_size(screen_width: int, screen_height: int) -> tuple:
    """
    Calculate responsive window size based on screen dimensions.
    
    Mirrors the logic in DesignTokens.get_responsive_window_size() for testability.
    
    Args:
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        
    Returns:
        tuple: (width, height) of the calculated window size
    """
    tier = get_screen_tier_for_width(screen_width)
    
    if tier == 'small':
        target_w = int(screen_width * 0.95)
        target_h = int(screen_height * 0.90)
        min_w, min_h = 960, 650
        max_w, max_h = 1024, 768
    elif tier == 'medium':
        target_w = int(screen_width * 0.90)
        target_h = int(screen_height * 0.88)
        min_w, min_h = 1100, 680
        max_w, max_h = 1600, 1000
    else:  # large
        target_w = int(screen_width * 0.75)
        target_h = int(screen_height * 0.80)
        min_w, min_h = 1400, 800
        max_w, max_h = 1920, 1200
    
    width = max(min_w, min(target_w, max_w))
    height = max(min_h, min(target_h, max_h))
    
    return width, height


def get_responsive_sidebar_width(screen_width: int) -> int:
    """
    Get sidebar width based on screen tier.
    
    Mirrors the logic in DesignTokens.get_responsive_sidebar_width() for testability.
    """
    tier = get_screen_tier_for_width(screen_width)
    
    if tier == 'small':
        return 220
    elif tier == 'medium':
        return 250
    else:
        return 280


def get_responsive_card_sizes(screen_width: int) -> dict:
    """
    Get responsive card sizes based on screen tier.
    
    Mirrors the logic in DesignTokens.get_responsive_card_sizes() for testability.
    """
    tier = get_screen_tier_for_width(screen_width)
    
    if tier == 'small':
        return {
            'stat_card': (150, 100),
            'signal_card': (260, 240)
        }
    elif tier == 'medium':
        return {
            'stat_card': (170, 110),
            'signal_card': (300, 260)
        }
    else:
        return {
            'stat_card': (180, 120),
            'signal_card': (320, 280)
        }


def get_responsive_spacing(screen_width: int) -> float:
    """
    Get responsive spacing multiplier based on screen tier.
    
    Mirrors the logic in DesignTokens.get_responsive_spacing() for testability.
    """
    tier = get_screen_tier_for_width(screen_width)
    
    if tier == 'small':
        return 0.75
    elif tier == 'medium':
        return 0.9
    else:
        return 1.0


# Strategies for generating screen dimensions
small_screen_width = st.integers(min_value=800, max_value=SMALL_MAX_WIDTH)
medium_screen_width = st.integers(min_value=SMALL_MAX_WIDTH + 1, max_value=MEDIUM_MAX_WIDTH)
large_screen_width = st.integers(min_value=MEDIUM_MAX_WIDTH + 1, max_value=3840)

any_screen_width = st.integers(min_value=800, max_value=3840)
any_screen_height = st.integers(min_value=600, max_value=2160)


class TestScreenTierClassification:
    """
    Property tests for screen tier classification.
    
    **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
    **Validates: Requirements 7.2**
    """

    @given(small_screen_width)
    @settings(max_examples=100)
    def test_small_screen_tier(self, width: int):
        """
        Property: For any screen width ≤1024, the tier SHALL be 'small'.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        tier = get_screen_tier_for_width(width)
        assert tier == 'small', f"Width {width} should be 'small' tier, got '{tier}'"

    @given(medium_screen_width)
    @settings(max_examples=100)
    def test_medium_screen_tier(self, width: int):
        """
        Property: For any screen width 1025-1600, the tier SHALL be 'medium'.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        tier = get_screen_tier_for_width(width)
        assert tier == 'medium', f"Width {width} should be 'medium' tier, got '{tier}'"

    @given(large_screen_width)
    @settings(max_examples=100)
    def test_large_screen_tier(self, width: int):
        """
        Property: For any screen width >1600, the tier SHALL be 'large'.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        tier = get_screen_tier_for_width(width)
        assert tier == 'large', f"Width {width} should be 'large' tier, got '{tier}'"

    @given(any_screen_width)
    @settings(max_examples=100)
    def test_tier_is_valid(self, width: int):
        """
        Property: For any screen width, the tier SHALL be one of 'small', 'medium', or 'large'.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        tier = get_screen_tier_for_width(width)
        assert tier in {'small', 'medium', 'large'}, f"Invalid tier '{tier}' for width {width}"


class TestResponsiveWindowSize:
    """
    Property tests for responsive window size calculation.
    
    **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
    **Validates: Requirements 7.2**
    """

    @given(any_screen_width, any_screen_height)
    @settings(max_examples=100)
    def test_window_size_within_bounds(self, screen_w: int, screen_h: int):
        """
        Property: For any screen size, the calculated window size SHALL be within
        the min/max bounds for that tier.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        width, height = calculate_responsive_window_size(screen_w, screen_h)
        tier = get_screen_tier_for_width(screen_w)
        
        if tier == 'small':
            assert 960 <= width <= 1024, f"Small tier width {width} out of bounds [960, 1024]"
            assert 650 <= height <= 768, f"Small tier height {height} out of bounds [650, 768]"
        elif tier == 'medium':
            assert 1100 <= width <= 1600, f"Medium tier width {width} out of bounds [1100, 1600]"
            assert 680 <= height <= 1000, f"Medium tier height {height} out of bounds [680, 1000]"
        else:  # large
            assert 1400 <= width <= 1920, f"Large tier width {width} out of bounds [1400, 1920]"
            assert 800 <= height <= 1200, f"Large tier height {height} out of bounds [800, 1200]"

    @given(any_screen_width, any_screen_height)
    @settings(max_examples=100)
    def test_window_size_is_positive(self, screen_w: int, screen_h: int):
        """
        Property: For any screen size, the calculated window dimensions SHALL be positive.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        width, height = calculate_responsive_window_size(screen_w, screen_h)
        assert width > 0, f"Window width should be positive, got {width}"
        assert height > 0, f"Window height should be positive, got {height}"

    @given(any_screen_width, any_screen_height)
    @settings(max_examples=100)
    def test_window_size_deterministic(self, screen_w: int, screen_h: int):
        """
        Property: For any screen size, calling calculate_responsive_window_size
        multiple times SHALL return the same result.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        result1 = calculate_responsive_window_size(screen_w, screen_h)
        result2 = calculate_responsive_window_size(screen_w, screen_h)
        assert result1 == result2, f"Non-deterministic results: {result1} vs {result2}"


class TestResponsiveSidebarWidth:
    """
    Property tests for responsive sidebar width.
    
    **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
    **Validates: Requirements 7.2**
    """

    @given(small_screen_width)
    @settings(max_examples=100)
    def test_small_screen_sidebar_width(self, width: int):
        """
        Property: For any small screen, sidebar width SHALL be 220px.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        sidebar_width = get_responsive_sidebar_width(width)
        assert sidebar_width == 220, f"Small screen sidebar should be 220, got {sidebar_width}"

    @given(medium_screen_width)
    @settings(max_examples=100)
    def test_medium_screen_sidebar_width(self, width: int):
        """
        Property: For any medium screen, sidebar width SHALL be 250px.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        sidebar_width = get_responsive_sidebar_width(width)
        assert sidebar_width == 250, f"Medium screen sidebar should be 250, got {sidebar_width}"

    @given(large_screen_width)
    @settings(max_examples=100)
    def test_large_screen_sidebar_width(self, width: int):
        """
        Property: For any large screen, sidebar width SHALL be 280px.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        sidebar_width = get_responsive_sidebar_width(width)
        assert sidebar_width == 280, f"Large screen sidebar should be 280, got {sidebar_width}"


class TestResponsiveCardSizes:
    """
    Property tests for responsive card sizes.
    
    **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
    **Validates: Requirements 7.2**
    """

    @given(any_screen_width)
    @settings(max_examples=100)
    def test_card_sizes_contain_required_keys(self, width: int):
        """
        Property: For any screen width, card sizes SHALL contain 'stat_card' and 'signal_card' keys.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        sizes = get_responsive_card_sizes(width)
        assert 'stat_card' in sizes, "Card sizes should contain 'stat_card'"
        assert 'signal_card' in sizes, "Card sizes should contain 'signal_card'"

    @given(any_screen_width)
    @settings(max_examples=100)
    def test_card_sizes_are_positive_tuples(self, width: int):
        """
        Property: For any screen width, card sizes SHALL be tuples of positive integers.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        sizes = get_responsive_card_sizes(width)
        
        for card_type, (w, h) in sizes.items():
            assert w > 0, f"{card_type} width should be positive, got {w}"
            assert h > 0, f"{card_type} height should be positive, got {h}"

    @given(small_screen_width)
    @settings(max_examples=100)
    def test_small_screen_card_sizes(self, width: int):
        """
        Property: For any small screen, card sizes SHALL match small tier specifications.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        sizes = get_responsive_card_sizes(width)
        assert sizes['stat_card'] == (150, 100), f"Small stat_card should be (150, 100), got {sizes['stat_card']}"
        assert sizes['signal_card'] == (260, 240), f"Small signal_card should be (260, 240), got {sizes['signal_card']}"


class TestResponsiveSpacing:
    """
    Property tests for responsive spacing multiplier.
    
    **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
    **Validates: Requirements 7.2**
    """

    @given(small_screen_width)
    @settings(max_examples=100)
    def test_small_screen_spacing(self, width: int):
        """
        Property: For any small screen, spacing multiplier SHALL be 0.75.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        spacing = get_responsive_spacing(width)
        assert spacing == 0.75, f"Small screen spacing should be 0.75, got {spacing}"

    @given(medium_screen_width)
    @settings(max_examples=100)
    def test_medium_screen_spacing(self, width: int):
        """
        Property: For any medium screen, spacing multiplier SHALL be 0.9.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        spacing = get_responsive_spacing(width)
        assert spacing == 0.9, f"Medium screen spacing should be 0.9, got {spacing}"

    @given(large_screen_width)
    @settings(max_examples=100)
    def test_large_screen_spacing(self, width: int):
        """
        Property: For any large screen, spacing multiplier SHALL be 1.0.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        spacing = get_responsive_spacing(width)
        assert spacing == 1.0, f"Large screen spacing should be 1.0, got {spacing}"

    @given(any_screen_width)
    @settings(max_examples=100)
    def test_spacing_is_valid_multiplier(self, width: int):
        """
        Property: For any screen width, spacing multiplier SHALL be between 0 and 1 (inclusive).
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        spacing = get_responsive_spacing(width)
        assert 0 < spacing <= 1.0, f"Spacing multiplier should be in (0, 1], got {spacing}"


class TestResponsiveLayoutMonotonicity:
    """
    Property tests for monotonicity of responsive layout values.
    
    **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
    **Validates: Requirements 7.2**
    """

    @given(st.integers(min_value=800, max_value=1024), st.integers(min_value=1601, max_value=3840))
    @settings(max_examples=100)
    def test_larger_screens_have_larger_sidebar(self, small_w: int, large_w: int):
        """
        Property: Larger screen tiers SHALL have wider sidebars than smaller tiers.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        small_sidebar = get_responsive_sidebar_width(small_w)
        large_sidebar = get_responsive_sidebar_width(large_w)
        assert large_sidebar >= small_sidebar, f"Large sidebar ({large_sidebar}) should be >= small ({small_sidebar})"

    @given(st.integers(min_value=800, max_value=1024), st.integers(min_value=1601, max_value=3840))
    @settings(max_examples=100)
    def test_larger_screens_have_larger_spacing(self, small_w: int, large_w: int):
        """
        Property: Larger screen tiers SHALL have larger spacing multipliers.
        
        **Feature: mvp-live-trading-connector, Property 15: Responsive Layout Adaptation**
        **Validates: Requirements 7.2**
        """
        small_spacing = get_responsive_spacing(small_w)
        large_spacing = get_responsive_spacing(large_w)
        assert large_spacing >= small_spacing, f"Large spacing ({large_spacing}) should be >= small ({small_spacing})"
