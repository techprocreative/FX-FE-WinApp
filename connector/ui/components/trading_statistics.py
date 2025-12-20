"""
TradingStatistics - Real-time Trading Statistics Aggregator
Aggregates stats from AutoTrader and emits Qt signals for UI updates
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DailyStats:
    """Statistics for a trading day"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    active_positions: int = 0
    signals_generated: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    @property
    def avg_profit_per_trade(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.total_profit / self.total_trades


class TradingStatistics(QObject):
    """Aggregates and manages trading statistics with real-time updates"""

    # Signals for UI updates
    stats_updated = pyqtSignal(dict)  # Overall stats
    symbol_stats_updated = pyqtSignal(str, dict)  # Symbol-specific stats
    trade_executed = pyqtSignal(str, str, dict)  # symbol, signal, trade_info
    signal_generated = pyqtSignal(str, str, float)  # symbol, signal, confidence

    def __init__(self, parent=None):
        super().__init__(parent)
        self.daily_stats = DailyStats()
        self.symbol_stats: Dict[str, DailyStats] = {}
        self._previous_stats = {}  # For trend calculation

    def reset_daily_stats(self):
        """Reset statistics for a new trading day"""
        # Save previous for trends
        self._previous_stats = {
            'total_trades': self.daily_stats.total_trades,
            'win_rate': self.daily_stats.win_rate,
            'total_profit': self.daily_stats.total_profit
        }

        self.daily_stats = DailyStats()
        self.symbol_stats = {}

    def record_signal(self, symbol: str, signal: str, confidence: float):
        """Record a trading signal"""
        self.daily_stats.signals_generated += 1

        # Initialize symbol stats if needed
        if symbol not in self.symbol_stats:
            self.symbol_stats[symbol] = DailyStats()

        self.symbol_stats[symbol].signals_generated += 1

        # Emit signal
        self.signal_generated.emit(symbol, signal, confidence)
        self._emit_stats_update()

    def record_trade(self, symbol: str, signal: str, trade_info: dict):
        """Record a trade execution"""
        self.daily_stats.total_trades += 1

        # Initialize symbol stats if needed
        if symbol not in self.symbol_stats:
            self.symbol_stats[symbol] = DailyStats()

        self.symbol_stats[symbol].total_trades += 1

        # Emit signal
        self.trade_executed.emit(symbol, signal, trade_info)
        self._emit_stats_update()

    def record_trade_close(self, symbol: str, profit: float):
        """Record a trade closure with P&L"""
        is_win = profit > 0

        self.daily_stats.total_profit += profit
        if is_win:
            self.daily_stats.winning_trades += 1
        else:
            self.daily_stats.losing_trades += 1

        # Update symbol stats
        if symbol in self.symbol_stats:
            self.symbol_stats[symbol].total_profit += profit
            if is_win:
                self.symbol_stats[symbol].winning_trades += 1
            else:
                self.symbol_stats[symbol].losing_trades += 1

        self._emit_stats_update()

    def update_active_positions(self, count: int):
        """Update the count of active positions"""
        self.daily_stats.active_positions = count
        self._emit_stats_update()

    def get_overall_stats(self) -> dict:
        """Get overall statistics"""
        # Calculate trends
        total_trades_trend = self.daily_stats.total_trades - self._previous_stats.get('total_trades', 0)
        profit_trend = self.daily_stats.total_profit - self._previous_stats.get('total_profit', 0)

        return {
            'total_trades': self.daily_stats.total_trades,
            'total_trades_trend': total_trades_trend,
            'win_rate': self.daily_stats.win_rate,
            'winning_trades': self.daily_stats.winning_trades,
            'losing_trades': self.daily_stats.losing_trades,
            'total_profit': self.daily_stats.total_profit,
            'profit_trend': profit_trend,
            'active_positions': self.daily_stats.active_positions,
            'signals_generated': self.daily_stats.signals_generated,
            'avg_profit_per_trade': self.daily_stats.avg_profit_per_trade,
            'session_duration': (datetime.now() - self.daily_stats.start_time).total_seconds()
        }

    def get_symbol_stats(self, symbol: str) -> Optional[dict]:
        """Get statistics for a specific symbol"""
        if symbol not in self.symbol_stats:
            return None

        stats = self.symbol_stats[symbol]
        return {
            'total_trades': stats.total_trades,
            'win_rate': stats.win_rate,
            'winning_trades': stats.winning_trades,
            'losing_trades': stats.losing_trades,
            'total_profit': stats.total_profit,
            'active_positions': stats.active_positions,
            'signals_generated': stats.signals_generated,
            'avg_profit_per_trade': stats.avg_profit_per_trade
        }

    def _emit_stats_update(self):
        """Emit stats update signals"""
        overall = self.get_overall_stats()
        self.stats_updated.emit(overall)

        # Emit per-symbol updates
        for symbol in self.symbol_stats:
            symbol_data = self.get_symbol_stats(symbol)
            if symbol_data:
                self.symbol_stats_updated.emit(symbol, symbol_data)
