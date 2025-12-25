"""
Auto Trader Module
ML-based automatic trading engine for BTCUSD and XAUUSD
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger

from core.mt5_client import MT5Client
from security.model_security import ModelSecurity, SecuredModel
from trading.risk_manager import RiskManager


class Signal(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradingConfig:
    """Configuration for auto trading"""
    symbol: str
    timeframe: str = "M15"
    volume: float = 0.01
    risk_percent: float = 1.0  # % of balance per trade
    max_positions: int = 1
    confidence_threshold: float = 0.6
    sl_pips: float = 50.0
    tp_pips: float = 100.0
    magic_number: int = 88888


@dataclass
class ModelInfo:
    """Information about a loaded model"""
    model_id: str
    symbol: str
    model: Any  # sklearn model
    config: TradingConfig
    last_prediction: Optional[Signal] = None
    last_prediction_time: Optional[datetime] = None
    accuracy: float = 0.0
    total_predictions: int = 0


@dataclass 
class TradeStats:
    """Trading statistics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.winning_trades / self.total_trades * 100


class AutoTrader:
    """
    ML-based automatic trading engine.
    Manages multiple models for different symbols.
    """
    
    def __init__(
        self, 
        mt5_client: MT5Client, 
        model_security: ModelSecurity,
        risk_manager: Optional[RiskManager] = None
    ):
        self.mt5 = mt5_client
        self.security = model_security
        self.risk_manager = risk_manager or RiskManager()
        
        # Active models: symbol -> ModelInfo
        self.models: Dict[str, ModelInfo] = {}
        
        # Trading state
        self.running = False
        self.paused = False
        self._task: Optional[asyncio.Task] = None
        
        # Statistics per symbol
        self.stats: Dict[str, TradeStats] = {}

        # Track active positions for close detection
        self._active_positions: Dict[int, Dict[str, Any]] = {}  # ticket -> position_info

        # Callbacks for UI updates
        self.on_signal_callback = None
        self.on_trade_callback = None
        self.on_close_callback = None  # NEW: Called when position closes
        self.on_error_callback = None
    
    def load_model(
        self, 
        model_id: str, 
        symbol: str,
        config: Optional[TradingConfig] = None
    ) -> bool:
        """
        Load an encrypted model for a symbol.
        
        Args:
            model_id: ID of the model in storage
            symbol: Trading symbol (e.g., 'BTCUSD', 'XAUUSD')
            config: Trading configuration
        
        Returns:
            True if model loaded successfully
        """
        try:
            # Load and decrypt model
            secured = self.security.load_secured_model(model_id)
            if not secured:
                logger.error(f"Model {model_id} not found")
                return False
            
            model = self.security.decrypt_model(secured)
            if not model:
                logger.error(f"Failed to decrypt model {model_id}")
                return False
            
            # Create config if not provided
            if config is None:
                config = TradingConfig(symbol=symbol)
            
            # Store model info
            self.models[symbol] = ModelInfo(
                model_id=model_id,
                symbol=symbol,
                model=model,
                config=config,
                accuracy=secured.metadata.get("accuracy", 0.0)
            )
            
            # Initialize stats
            if symbol not in self.stats:
                self.stats[symbol] = TradeStats()
            
            logger.info(f"Model {model_id} loaded for {symbol}")
            return True
            
        except Exception as e:
            logger.exception(f"Error loading model {model_id}: {e}")
            return False
    
    def unload_model(self, symbol: str) -> bool:
        """Unload model for a symbol"""
        if symbol in self.models:
            del self.models[symbol]
            logger.info(f"Model unloaded for {symbol}")
            return True
        return False
    
    def get_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicator features from OHLC data.
        
        Features:
        - RSI (14)
        - MACD & Signal
        - Bollinger Bands (20, 2)
        - EMA 9, 21
        - ATR (14)
        - Price change %
        """
        features = pd.DataFrame(index=df.index)
        
        # Price data
        close = df['close']
        high = df['high']
        low = df['low']
        
        # RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        features['macd'] = ema12 - ema26
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        # Bollinger Bands
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        features['bb_upper'] = sma20 + (std20 * 2)
        features['bb_lower'] = sma20 - (std20 * 2)
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma20
        features['bb_position'] = (close - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
        
        # EMAs
        features['ema_9'] = close.ewm(span=9, adjust=False).mean()
        features['ema_21'] = close.ewm(span=21, adjust=False).mean()
        features['ema_cross'] = (features['ema_9'] - features['ema_21']) / close
        
        # ATR (14)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        features['atr'] = tr.rolling(window=14).mean()
        features['atr_percent'] = features['atr'] / close * 100
        
        # Price change
        features['price_change'] = close.pct_change() * 100
        features['price_change_5'] = close.pct_change(5) * 100
        
        # Volume (if available)
        if 'volume' in df.columns:
            features['volume_ma'] = df['volume'].rolling(window=20).mean()
            features['volume_ratio'] = df['volume'] / features['volume_ma']
        
        # Normalize features
        for col in features.columns:
            if features[col].std() > 0:
                features[col] = (features[col] - features[col].mean()) / features[col].std()
        
        return features.dropna()
    
    def predict(self, symbol: str) -> tuple[Signal, float]:
        """
        Get ML prediction for a symbol.
        
        Returns:
            (Signal, confidence) tuple
        """
        if symbol not in self.models:
            return Signal.HOLD, 0.0
        
        model_info = self.models[symbol]
        
        try:
            # Get OHLC data
            ohlc = self.mt5.get_ohlc(
                symbol=symbol,
                timeframe=model_info.config.timeframe,
                count=100  # Need enough for indicators
            )
            
            if not ohlc or len(ohlc) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return Signal.HOLD, 0.0
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlc)
            
            # Calculate features
            features = self.get_features(df)
            
            if features.empty:
                return Signal.HOLD, 0.0
            
            # Get latest features
            X = features.iloc[[-1]].values
            
            # Predict
            model = model_info.model
            
            # Get prediction (0=sell, 1=hold, 2=buy)
            prediction = model.predict(X)[0]
            
            # Get confidence (probability)
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)[0]
                confidence = max(proba)
            else:
                confidence = 0.7  # Default for models without proba
            
            # Map prediction to signal
            if prediction == 2:
                signal = Signal.BUY
            elif prediction == 0:
                signal = Signal.SELL
            else:
                signal = Signal.HOLD
            
            # Update model info
            model_info.last_prediction = signal
            model_info.last_prediction_time = datetime.now()
            model_info.total_predictions += 1
            
            logger.info(f"{symbol}: Predicted {signal.value} with confidence {confidence:.2%}")
            
            return signal, confidence
            
        except Exception as e:
            logger.exception(f"Prediction error for {symbol}: {e}")
            return Signal.HOLD, 0.0
    
    def execute_signal(
        self, 
        symbol: str, 
        signal: Signal, 
        confidence: float
    ) -> Optional[int]:
        """
        Execute a trading signal.
        
        Args:
            symbol: Trading symbol
            signal: BUY, SELL, or HOLD
            confidence: Prediction confidence
        
        Returns:
            Ticket number if trade executed, None otherwise
        """
        if symbol not in self.models:
            return None
        
        config = self.models[symbol].config
        
        # Check confidence threshold
        if confidence < config.confidence_threshold:
            logger.debug(f"Confidence {confidence:.2%} below threshold {config.confidence_threshold:.2%}")
            return None
        
        # Check if we should trade
        if signal == Signal.HOLD:
            return None
        
        # Check existing positions
        positions = self.mt5.get_positions()
        symbol_positions = [p for p in positions if p.symbol == symbol and p.magic == config.magic_number]
        
        if len(symbol_positions) >= config.max_positions:
            logger.debug(f"Max positions ({config.max_positions}) reached for {symbol}")
            return None
        
        # Check for conflicting positions
        for pos in symbol_positions:
            if (signal == Signal.BUY and pos.type == 'sell') or \
               (signal == Signal.SELL and pos.type == 'buy'):
                # Close conflicting position first
                self.mt5.close_position(pos.ticket)
                logger.info(f"Closed conflicting position {pos.ticket}")
        
        # Get pip size using RiskManager
        pip_size = self.risk_manager.get_pip_size(symbol)
        
        # Calculate volume based on risk using RiskManager
        account = self.mt5.get_account_info()
        if account:
            # Estimate pip value (simplified: pip_size * volume * 100000 for forex)
            # For crypto/metals, pip_value varies by instrument
            pip_value = pip_size * 100000  # Standard lot pip value estimate
            if 'BTC' in symbol.upper():
                pip_value = 1.0  # BTC pip value per lot
            elif 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
                pip_value = 10.0  # Gold pip value per lot
            
            volume = self.risk_manager.calculate_lot_size(
                balance=account.balance,
                risk_percent=config.risk_percent,
                sl_pips=config.sl_pips,
                pip_value=pip_value
            )
        else:
            volume = config.volume
        
        # Get current price for SL/TP calculation
        tick = self.mt5.get_ohlc(symbol, "M1", 1)
        if tick:
            current_price = tick[0]['close']
            
            # Calculate SL/TP using RiskManager
            sl, tp = self.risk_manager.calculate_sl_tp(
                entry_price=current_price,
                order_type=signal.value,
                sl_pips=config.sl_pips,
                tp_pips=config.tp_pips,
                pip_size=pip_size
            )
        else:
            sl = None
            tp = None
        
        # Execute trade
        ticket = self.mt5.open_position(
            symbol=symbol,
            order_type=signal.value,
            volume=volume,
            sl=sl,
            tp=tp,
            magic=config.magic_number,
            comment=f"NexusTrade ML {confidence:.0%}"
        )
        
        if ticket:
            logger.info(f"Trade executed: {signal.value} {volume} {symbol} @ ticket {ticket}")

            # Track position for close detection
            self._active_positions[ticket] = {
                'symbol': symbol,
                'signal': signal.value,
                'volume': volume,
                'open_time': datetime.now(),
                'open_price': tick[0]['close'] if tick else 0
            }

            # Update stats
            self.stats[symbol].total_trades += 1

            # Callback
            if self.on_trade_callback:
                self.on_trade_callback(symbol, signal, ticket, volume)

        return ticket

    def _check_closed_positions(self):
        """
        Check for positions that have closed and trigger callbacks.
        Updates statistics with P&L.
        """
        if not self._active_positions:
            return

        # Get current open positions from MT5
        current_positions = self.mt5.get_positions()
        current_tickets = {pos.ticket for pos in current_positions}

        # Find closed positions
        for ticket, pos_info in list(self._active_positions.items()):
            if ticket not in current_tickets:
                # Position has closed
                try:
                    symbol = pos_info['symbol']
                    open_time = pos_info['open_time']

                    # Query trade history to get P&L
                    from_date = open_time - timedelta(minutes=1)
                    to_date = datetime.now()
                    history = self.mt5.get_history(from_date, to_date)

                    # Find closing trade for this ticket
                    profit = 0.0
                    for trade in history:
                        if trade.ticket == ticket:
                            profit = trade.profit
                            logger.info(f"Found closed position {ticket}: profit=${profit:.2f}")
                            break

                    # Update stats
                    if symbol in self.stats:
                        self.stats[symbol].total_profit += profit
                        if profit > 0:
                            self.stats[symbol].winning_trades += 1
                        elif profit < 0:
                            self.stats[symbol].losing_trades += 1

                    # Trigger callback with P&L
                    if self.on_close_callback:
                        self.on_close_callback(ticket, profit)

                    logger.info(f"Position closed: ticket={ticket}, symbol={symbol}, profit=${profit:.2f}")

                except Exception as e:
                    logger.error(f"Error processing closed position {ticket}: {e}")

                # Remove from active tracking
                del self._active_positions[ticket]

    async def run_loop(self, interval_seconds: int = 60):
        """
        Main trading loop.
        Runs predictions and executes signals at regular intervals.
        """
        logger.info(f"Auto trading loop started (interval: {interval_seconds}s)")

        while self.running:
            if self.paused:
                await asyncio.sleep(1)
                continue

            try:
                # Check MT5 connection (triggers auto-reconnect if needed)
                if not self.mt5.check_connection():
                    logger.warning("MT5 not connected, skipping iteration")
                    await asyncio.sleep(interval_seconds)
                    continue

                # Check for closed positions
                self._check_closed_positions()

                # Process each active model
                for symbol, model_info in self.models.items():
                    if not self.running:
                        break

                    # Get prediction
                    signal, confidence = self.predict(symbol)

                    # Notify UI
                    if self.on_signal_callback:
                        self.on_signal_callback(symbol, signal, confidence)

                    # Execute if appropriate
                    if signal != Signal.HOLD:
                        self.execute_signal(symbol, signal, confidence)

                    # Small delay between symbols
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.exception(f"Error in trading loop: {e}")
                if self.on_error_callback:
                    self.on_error_callback(str(e))

            # Wait for next iteration
            await asyncio.sleep(interval_seconds)

        logger.info("Auto trading loop stopped")
    
    def start(self, interval_seconds: int = 60):
        """Start the auto trading loop"""
        if self.running:
            logger.warning("Auto trading already running")
            return
        
        if not self.models:
            logger.error("No models loaded, cannot start")
            return
        
        self.running = True
        self._task = asyncio.create_task(self.run_loop(interval_seconds))
        logger.info("Auto trading started")
    
    def stop(self):
        """Stop the auto trading loop"""
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Auto trading stopped")
    
    def pause(self):
        """Pause trading (predictions continue)"""
        self.paused = True
        logger.info("Auto trading paused")
    
    def resume(self):
        """Resume trading"""
        self.paused = False
        logger.info("Auto trading resumed")
    
    def get_status(self) -> dict:
        """Get current auto trader status"""
        return {
            "running": self.running,
            "paused": self.paused,
            "active_models": list(self.models.keys()),
            "stats": {
                symbol: {
                    "total_trades": stats.total_trades,
                    "win_rate": stats.win_rate,
                    "total_profit": stats.total_profit
                }
                for symbol, stats in self.stats.items()
            }
        }
    
    def get_model_info(self, symbol: str) -> Optional[dict]:
        """Get information about a loaded model"""
        if symbol not in self.models:
            return None
        
        info = self.models[symbol]
        return {
            "model_id": info.model_id,
            "symbol": info.symbol,
            "accuracy": info.accuracy,
            "last_prediction": info.last_prediction.value if info.last_prediction else None,
            "last_prediction_time": info.last_prediction_time.isoformat() if info.last_prediction_time else None,
            "total_predictions": info.total_predictions,
            "config": {
                "timeframe": info.config.timeframe,
                "volume": info.config.volume,
                "risk_percent": info.config.risk_percent,
                "confidence_threshold": info.config.confidence_threshold
            }
        }
