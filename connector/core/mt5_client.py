"""
MT5 Client Module
Handles all MetaTrader 5 API interactions
"""

import MetaTrader5 as mt5
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from core.config import MT5Config


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
    
    def __init__(self, config: Optional[MT5Config] = None):
        self.config = config or MT5Config()
        self._connected = False
        self._account_info: Optional[AccountInfo] = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        return self._connected and mt5.terminal_info() is not None
    
    def initialize(self) -> bool:
        """Initialize MT5 terminal connection"""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            logger.info("MT5 terminal initialized successfully")
            return True
        except Exception as e:
            logger.exception(f"MT5 initialization error: {e}")
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
                logger.error(f"MT5 login failed: {error}")
                return False
            
            self._connected = True
            self._update_account_info()
            logger.info(f"Logged in to MT5 account {login} on {server}")
            return True
            
        except Exception as e:
            logger.exception(f"MT5 login error: {e}")
            return False
    
    def logout(self):
        """Logout and shutdown MT5"""
        try:
            mt5.shutdown()
            self._connected = False
            self._account_info = None
            logger.info("MT5 connection closed")
        except Exception as e:
            logger.exception(f"MT5 logout error: {e}")
    
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
            logger.error("Not connected to MT5")
            return None
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return None
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}")
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
            logger.error(f"Order failed: {error}")
            return None
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return None
        
        logger.info(f"Position opened: {result.order} {order_type} {volume} {symbol}")
        return result.order
    
    def close_position(self, ticket: int) -> bool:
        """Close a position by ticket"""
        if not self.is_connected:
            return False
        
        position = mt5.positions_get(ticket=ticket)
        if not position:
            logger.error(f"Position {ticket} not found")
            return False
        
        position = position[0]
        
        # Determine close type and price
        tick = mt5.symbol_info_tick(position.symbol)
        if tick is None:
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
        
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close failed for {ticket}")
            return False
        
        logger.info(f"Position {ticket} closed")
        return True
    
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
