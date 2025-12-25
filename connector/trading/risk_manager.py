"""
Risk Manager Module
Handles position sizing, SL/TP calculation, and risk validation.
"""

from typing import Tuple
from loguru import logger


class RiskManager:
    """
    Calculates position sizing and risk parameters.
    
    Provides methods for:
    - Lot size calculation based on risk percentage
    - Stop loss and take profit level calculation
    - Risk percentage validation
    - Position limit validation
    """
    
    # Minimum lot size allowed by most brokers
    MIN_LOT_SIZE = 0.01
    
    # Risk percentage bounds
    MIN_RISK_PERCENT = 0.1
    MAX_RISK_PERCENT = 5.0
    
    def __init__(self):
        """Initialize RiskManager"""
        pass
    
    def calculate_lot_size(
        self, 
        balance: float, 
        risk_percent: float, 
        sl_pips: float, 
        pip_value: float
    ) -> float:
        """
        Calculate lot size based on risk percentage and account balance.
        
        Formula: lot_size = (balance * risk_percent / 100) / (sl_pips * pip_value)
        
        Args:
            balance: Account balance
            risk_percent: Risk percentage per trade (0.1 to 5.0)
            sl_pips: Stop loss distance in pips
            pip_value: Value per pip per lot
        
        Returns:
            Calculated lot size, minimum 0.01
        
        Requirements: 3.2, 3.5
        """
        if balance <= 0:
            logger.warning("Invalid balance for lot size calculation")
            return self.MIN_LOT_SIZE
        
        if sl_pips <= 0:
            logger.warning("Invalid SL pips for lot size calculation")
            return self.MIN_LOT_SIZE
        
        if pip_value <= 0:
            logger.warning("Invalid pip value for lot size calculation")
            return self.MIN_LOT_SIZE
        
        # Calculate risk amount
        risk_amount = balance * (risk_percent / 100)
        
        # Calculate lot size
        lot_size = risk_amount / (sl_pips * pip_value)
        
        # Round to 2 decimal places
        lot_size = round(lot_size, 2)
        
        # Enforce minimum lot size
        if lot_size < self.MIN_LOT_SIZE:
            logger.debug(f"Calculated lot size {lot_size} below minimum, using {self.MIN_LOT_SIZE}")
            return self.MIN_LOT_SIZE
        
        return lot_size
    
    def get_pip_size(self, symbol: str) -> float:
        """
        Get pip size for different instrument types.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'BTCUSD', 'XAUUSD')
        
        Returns:
            Pip size for the symbol
        
        Requirements: 3.2, 3.5
        """
        symbol_upper = symbol.upper()
        
        # Crypto pairs (BTC, ETH, etc.)
        if any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'LTC', 'XRP']):
            return 1.0
        
        # Metals (Gold, Silver)
        if any(metal in symbol_upper for metal in ['XAU', 'GOLD', 'XAG', 'SILVER']):
            return 0.1
        
        # JPY pairs
        if 'JPY' in symbol_upper:
            return 0.01
        
        # Standard forex pairs
        return 0.0001
    
    def calculate_sl_tp(
        self, 
        entry_price: float, 
        order_type: str, 
        sl_pips: float, 
        tp_pips: float, 
        pip_size: float
    ) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels.
        
        Args:
            entry_price: Entry price for the trade
            order_type: 'buy' or 'sell'
            sl_pips: Stop loss distance in pips
            tp_pips: Take profit distance in pips
            pip_size: Pip size for the symbol
        
        Returns:
            Tuple of (stop_loss, take_profit) prices
        
        Requirements: 3.3
        """
        order_type_lower = order_type.lower()
        
        sl_distance = sl_pips * pip_size
        tp_distance = tp_pips * pip_size
        
        if order_type_lower == 'buy':
            # For BUY: SL below entry, TP above entry
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:
            # For SELL: SL above entry, TP below entry
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        
        return (stop_loss, take_profit)
    
    def validate_risk_percent(self, value: float) -> bool:
        """
        Validate risk percentage is within allowed bounds.
        
        Args:
            value: Risk percentage to validate
        
        Returns:
            True if valid (0.1% to 5.0%), False otherwise
        
        Requirements: 3.1
        """
        return self.MIN_RISK_PERCENT <= value <= self.MAX_RISK_PERCENT
    
    def validate_position_limit(self, current: int, max_positions: int) -> bool:
        """
        Validate if a new position can be opened.
        
        Args:
            current: Current number of open positions
            max_positions: Maximum allowed positions
        
        Returns:
            True if new position can be opened, False otherwise
        
        Requirements: 3.4
        """
        return current < max_positions
