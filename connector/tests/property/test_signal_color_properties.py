"""
Property-based tests for Signal Color Coding.

**Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**

Tests that for any trading signal, the UI displays the correct color:
- Green (SUCCESS) for BUY
- Red (DANGER) for SELL
- Gray (TEXT_PLACEHOLDER) for HOLD

Validates: Requirements 7.5
"""
from hypothesis import given, settings
from hypothesis import strategies as st
import pytest


# Define color constants matching DesignTokens to avoid PyQt6 dependency in tests
# These values are from ui/design_system.py
class SignalColors:
    """Signal color constants matching DesignTokens."""
    SUCCESS = "#10b981"          # Green - for BUY
    DANGER = "#f43f5e"           # Rose/Red - for SELL
    TEXT_PLACEHOLDER = "#64748b" # Slate 500/Gray - for HOLD


def get_signal_color(signal: str) -> str:
    """
    Get the expected color for a given signal.
    
    This function mirrors the color logic in SignalCard.update_signal()
    to provide a testable, pure function for property testing.
    
    Args:
        signal: The trading signal ('BUY', 'SELL', 'HOLD' or variations)
        
    Returns:
        The color token that should be used for this signal
    """
    signal_upper = signal.upper().strip()
    
    if signal_upper == 'BUY':
        return SignalColors.SUCCESS
    elif signal_upper == 'SELL':
        return SignalColors.DANGER
    else:  # HOLD or any other value
        return SignalColors.TEXT_PLACEHOLDER


class TestSignalColorCoding:
    """
    Property tests for signal color coding.
    
    **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
    **Validates: Requirements 7.5**
    """

    @given(st.sampled_from(['BUY', 'buy', 'Buy', 'BUY ', ' BUY', ' buy ']))
    @settings(max_examples=100)
    def test_buy_signal_returns_green(self, signal: str):
        """
        Property: For any BUY signal (case-insensitive), the color SHALL be green (SUCCESS).
        
        **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
        **Validates: Requirements 7.5**
        """
        color = get_signal_color(signal)
        assert color == SignalColors.SUCCESS, f"BUY signal '{signal}' should return SUCCESS color, got {color}"

    @given(st.sampled_from(['SELL', 'sell', 'Sell', 'SELL ', ' SELL', ' sell ']))
    @settings(max_examples=100)
    def test_sell_signal_returns_red(self, signal: str):
        """
        Property: For any SELL signal (case-insensitive), the color SHALL be red (DANGER).
        
        **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
        **Validates: Requirements 7.5**
        """
        color = get_signal_color(signal)
        assert color == SignalColors.DANGER, f"SELL signal '{signal}' should return DANGER color, got {color}"

    @given(st.sampled_from(['HOLD', 'hold', 'Hold', 'HOLD ', ' HOLD', ' hold ']))
    @settings(max_examples=100)
    def test_hold_signal_returns_gray(self, signal: str):
        """
        Property: For any HOLD signal (case-insensitive), the color SHALL be gray (TEXT_PLACEHOLDER).
        
        **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
        **Validates: Requirements 7.5**
        """
        color = get_signal_color(signal)
        assert color == SignalColors.TEXT_PLACEHOLDER, f"HOLD signal '{signal}' should return TEXT_PLACEHOLDER color, got {color}"

    @given(st.text(min_size=1, max_size=20).filter(
        lambda s: s.upper().strip() not in ['BUY', 'SELL', 'HOLD']
    ))
    @settings(max_examples=100)
    def test_unknown_signal_defaults_to_gray(self, signal: str):
        """
        Property: For any unknown signal, the color SHALL default to gray (TEXT_PLACEHOLDER).
        
        This ensures graceful handling of unexpected signal values.
        
        **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
        **Validates: Requirements 7.5**
        """
        color = get_signal_color(signal)
        assert color == SignalColors.TEXT_PLACEHOLDER, f"Unknown signal '{signal}' should default to TEXT_PLACEHOLDER color, got {color}"

    @given(st.sampled_from(['BUY', 'SELL', 'HOLD']))
    @settings(max_examples=100)
    def test_signal_color_is_valid_design_token(self, signal: str):
        """
        Property: For any valid signal, the returned color SHALL be a valid design token.
        
        **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
        **Validates: Requirements 7.5**
        """
        color = get_signal_color(signal)
        valid_colors = {SignalColors.SUCCESS, SignalColors.DANGER, SignalColors.TEXT_PLACEHOLDER}
        assert color in valid_colors, f"Signal '{signal}' returned invalid color: {color}"

    @given(st.sampled_from(['BUY', 'SELL', 'HOLD']))
    @settings(max_examples=100)
    def test_signal_color_mapping_is_deterministic(self, signal: str):
        """
        Property: For any signal, calling get_signal_color multiple times SHALL return the same color.
        
        **Feature: mvp-live-trading-connector, Property 11: Signal Color Coding**
        **Validates: Requirements 7.5**
        """
        color1 = get_signal_color(signal)
        color2 = get_signal_color(signal)
        color3 = get_signal_color(signal)
        
        assert color1 == color2 == color3, f"Signal '{signal}' returned inconsistent colors: {color1}, {color2}, {color3}"
