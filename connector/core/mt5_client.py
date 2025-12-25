"""
MT5 Client Module
Handles all MetaTrader 5 API interactions

Requirements: 1.3, 1.4, 1.5, 1.6, 8.1
"""

import MetaTrader5 as mt5
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass
from loguru import logger

from core.config import MT5Config
from core.errors import (
    ErrorCode, 
    get_error_info, 
    MT5ConnectionError,
    TradingError,
)


@dataclass
class AccountInfo:
    """MT5 Account Information"""
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    margin_free: float
    profit: float
    leverage: int
    currency: str


@dataclass
class Position:
    """Open position data"""
    ticket: int
    symbol: str
    type: str  # 'buy' or 'sell'
    volume: float
    open_price: float
    current_price: float
    open_time: datetime
    profit: float
    swap: float
    magic: int
    comment: str


@dataclass
class Trade:
    """Closed trade/deal data"""
    ticket: int
    symbol: str
    type: str
    volume: float
    open_price: float
    close_price: float
    open_time: datetime
    close_time: datetime
    profit: float
    commission: float
    swap: float
    magic: int
    comment: str


class MT5Client:
    """MetaTrader 5 API Client"""
    
    # Reconnection constants
    MAX_RECONNECT_ATTEMPTS = 3
    RECONNECT_INTERVAL_SECONDS = 10
    
    # MT5 error code mappings
    MT5_ERROR_CODES = {
        # Connection errors
        -1: ErrorCode.MT5_NOT_INSTALLED,
        -2: ErrorCode.MT5_INIT_FAILED,
        -3: ErrorCode.MT5_INVALID_CREDENTIALS,
        -4: ErrorCode.MT5_SERVER_UNREACHABLE,
        -5: ErrorCode.MT5_CONNECTION_TIMEOUT,
        # Trade errors (MT5 retcodes)
        10004: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_REQUOTE
        10006: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_REJECT
        10007: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_CANCEL
        10010: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_PRICE_CHANGED
        10011: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_PRICE_OFF
        10013: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_INVALID
        10014: ErrorCode.TRADE_INVALID_VOLUME,  # TRADE_RETCODE_INVALID_VOLUME
        10015: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_INVALID_PRICE
        10016: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_INVALID_STOPS
        10017: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_TRADE_DISABLED
        10018: ErrorCode.TRADE_MARKET_CLOSED,   # TRADE_RETCODE_MARKET_CLOSED
        10019: ErrorCode.TRADE_INSUFFICIENT_MARGIN,  # TRADE_RETCODE_NO_MONEY
        10020: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_PRICE_CHANGED
        10021: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_PRICE_OFF
        10022: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_INVALID_EXPIRATION
        10023: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_ORDER_CHANGED
        10024: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_TOO_MANY_REQUESTS
        10025: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_NO_CHANGES
        10026: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_SERVER_DISABLES_AT
        10027: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_CLIENT_DISABLES_AT
        10028: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_LOCKED
        10029: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_FROZEN
        10030: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_INVALID_FILL
        10031: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_CONNECTION
        10032: ErrorCode.TRADE_ORDER_REJECTED,  # TRADE_RETCODE_ONLY_REAL
        10033: ErrorCode.TRADE_MAX_POSITIONS,   # TRADE_RETCODE_LIMIT_ORDERS
        10034: ErrorCode.TRADE_MAX_POSITIONS,   # TRADE_RETCODE_LIMIT_VOLUME
    }
    
    def __init__(self, config: Optional[MT5Config] = None):
        self.config = config or MT5Config()
        self._connected = False
        self._account_info: Optional[AccountInfo] = None
        
        # Reconnection state
        self._reconnect_attempts = 0
        self._last_credentials: Optional[Dict[str, Any]] = None
        self._reconnecting = False
        
        # Last error information
        self._last_error_code: Optional[str] = None
        self._last_error_details: Optional[str] = None
        
        # Callback for connection state changes
        self.on_connection_lost_callback: Optional[Callable[[], None]] = None
        self.on_reconnected_callback: Optional[Callable[[], None]] = None
        self.on_reconnect_failed_callback: Optional[Callable[[int], None]] = None
        self.on_error_callback: Optional[Callable[[str, str], None]] = None  # error_code, details
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        return self._connected and mt5.terminal_info() is not None
    
    @property
    def last_error_code(self) -> Optional[str]:
        """Get the last error code"""
        return self._last_error_code
    
    @property
    def last_error_details(self) -> Optional[str]:
        """Get the last error details"""
        return self._last_error_details
    
    def _set_error(self, error_code: str, details: Optional[str] = None) -> None:
        """Set the last error and trigger callback"""
        self._last_error_code = error_code
        self._last_error_details = details
        logger.error(f"MT5 Error [{error_code}]: {details}")
        
        if self.on_error_callback:
            self.on_error_callback(error_code, details or "")
    
    def _classify_mt5_error(self, mt5_error: Tuple[int, str]) -> str:
        """
        Classify MT5 error into our error code system.
        
        Args:
            mt5_error: Tuple of (error_code, error_description) from mt5.last_error()
            
        Returns:
            Our internal error code
        """
        error_num, error_desc = mt5_error
        
        # Check for known error codes
        if error_num in self.MT5_ERROR_CODES:
            return self.MT5_ERROR_CODES[error_num]
        
        # Classify by error description patterns
        error_desc_lower = error_desc.lower() if error_desc else ""
        
        if "timeout" in error_desc_lower:
            return ErrorCode.MT5_CONNECTION_TIMEOUT
        elif "invalid" in error_desc_lower and "credential" in error_desc_lower:
            return ErrorCode.MT5_INVALID_CREDENTIALS
        elif "invalid" in error_desc_lower and ("login" in error_desc_lower or "password" in error_desc_lower):
            return ErrorCode.MT5_INVALID_CREDENTIALS
        elif "server" in error_desc_lower or "connect" in error_desc_lower:
            return ErrorCode.MT5_SERVER_UNREACHABLE
        elif "margin" in error_desc_lower or "money" in error_desc_lower:
            return ErrorCode.TRADE_INSUFFICIENT_MARGIN
        elif "symbol" in error_desc_lower and "not found" in error_desc_lower:
            return ErrorCode.TRADE_SYMBOL_NOT_FOUND
        elif "volume" in error_desc_lower:
            return ErrorCode.TRADE_INVALID_VOLUME
        elif "market" in error_desc_lower and "closed" in error_desc_lower:
            return ErrorCode.TRADE_MARKET_CLOSED
        
        # Default to generic connection error for unknown errors
        return ErrorCode.MT5_INIT_FAILED
    
    def _classify_trade_retcode(self, retcode: int, comment: str = "") -> str:
        """
        Classify MT5 trade return code into our error code system.
        
        Args:
            retcode: MT5 trade return code
            comment: Optional comment from MT5
            
        Returns:
            Our internal error code
        """
        if retcode in self.MT5_ERROR_CODES:
            return self.MT5_ERROR_CODES[retcode]
        
        # Classify by comment patterns
        comment_lower = comment.lower() if comment else ""
        
        if "margin" in comment_lower or "money" in comment_lower:
            return ErrorCode.TRADE_INSUFFICIENT_MARGIN
        elif "volume" in comment_lower:
            return ErrorCode.TRADE_INVALID_VOLUME
        elif "market" in comment_lower and "closed" in comment_lower:
            return ErrorCode.TRADE_MARKET_CLOSED
        
        return ErrorCode.TRADE_ORDER_REJECTED
    
    def initialize(self) -> bool:
        """Initialize MT5 terminal connection"""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                error_code = self._classify_mt5_error(error)
                self._set_error(error_code, f"MT5 error: {error}")
                return False
            
            logger.info("MT5 terminal initialized successfully")
            return True
        except Exception as e:
            self._set_error(ErrorCode.MT5_NOT_INSTALLED, str(e))
            return False
    
    def login(self, login: int, password: str, server: str) -> bool:
        """Login to MT5 account"""
        try:
            if not self.initialize():
                return False
            
            authorized = mt5.login(
                login=login,
                password=password,
                server=server,
                timeout=self.config.timeout
            )
            
            if not authorized:
                error = mt5.last_error()
                error_code = self._classify_mt5_error(error)
                self._set_error(error_code, f"Login failed for {login}@{server}: {error}")
                return False
            
            self._connected = True
            self._reconnect_attempts = 0  # Reset on successful login
            self._last_error_code = None  # Clear any previous errors
            
            # Store credentials for potential reconnection
            self._last_credentials = {
                'login': login,
                'password': password,
                'server': server
            }
            
            self._update_account_info()
            logger.info(f"Logged in to MT5 account {login} on {server}")
            return True
            
        except Exception as e:
            self._set_error(ErrorCode.MT5_INIT_FAILED, str(e))
            return False
    
    def login_with_error(self, login: int, password: str, server: str) -> Tuple[bool, Optional[str]]:
        """
        Login to MT5 account with detailed error information.
        
        Returns:
            Tuple of (success, error_code) where error_code is None on success
        """
        success = self.login(login, password, server)
        return (success, None if success else self._last_error_code)
    
    def logout(self):
        """Logout and shutdown MT5"""
        try:
            mt5.shutdown()
            self._connected = False
            self._account_info = None
            self._last_credentials = None  # Clear credentials on explicit logout
            self._reconnect_attempts = 0
            logger.info("MT5 connection closed")
        except Exception as e:
            logger.exception(f"MT5 logout error: {e}")
    
    def _attempt_reconnect(self) -> bool:
        """
        Attempt to reconnect to MT5 after connection loss.
        
        Implements retry logic with up to MAX_RECONNECT_ATTEMPTS attempts
        and RECONNECT_INTERVAL_SECONDS between attempts.
        
        Returns:
            True if reconnection successful, False if all attempts failed
        """
        if self._last_credentials is None:
            self._set_error(ErrorCode.MT5_RECONNECT_FAILED, "Cannot reconnect: no stored credentials")
            return False
        
        if self._reconnecting:
            logger.debug("Reconnection already in progress")
            return False
        
        self._reconnecting = True
        
        try:
            while self._reconnect_attempts < self.MAX_RECONNECT_ATTEMPTS:
                self._reconnect_attempts += 1
                logger.info(
                    f"Reconnection attempt {self._reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS}"
                )
                
                # Shutdown existing connection first
                try:
                    mt5.shutdown()
                except Exception:
                    pass
                
                # Wait before attempting reconnection
                if self._reconnect_attempts > 1:
                    logger.info(f"Waiting {self.RECONNECT_INTERVAL_SECONDS}s before retry...")
                    time.sleep(self.RECONNECT_INTERVAL_SECONDS)
                
                # Attempt to reconnect
                if self.initialize():
                    authorized = mt5.login(
                        login=self._last_credentials['login'],
                        password=self._last_credentials['password'],
                        server=self._last_credentials['server'],
                        timeout=self.config.timeout
                    )
                    
                    if authorized:
                        self._connected = True
                        self._reconnect_attempts = 0
                        self._last_error_code = None  # Clear error on success
                        self._update_account_info()
                        logger.info("Reconnection successful")
                        
                        if self.on_reconnected_callback:
                            self.on_reconnected_callback()
                        
                        return True
                
                logger.warning(f"Reconnection attempt {self._reconnect_attempts} failed")
            
            # All attempts exhausted
            self._set_error(
                ErrorCode.MT5_RECONNECT_FAILED,
                f"Reconnection failed after {self.MAX_RECONNECT_ATTEMPTS} attempts"
            )
            self._connected = False
            
            if self.on_reconnect_failed_callback:
                self.on_reconnect_failed_callback(self._reconnect_attempts)
            
            return False
            
        finally:
            self._reconnecting = False
    
    def check_connection(self) -> bool:
        """
        Check connection status and trigger reconnection if connection lost.
        
        This method should be called periodically to detect connection loss
        and automatically attempt reconnection.
        
        Returns:
            True if connected (or reconnected), False otherwise
        """
        # Check if we think we're connected but MT5 terminal says otherwise
        if self._connected and mt5.terminal_info() is None:
            self._set_error(ErrorCode.MT5_CONNECTION_LOST, "Connection lost detected")
            self._connected = False
            
            if self.on_connection_lost_callback:
                self.on_connection_lost_callback()
            
            # Attempt automatic reconnection if we have credentials
            if self._last_credentials is not None:
                return self._attempt_reconnect()
            
            return False
        
        return self._connected
    
    def reset_reconnect_attempts(self):
        """Reset the reconnection attempt counter"""
        self._reconnect_attempts = 0
    
    def _update_account_info(self):
        """Update cached account info"""
        if not self.is_connected:
            return
        
        info = mt5.account_info()
        if info:
            self._account_info = AccountInfo(
                login=info.login,
                server=info.server,
                balance=info.balance,
                equity=info.equity,
                margin=info.margin,
                margin_free=info.margin_free,
                profit=info.profit,
                leverage=info.leverage,
                currency=info.currency
            )
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get current account information"""
        self._update_account_info()
        return self._account_info
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        if not self.is_connected:
            return []
        
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        result = []
        for pos in positions:
            result.append(Position(
                ticket=pos.ticket,
                symbol=pos.symbol,
                type='buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                volume=pos.volume,
                open_price=pos.price_open,
                current_price=pos.price_current,
                open_time=datetime.fromtimestamp(pos.time),
                profit=pos.profit,
                swap=pos.swap,
                magic=pos.magic,
                comment=pos.comment
            ))
        
        return result
    
    def get_history(
        self, 
        from_date: datetime, 
        to_date: Optional[datetime] = None
    ) -> List[Trade]:
        """Get trade history for date range"""
        if not self.is_connected:
            return []
        
        to_date = to_date or datetime.now()
        
        deals = mt5.history_deals_get(from_date, to_date)
        if deals is None:
            return []
        
        # Group deals by position id to match entry/exit
        result = []
        for deal in deals:
            if deal.entry == mt5.DEAL_ENTRY_OUT:  # Closing deals
                result.append(Trade(
                    ticket=deal.position_id,
                    symbol=deal.symbol,
                    type='buy' if deal.type == mt5.DEAL_TYPE_SELL else 'sell',  # Closing is opposite
                    volume=deal.volume,
                    open_price=deal.price,  # Simplified
                    close_price=deal.price,
                    open_time=datetime.fromtimestamp(deal.time),
                    close_time=datetime.fromtimestamp(deal.time),
                    profit=deal.profit,
                    commission=deal.commission,
                    swap=deal.swap,
                    magic=deal.magic,
                    comment=deal.comment
                ))
        
        return result
    
    def open_position(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        magic: int = 0,
        comment: str = ""
    ) -> Optional[int]:
        """Open a new position"""
        if not self.is_connected:
            self._set_error(ErrorCode.MT5_CONNECTION_LOST, "Not connected to MT5")
            return None
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self._set_error(ErrorCode.TRADE_SYMBOL_NOT_FOUND, f"Symbol {symbol} not found")
            return None
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                self._set_error(ErrorCode.TRADE_SYMBOL_NOT_FOUND, f"Failed to select symbol {symbol}")
                return None
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            self._set_error(ErrorCode.TRADE_SYMBOL_NOT_FOUND, f"Failed to get tick for {symbol}")
            return None
        
        # Determine order type and price
        if order_type.lower() == 'buy':
            mt5_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        else:
            mt5_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        
        # Create order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": mt5_type,
            "price": price,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if sl:
            request["sl"] = sl
        if tp:
            request["tp"] = tp
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            error_code = self._classify_mt5_error(error)
            self._set_error(error_code, f"Order failed: {error}")
            return None
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code = self._classify_trade_retcode(result.retcode, result.comment)
            self._set_error(error_code, f"Order rejected: {result.retcode} - {result.comment}")
            return None
        
        logger.info(f"Position opened: {result.order} {order_type} {volume} {symbol}")
        return result.order
    
    def open_position_with_error(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        magic: int = 0,
        comment: str = ""
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Open a new position with detailed error information.
        
        Returns:
            Tuple of (ticket, error_code) where error_code is None on success
        """
        ticket = self.open_position(symbol, order_type, volume, sl, tp, magic, comment)
        return (ticket, None if ticket else self._last_error_code)
    
    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        if not self.is_connected:
            self._set_error(ErrorCode.MT5_CONNECTION_LOST, "Not connected to MT5")
            return False
        
        position = mt5.positions_get(ticket=ticket)
        if not position:
            self._set_error(ErrorCode.TRADE_POSITION_NOT_FOUND, f"Position {ticket} not found")
            return False
        
        position = position[0]
        
        # Determine close type and price
        tick = mt5.symbol_info_tick(position.symbol)
        if tick is None:
            self._set_error(ErrorCode.TRADE_SYMBOL_NOT_FOUND, f"Failed to get tick for {position.symbol}")
            return False
        
        if position.type == mt5.ORDER_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            close_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            error_code = self._classify_mt5_error(error)
            self._set_error(error_code, f"Close failed for {ticket}: {error}")
            return False
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code = self._classify_trade_retcode(result.retcode, result.comment)
            self._set_error(error_code, f"Close rejected for {ticket}: {result.retcode} - {result.comment}")
            return False
        
        logger.info(f"Position {ticket} closed")
        return True
    
    def close_position_with_error(self, ticket: int) -> Tuple[bool, Optional[str]]:
        """
        Close a position with detailed error information.
        
        Returns:
            Tuple of (success, error_code) where error_code is None on success
        """
        success = self.close_position(ticket)
        return (success, None if success else self._last_error_code)
    
    def get_symbols(self) -> List[str]:
        """Get list of available symbols"""
        if not self.is_connected:
            return []
        
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        
        return [s.name for s in symbols if s.visible]
    
    def get_ohlc(
        self,
        symbol: str,
        timeframe: str,
        count: int = 1000
    ) -> Optional[List[Dict[str, Any]]]:
        """Get OHLC data for symbol"""
        if not self.is_connected:
            return None
        
        # Map timeframe string to MT5 constant
        tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
        }
        
        mt5_tf = tf_map.get(timeframe.upper())
        if mt5_tf is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None
        
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
        if rates is None:
            return None
        
        result = []
        for rate in rates:
            result.append({
                'time': datetime.fromtimestamp(rate['time']),
                'open': rate['open'],
                'high': rate['high'],
                'low': rate['low'],
                'close': rate['close'],
                'volume': rate['tick_volume']
            })
        
        return result
