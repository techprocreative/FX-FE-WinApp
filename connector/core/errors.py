"""
NexusTrade Error Handling Module
Provides user-friendly error messages and error classification for common errors.

Requirements: 8.1, 8.3
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class ErrorCategory(Enum):
    """Categories of errors for classification and handling"""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    TRADING = "trading"
    MODEL = "model"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Warning, operation may continue
    ERROR = "error"         # Error, operation failed but app continues
    CRITICAL = "critical"   # Critical, requires user action or app restart


@dataclass
class ErrorInfo:
    """Structured error information"""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    guidance: str
    recoverable: bool = True


class ErrorCode:
    """Error code constants"""
    # MT5 Connection Errors (1xxx)
    MT5_NOT_INSTALLED = "MT5_1001"
    MT5_INIT_FAILED = "MT5_1002"
    MT5_INVALID_CREDENTIALS = "MT5_1003"
    MT5_SERVER_UNREACHABLE = "MT5_1004"
    MT5_CONNECTION_TIMEOUT = "MT5_1005"
    MT5_CONNECTION_LOST = "MT5_1006"
    MT5_RECONNECT_FAILED = "MT5_1007"
    
    # Trading Errors (2xxx)
    TRADE_INSUFFICIENT_MARGIN = "TRADE_2001"
    TRADE_ORDER_REJECTED = "TRADE_2002"
    TRADE_SYMBOL_NOT_FOUND = "TRADE_2003"
    TRADE_INVALID_VOLUME = "TRADE_2004"
    TRADE_MARKET_CLOSED = "TRADE_2005"
    TRADE_POSITION_NOT_FOUND = "TRADE_2006"
    TRADE_MAX_POSITIONS = "TRADE_2007"
    
    # Authentication Errors (3xxx)
    AUTH_INVALID_CREDENTIALS = "AUTH_3001"
    AUTH_EMAIL_NOT_CONFIRMED = "AUTH_3002"
    AUTH_SESSION_EXPIRED = "AUTH_3003"
    AUTH_NETWORK_ERROR = "AUTH_3004"
    AUTH_UNKNOWN = "AUTH_3005"
    
    # Model Errors (4xxx)
    MODEL_NOT_FOUND = "MODEL_4001"
    MODEL_DECRYPTION_FAILED = "MODEL_4002"
    MODEL_LOAD_FAILED = "MODEL_4003"
    MODEL_PREDICTION_FAILED = "MODEL_4004"
    MODEL_SYNC_FAILED = "MODEL_4005"
    
    # Configuration Errors (5xxx)
    CONFIG_LOAD_FAILED = "CONFIG_5001"
    CONFIG_SAVE_FAILED = "CONFIG_5002"
    CONFIG_INVALID = "CONFIG_5003"
    
    # System Errors (9xxx)
    SYSTEM_UNKNOWN = "SYS_9001"
    SYSTEM_FILE_ERROR = "SYS_9002"
    SYSTEM_NETWORK_ERROR = "SYS_9003"


# Error message mapping - maps error codes to user-friendly information
ERROR_MESSAGES: Dict[str, ErrorInfo] = {
    # MT5 Connection Errors
    ErrorCode.MT5_NOT_INSTALLED: ErrorInfo(
        code=ErrorCode.MT5_NOT_INSTALLED,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.CRITICAL,
        user_message="MetaTrader 5 is not installed",
        technical_message="MT5 terminal not found on system",
        guidance="Please install MetaTrader 5 from your broker's website and try again.",
        recoverable=False
    ),
    ErrorCode.MT5_INIT_FAILED: ErrorInfo(
        code=ErrorCode.MT5_INIT_FAILED,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.ERROR,
        user_message="Failed to initialize MT5",
        technical_message="MT5 initialization returned False",
        guidance="Make sure MT5 is running and try again. If the problem persists, restart MT5.",
        recoverable=True
    ),
    ErrorCode.MT5_INVALID_CREDENTIALS: ErrorInfo(
        code=ErrorCode.MT5_INVALID_CREDENTIALS,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.ERROR,
        user_message="Invalid MT5 credentials",
        technical_message="MT5 login failed - invalid login/password",
        guidance="Please check your login number and password, then try again.",
        recoverable=True
    ),
    ErrorCode.MT5_SERVER_UNREACHABLE: ErrorInfo(
        code=ErrorCode.MT5_SERVER_UNREACHABLE,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.ERROR,
        user_message="Cannot connect to trading server",
        technical_message="MT5 server connection failed",
        guidance="Check your internet connection and verify the server name is correct.",
        recoverable=True
    ),
    ErrorCode.MT5_CONNECTION_TIMEOUT: ErrorInfo(
        code=ErrorCode.MT5_CONNECTION_TIMEOUT,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.ERROR,
        user_message="Connection timed out",
        technical_message="MT5 connection timeout after 30 seconds",
        guidance="The server is taking too long to respond. Check your connection and try again.",
        recoverable=True
    ),
    ErrorCode.MT5_CONNECTION_LOST: ErrorInfo(
        code=ErrorCode.MT5_CONNECTION_LOST,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.WARNING,
        user_message="Connection to MT5 lost",
        technical_message="MT5 terminal connection dropped",
        guidance="Attempting to reconnect automatically...",
        recoverable=True
    ),
    ErrorCode.MT5_RECONNECT_FAILED: ErrorInfo(
        code=ErrorCode.MT5_RECONNECT_FAILED,
        category=ErrorCategory.CONNECTION,
        severity=ErrorSeverity.ERROR,
        user_message="Failed to reconnect to MT5",
        technical_message="All reconnection attempts exhausted",
        guidance="Please check your connection and reconnect manually from Settings.",
        recoverable=True
    ),
    
    # Trading Errors
    ErrorCode.TRADE_INSUFFICIENT_MARGIN: ErrorInfo(
        code=ErrorCode.TRADE_INSUFFICIENT_MARGIN,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.WARNING,
        user_message="Insufficient margin for trade",
        technical_message="Account margin insufficient for requested volume",
        guidance="Reduce the lot size or deposit more funds to your account.",
        recoverable=True
    ),
    ErrorCode.TRADE_ORDER_REJECTED: ErrorInfo(
        code=ErrorCode.TRADE_ORDER_REJECTED,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.WARNING,
        user_message="Order was rejected",
        technical_message="MT5 order_send returned rejection",
        guidance="The broker rejected this order. Check market conditions and try again.",
        recoverable=True
    ),
    ErrorCode.TRADE_SYMBOL_NOT_FOUND: ErrorInfo(
        code=ErrorCode.TRADE_SYMBOL_NOT_FOUND,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.ERROR,
        user_message="Trading symbol not found",
        technical_message="Symbol not available in MT5 terminal",
        guidance="This symbol is not available. Check if it's enabled in MT5 Market Watch.",
        recoverable=True
    ),
    ErrorCode.TRADE_INVALID_VOLUME: ErrorInfo(
        code=ErrorCode.TRADE_INVALID_VOLUME,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.WARNING,
        user_message="Invalid trade volume",
        technical_message="Volume outside allowed range",
        guidance="Adjust the lot size to be within the allowed range for this symbol.",
        recoverable=True
    ),
    ErrorCode.TRADE_MARKET_CLOSED: ErrorInfo(
        code=ErrorCode.TRADE_MARKET_CLOSED,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.INFO,
        user_message="Market is closed",
        technical_message="Trading session not active",
        guidance="Wait for the market to open before placing trades.",
        recoverable=True
    ),
    ErrorCode.TRADE_POSITION_NOT_FOUND: ErrorInfo(
        code=ErrorCode.TRADE_POSITION_NOT_FOUND,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.WARNING,
        user_message="Position not found",
        technical_message="Position ticket not found in open positions",
        guidance="The position may have been closed already.",
        recoverable=True
    ),
    ErrorCode.TRADE_MAX_POSITIONS: ErrorInfo(
        code=ErrorCode.TRADE_MAX_POSITIONS,
        category=ErrorCategory.TRADING,
        severity=ErrorSeverity.INFO,
        user_message="Maximum positions reached",
        technical_message="Position limit exceeded",
        guidance="Close some positions or increase the limit in Settings.",
        recoverable=True
    ),
    
    # Authentication Errors
    ErrorCode.AUTH_INVALID_CREDENTIALS: ErrorInfo(
        code=ErrorCode.AUTH_INVALID_CREDENTIALS,
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        user_message="Invalid email or password",
        technical_message="Supabase auth failed - invalid credentials",
        guidance="Please check your email and password, then try again.",
        recoverable=True
    ),
    ErrorCode.AUTH_EMAIL_NOT_CONFIRMED: ErrorInfo(
        code=ErrorCode.AUTH_EMAIL_NOT_CONFIRMED,
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        user_message="Email not confirmed",
        technical_message="Supabase auth failed - email not confirmed",
        guidance="Please check your inbox and confirm your email address first.",
        recoverable=True
    ),
    ErrorCode.AUTH_SESSION_EXPIRED: ErrorInfo(
        code=ErrorCode.AUTH_SESSION_EXPIRED,
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.WARNING,
        user_message="Session expired",
        technical_message="Auth token expired",
        guidance="Please log in again to continue.",
        recoverable=True
    ),
    ErrorCode.AUTH_NETWORK_ERROR: ErrorInfo(
        code=ErrorCode.AUTH_NETWORK_ERROR,
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        user_message="Network error during login",
        technical_message="Failed to reach authentication server",
        guidance="Check your internet connection and try again.",
        recoverable=True
    ),
    ErrorCode.AUTH_UNKNOWN: ErrorInfo(
        code=ErrorCode.AUTH_UNKNOWN,
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.ERROR,
        user_message="Login failed",
        technical_message="Unknown authentication error",
        guidance="Please try again. If the problem persists, contact support.",
        recoverable=True
    ),
    
    # Model Errors
    ErrorCode.MODEL_NOT_FOUND: ErrorInfo(
        code=ErrorCode.MODEL_NOT_FOUND,
        category=ErrorCategory.MODEL,
        severity=ErrorSeverity.WARNING,
        user_message="Model not found",
        technical_message="Model file not found in storage",
        guidance="Sync models from cloud or train a new model.",
        recoverable=True
    ),
    ErrorCode.MODEL_DECRYPTION_FAILED: ErrorInfo(
        code=ErrorCode.MODEL_DECRYPTION_FAILED,
        category=ErrorCategory.MODEL,
        severity=ErrorSeverity.ERROR,
        user_message="Model corrupted or invalid",
        technical_message="Model decryption failed",
        guidance="Re-download the model from cloud or train a new one.",
        recoverable=True
    ),
    ErrorCode.MODEL_LOAD_FAILED: ErrorInfo(
        code=ErrorCode.MODEL_LOAD_FAILED,
        category=ErrorCategory.MODEL,
        severity=ErrorSeverity.ERROR,
        user_message="Failed to load model",
        technical_message="Model loading error",
        guidance="The model file may be corrupted. Try syncing from cloud.",
        recoverable=True
    ),
    ErrorCode.MODEL_PREDICTION_FAILED: ErrorInfo(
        code=ErrorCode.MODEL_PREDICTION_FAILED,
        category=ErrorCategory.MODEL,
        severity=ErrorSeverity.WARNING,
        user_message="Prediction failed",
        technical_message="Model prediction error",
        guidance="Check if the model is compatible with current data.",
        recoverable=True
    ),
    ErrorCode.MODEL_SYNC_FAILED: ErrorInfo(
        code=ErrorCode.MODEL_SYNC_FAILED,
        category=ErrorCategory.MODEL,
        severity=ErrorSeverity.ERROR,
        user_message="Failed to sync models",
        technical_message="Cloud sync error",
        guidance="Check your internet connection and try again.",
        recoverable=True
    ),
    
    # Configuration Errors
    ErrorCode.CONFIG_LOAD_FAILED: ErrorInfo(
        code=ErrorCode.CONFIG_LOAD_FAILED,
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.WARNING,
        user_message="Failed to load settings",
        technical_message="Configuration file read error",
        guidance="Default settings will be used. Your settings may need to be reconfigured.",
        recoverable=True
    ),
    ErrorCode.CONFIG_SAVE_FAILED: ErrorInfo(
        code=ErrorCode.CONFIG_SAVE_FAILED,
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.WARNING,
        user_message="Failed to save settings",
        technical_message="Configuration file write error",
        guidance="Check disk space and permissions, then try again.",
        recoverable=True
    ),
    ErrorCode.CONFIG_INVALID: ErrorInfo(
        code=ErrorCode.CONFIG_INVALID,
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.WARNING,
        user_message="Invalid configuration",
        technical_message="Configuration validation failed",
        guidance="Some settings are invalid. Please review and correct them.",
        recoverable=True
    ),
    
    # System Errors
    ErrorCode.SYSTEM_UNKNOWN: ErrorInfo(
        code=ErrorCode.SYSTEM_UNKNOWN,
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.ERROR,
        user_message="An unexpected error occurred",
        technical_message="Unknown system error",
        guidance="Please try again. If the problem persists, check the logs.",
        recoverable=True
    ),
    ErrorCode.SYSTEM_FILE_ERROR: ErrorInfo(
        code=ErrorCode.SYSTEM_FILE_ERROR,
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.ERROR,
        user_message="File operation failed",
        technical_message="File system error",
        guidance="Check disk space and file permissions.",
        recoverable=True
    ),
    ErrorCode.SYSTEM_NETWORK_ERROR: ErrorInfo(
        code=ErrorCode.SYSTEM_NETWORK_ERROR,
        category=ErrorCategory.SYSTEM,
        severity=ErrorSeverity.ERROR,
        user_message="Network error",
        technical_message="Network operation failed",
        guidance="Check your internet connection and try again.",
        recoverable=True
    ),
}


def get_error_info(error_code: str) -> ErrorInfo:
    """
    Get error information for a given error code.
    
    Args:
        error_code: The error code to look up
        
    Returns:
        ErrorInfo object with user-friendly message and guidance
    """
    return ERROR_MESSAGES.get(error_code, ERROR_MESSAGES[ErrorCode.SYSTEM_UNKNOWN])


def get_user_message(error_code: str) -> str:
    """Get just the user-friendly message for an error code"""
    return get_error_info(error_code).user_message


def get_guidance(error_code: str) -> str:
    """Get the actionable guidance for an error code"""
    return get_error_info(error_code).guidance


def is_critical(error_code: str) -> bool:
    """Check if an error is critical (requires user action)"""
    info = get_error_info(error_code)
    return info.severity == ErrorSeverity.CRITICAL


def is_recoverable(error_code: str) -> bool:
    """Check if an error is recoverable"""
    return get_error_info(error_code).recoverable


class NexusTradeError(Exception):
    """Base exception for NexusTrade errors"""
    
    def __init__(self, error_code: str, details: Optional[str] = None):
        self.error_code = error_code
        self.error_info = get_error_info(error_code)
        self.details = details
        super().__init__(self.error_info.user_message)
    
    @property
    def user_message(self) -> str:
        return self.error_info.user_message
    
    @property
    def guidance(self) -> str:
        return self.error_info.guidance
    
    @property
    def is_critical(self) -> bool:
        return self.error_info.severity == ErrorSeverity.CRITICAL
    
    @property
    def category(self) -> ErrorCategory:
        return self.error_info.category


class MT5ConnectionError(NexusTradeError):
    """MT5 connection related errors"""
    pass


class TradingError(NexusTradeError):
    """Trading operation errors"""
    pass


class AuthenticationError(NexusTradeError):
    """Authentication errors"""
    pass


class ModelError(NexusTradeError):
    """Model related errors"""
    pass


class ConfigurationError(NexusTradeError):
    """Configuration errors"""
    pass
