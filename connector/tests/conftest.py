"""
Pytest configuration and shared fixtures for NexusTrade Connector tests.

Configures Hypothesis with minimum 100 iterations per property test
as specified in the design document.
"""
import pytest
from hypothesis import settings, Verbosity

# Configure Hypothesis default settings
# Minimum 100 examples per property test as per Testing Strategy
settings.register_profile(
    "default",
    max_examples=100,
    verbosity=Verbosity.normal,
    deadline=None,  # Disable deadline for complex tests
)

settings.register_profile(
    "ci",
    max_examples=100,
    verbosity=Verbosity.normal,
    deadline=None,
)

settings.register_profile(
    "debug",
    max_examples=10,
    verbosity=Verbosity.verbose,
    deadline=None,
)

# Load default profile
settings.load_profile("default")


@pytest.fixture
def sample_account_info():
    """Sample account info for testing."""
    return {
        "login": 12345678,
        "server": "Demo-Server",
        "balance": 10000.0,
        "equity": 10500.0,
        "margin": 500.0,
        "margin_free": 10000.0,
        "profit": 500.0,
        "leverage": 100,
        "currency": "USD",
    }


@pytest.fixture
def sample_trading_config():
    """Sample trading configuration for testing."""
    return {
        "symbol": "BTCUSD",
        "timeframe": "M15",
        "volume": 0.01,
        "risk_percent": 1.0,
        "max_positions": 1,
        "confidence_threshold": 0.6,
        "sl_pips": 50.0,
        "tp_pips": 100.0,
        "magic_number": 88888,
    }


@pytest.fixture
def sample_trade():
    """Sample trade data for testing."""
    from datetime import datetime
    return {
        "ticket": 123456789,
        "symbol": "BTCUSD",
        "type": "buy",
        "volume": 0.01,
        "open_price": 42000.50,
        "close_price": 42150.75,
        "open_time": datetime(2025, 1, 15, 10, 30, 0),
        "close_time": datetime(2025, 1, 15, 11, 45, 0),
        "profit": 150.25,
        "commission": -0.50,
        "swap": -0.10,
        "magic": 88888,
        "comment": "NexusTrade Auto",
    }
