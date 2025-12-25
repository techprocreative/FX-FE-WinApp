"""
Property-based tests for Model Metadata Display.

**Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**

Tests that for any model in storage, the Models page displays all required
metadata fields: name, symbol, accuracy, and created date.

Validates: Requirements 4.1
"""
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from datetime import datetime
import pytest


def extract_model_display_fields(model_info: dict) -> dict:
    """
    Extract the fields that would be displayed in a ModelCard.
    
    This function mirrors the display logic in ModelCard to provide
    a testable, pure function for property testing.
    
    Args:
        model_info: Dict with model metadata
        
    Returns:
        Dict with the extracted display fields
    """
    # Extract name (required)
    name = model_info.get('name', 'Unknown')
    
    # Extract symbol (required)
    symbol = model_info.get('symbol', 'Unknown').upper()
    
    # Extract accuracy (required, normalize to percentage)
    accuracy = model_info.get('accuracy', 0.0)
    accuracy_pct = accuracy * 100 if accuracy <= 1.0 else accuracy
    
    # Extract created_at (required)
    created_at = model_info.get('created_at', 'Unknown')
    
    # Format created_at if it's a valid ISO string
    if isinstance(created_at, str) and created_at != 'Unknown':
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_at = dt.strftime('%Y-%m-%d %H:%M')
        except:
            pass
    
    return {
        'name': name,
        'symbol': symbol,
        'accuracy_pct': accuracy_pct,
        'created_at': created_at
    }


def validate_model_metadata_completeness(model_info: dict) -> tuple[bool, list[str]]:
    """
    Validate that all required metadata fields are present and displayable.
    
    Args:
        model_info: Dict with model metadata
        
    Returns:
        Tuple of (is_valid, list of missing/invalid fields)
    """
    missing_fields = []
    
    # Check name
    name = model_info.get('name')
    if not name or name == 'Unknown':
        missing_fields.append('name')
    
    # Check symbol
    symbol = model_info.get('symbol')
    if not symbol or symbol.upper() == 'UNKNOWN':
        missing_fields.append('symbol')
    
    # Check accuracy (must be a number)
    accuracy = model_info.get('accuracy')
    if accuracy is None or not isinstance(accuracy, (int, float)):
        missing_fields.append('accuracy')
    
    # Check created_at
    created_at = model_info.get('created_at')
    if not created_at or created_at == 'Unknown':
        missing_fields.append('created_at')
    
    return (len(missing_fields) == 0, missing_fields)


# Strategies for generating valid model metadata
@st.composite
def valid_model_info(draw):
    """Generate valid model metadata dictionaries."""
    model_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='-_'
    )))
    
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
        whitelist_characters='-_'
    )).filter(lambda x: x.strip()))
    
    symbol = draw(st.sampled_from(['BTCUSD', 'EURUSD', 'XAUUSD', 'GBPUSD', 'USDJPY']))
    
    # Accuracy between 0 and 1 (or 0-100)
    accuracy = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    
    # Generate valid ISO datetime string
    year = draw(st.integers(min_value=2020, max_value=2025))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    created_at = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"
    
    file_size = draw(st.integers(min_value=1000, max_value=10000000))
    
    return {
        'model_id': model_id,
        'name': name,
        'symbol': symbol,
        'accuracy': accuracy,
        'created_at': created_at,
        'file_size': file_size,
        'is_active': draw(st.booleans())
    }


class TestModelMetadataDisplay:
    """
    Property tests for model metadata display.
    
    **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
    **Validates: Requirements 4.1**
    """

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_all_required_fields_are_extractable(self, model_info: dict):
        """
        Property: For any valid model, all required metadata fields SHALL be extractable.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        display_fields = extract_model_display_fields(model_info)
        
        # All required fields must be present
        assert 'name' in display_fields, "name field must be extractable"
        assert 'symbol' in display_fields, "symbol field must be extractable"
        assert 'accuracy_pct' in display_fields, "accuracy field must be extractable"
        assert 'created_at' in display_fields, "created_at field must be extractable"

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_name_is_preserved(self, model_info: dict):
        """
        Property: For any model, the displayed name SHALL match the original name.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        display_fields = extract_model_display_fields(model_info)
        assert display_fields['name'] == model_info['name'], \
            f"Name should be preserved: expected '{model_info['name']}', got '{display_fields['name']}'"

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_symbol_is_uppercase(self, model_info: dict):
        """
        Property: For any model, the displayed symbol SHALL be uppercase.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        display_fields = extract_model_display_fields(model_info)
        assert display_fields['symbol'] == display_fields['symbol'].upper(), \
            f"Symbol should be uppercase: got '{display_fields['symbol']}'"

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_accuracy_is_percentage(self, model_info: dict):
        """
        Property: For any model with accuracy 0-1, the displayed accuracy SHALL be 0-100%.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        display_fields = extract_model_display_fields(model_info)
        accuracy_pct = display_fields['accuracy_pct']
        
        # Accuracy should be in percentage form (0-100)
        assert 0 <= accuracy_pct <= 100, \
            f"Accuracy percentage should be 0-100: got {accuracy_pct}"

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_created_date_is_formatted(self, model_info: dict):
        """
        Property: For any model with valid ISO date, the created_at SHALL be formatted.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        display_fields = extract_model_display_fields(model_info)
        created_at = display_fields['created_at']
        
        # Should be formatted as 'YYYY-MM-DD HH:MM'
        assert created_at != 'Unknown', "Created date should be formatted"
        # Check format pattern
        parts = created_at.split(' ')
        assert len(parts) == 2, f"Created date should have date and time parts: got '{created_at}'"

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_valid_model_passes_completeness_check(self, model_info: dict):
        """
        Property: For any valid model, the completeness validation SHALL pass.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        is_valid, missing = validate_model_metadata_completeness(model_info)
        assert is_valid, f"Valid model should pass completeness check, missing: {missing}"

    @given(st.sampled_from(['name', 'symbol', 'accuracy', 'created_at']))
    @settings(max_examples=100)
    def test_missing_field_fails_completeness(self, missing_field: str):
        """
        Property: For any model missing a required field, completeness validation SHALL fail.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        # Create a model with one missing field
        model_info = {
            'model_id': 'test-model',
            'name': 'Test Model',
            'symbol': 'BTCUSD',
            'accuracy': 0.85,
            'created_at': '2024-01-15T10:30:00'
        }
        
        # Remove the field
        del model_info[missing_field]
        
        is_valid, missing = validate_model_metadata_completeness(model_info)
        assert not is_valid, f"Model missing '{missing_field}' should fail completeness check"
        assert missing_field in missing, f"Missing field '{missing_field}' should be reported"

    @given(valid_model_info())
    @settings(max_examples=100)
    def test_extraction_is_deterministic(self, model_info: dict):
        """
        Property: For any model, extracting display fields multiple times SHALL return same result.
        
        **Feature: mvp-live-trading-connector, Property 10: Model Metadata Display**
        **Validates: Requirements 4.1**
        """
        result1 = extract_model_display_fields(model_info)
        result2 = extract_model_display_fields(model_info)
        result3 = extract_model_display_fields(model_info)
        
        assert result1 == result2 == result3, \
            f"Extraction should be deterministic: got {result1}, {result2}, {result3}"
