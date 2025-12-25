"""
NexusTrade Core Module
"""

from core.config import Config, MT5Config, SupabaseConfig
from core.mt5_client import MT5Client, AccountInfo, Position, Trade
from core.trade_serializer import TradeSerializer
from core.config_manager import ConfigManager, ConfigData, MT5ConfigData, TradingConfigData
from core.errors import (
    ErrorCode,
    ErrorCategory,
    ErrorSeverity,
    ErrorInfo,
    get_error_info,
    get_user_message,
    get_guidance,
    is_critical,
    is_recoverable,
    NexusTradeError,
    MT5ConnectionError,
    TradingError,
    AuthenticationError,
    ModelError,
    ConfigurationError,
)

__all__ = [
    'Config',
    'MT5Config',
    'SupabaseConfig',
    'MT5Client',
    'AccountInfo',
    'Position',
    'Trade',
    'TradeSerializer',
    'ConfigManager',
    'ConfigData',
    'MT5ConfigData',
    'TradingConfigData',
    # Error handling
    'ErrorCode',
    'ErrorCategory',
    'ErrorSeverity',
    'ErrorInfo',
    'get_error_info',
    'get_user_message',
    'get_guidance',
    'is_critical',
    'is_recoverable',
    'NexusTradeError',
    'MT5ConnectionError',
    'TradingError',
    'AuthenticationError',
    'ModelError',
    'ConfigurationError',
]
