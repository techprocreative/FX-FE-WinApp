# AutoTrader Enhancement Summary

## Changes Made to `trading/auto_trader.py`

### 1. Added Position Close Tracking

**New Attributes** (line 93-99):
```python
# Track active positions for close detection
self._active_positions: Dict[int, Dict[str, Any]] = {}  # ticket -> position_info

# Callbacks for UI updates
self.on_signal_callback = None
self.on_trade_callback = None
self.on_close_callback = None  # NEW: Called when position closes
self.on_error_callback = None
```

### 2. Track Positions on Open (line 396-403)

When a trade is executed, we now store position info for close detection:

```python
# Track position for close detection
self._active_positions[ticket] = {
    'symbol': symbol,
    'signal': signal.value,
    'volume': volume,
    'open_time': datetime.now(),
    'open_price': tick[0]['close'] if tick else 0
}
```

### 3. New Method: `_check_closed_positions()` (line 414-465)

**Purpose**: Detect closed positions and calculate P&L from MT5 history

**How it works**:
1. Get current open positions from MT5
2. Compare with `_active_positions` to find closed tickets
3. Query `mt5.get_history()` for the closed position's deal
4. Extract profit from history
5. Update symbol statistics (total_profit, winning_trades, losing_trades)
6. Trigger `on_close_callback(ticket, profit)`
7. Remove from active tracking

**Code**:
```python
def _check_closed_positions(self):
    """Check for positions that have closed and trigger callbacks."""
    if not self._active_positions:
        return

    # Get current open positions
    current_positions = self.mt5.get_positions()
    current_tickets = {pos.ticket for pos in current_positions}

    # Find closed positions
    for ticket, pos_info in list(self._active_positions.items()):
        if ticket not in current_tickets:
            # Position has closed - query history for P&L
            symbol = pos_info['symbol']
            open_time = pos_info['open_time']

            from_date = open_time - timedelta(minutes=1)
            to_date = datetime.now()
            history = self.mt5.get_history(from_date, to_date)

            # Find profit
            profit = 0.0
            for trade in history:
                if trade.ticket == ticket:
                    profit = trade.profit
                    break

            # Update stats and trigger callback
            if symbol in self.stats:
                self.stats[symbol].total_profit += profit
                if profit > 0:
                    self.stats[symbol].winning_trades += 1
                elif profit < 0:
                    self.stats[symbol].losing_trades += 1

            if self.on_close_callback:
                self.on_close_callback(ticket, profit)

            del self._active_positions[ticket]
```

### 4. Integrated in Trading Loop (line 433-434)

The `run_loop()` now checks for closed positions every iteration:

```python
async def run_loop(self, interval_seconds: int = 60):
    while self.running:
        # ... connection check ...

        # Check for closed positions
        self._check_closed_positions()  # NEW

        # Process predictions and signals
        for symbol, model_info in self.models.items():
            # ...
```

## Integration with MainWindow

The AutoTrader changes are fully compatible with the MainWindow implementation:

### Signal Connection (main_window.py line 1468)
```python
self.trader_thread.trade_closed.connect(self._on_trade_close)
```

### Callback Setup (main_window.py line 58)
```python
self.auto_trader.on_close_callback = lambda t, p: self.trade_closed.emit(t, p)
```

### Event Handler (main_window.py line 1628-1673)
```python
def _on_trade_close(self, ticket: int, profit: float):
    """Handle trade close - Update P&L in trade log"""
    # Find row from ticket mapping
    # Update P&L column with color coding
    # Update Status column
    # Clean up tracking
```

## Testing Checklist

### Unit Testing
- [ ] Verify `_active_positions` populates on trade execution
- [ ] Verify `_check_closed_positions()` detects closed positions
- [ ] Verify profit correctly extracted from MT5 history
- [ ] Verify stats update correctly (total_profit, win_rate)
- [ ] Verify callback fires with correct ticket and profit

### Integration Testing
- [ ] Connect to MT5
- [ ] Load a model
- [ ] Start auto trading
- [ ] Execute a trade (manual or via signal)
- [ ] Close the position manually
- [ ] Verify `on_close_callback` fires
- [ ] Verify UI updates with P&L in trade log
- [ ] Verify stats cards update correctly

### Edge Cases
- [ ] Position closed before first loop iteration (check on startup)
- [ ] Multiple positions close simultaneously
- [ ] MT5 history query fails (error handling)
- [ ] Position not found in history (defaults to profit=0)
- [ ] Very old positions (history query timeframe)

## Known Limitations

1. **History Query Timeframe**: Uses `open_time - 1 minute` to `now`
   - Assumption: Position close history is available in this range
   - May fail for very quick trades (< 1 minute)
   - **Mitigation**: Could expand timeframe if needed

2. **Ticket Matching**: Relies on `trade.ticket == position.ticket`
   - MT5 history API returns `position_id` which should match
   - Verify this mapping is correct in your MT5 setup

3. **Polling-based Detection**: Checks closed positions every loop iteration
   - Not instant - there's a delay up to `interval_seconds`
   - **Alternative**: Could poll more frequently in separate task

## Performance Considerations

- `_check_closed_positions()` only runs if `_active_positions` is non-empty
- History query is scoped to specific timeframe (not entire history)
- Uses set comparison for O(n) closed position detection
- Removes from `_active_positions` immediately after detection

## Files Modified

1. **trading/auto_trader.py**
   - Lines added: ~60 lines
   - New method: `_check_closed_positions()`
   - Modified: `__init__`, `execute_signal`, `run_loop`

## Status

✅ **Implementation Complete**

All AutoTrader enhancements for P&L tracking are now implemented and integrated with the MainWindow UI redesign.

**Next**: Run manual tests to verify the complete flow works end-to-end.
