"""
Trading Module
Contains auto trading engine and risk management components.
"""

from trading.auto_trader import AutoTrader, Signal, TradingConfig, TradeStats
from trading.risk_manager import RiskManager

__all__ = [
    'AutoTrader',
    'Signal', 
    'TradingConfig',
    'TradeStats',
    'RiskManager',
]
