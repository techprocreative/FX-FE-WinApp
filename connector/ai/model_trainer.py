"""
ML Model Trainer
Train Random Forest models for BTCUSD and XAUUSD trading signals
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from loguru import logger

# For data fetching without MT5 connection
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

from security.model_security import ModelSecurity


class ModelTrainer:
    """
    Train ML models for trading signal prediction.
    Supports BTCUSD and XAUUSD with technical indicators.
    """
    
    # Feature columns used for training
    FEATURE_COLUMNS = [
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'bb_width', 'bb_position',
        'ema_cross', 'atr_percent',
        'price_change', 'price_change_5'
    ]
    
    # Default training parameters
    DEFAULT_PARAMS = {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 20,
        'min_samples_leaf': 10,
        'random_state': 42,
        'n_jobs': -1
    }
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path.home() / ".nexustrade" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.security = ModelSecurity(self.models_dir)
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = "M15",
        days: int = 90
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data from MT5.
        
        Args:
            symbol: Trading symbol (BTCUSD, XAUUSD)
            timeframe: Timeframe string (M1, M5, M15, H1, etc.)
            days: Number of days of history
        
        Returns:
            DataFrame with OHLC data
        """
        if not MT5_AVAILABLE:
            logger.warning("MT5 not available, using sample data")
            return self._generate_sample_data(symbol, days)
        
        # Initialize MT5 if needed
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return self._generate_sample_data(symbol, days)
        
        # Timeframe mapping
        tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }
        
        mt5_tf = tf_map.get(timeframe.upper(), mt5.TIMEFRAME_M15)
        
        # Calculate bars needed
        bars_per_day = {
            'M1': 1440, 'M5': 288, 'M15': 96,
            'M30': 48, 'H1': 24, 'H4': 6, 'D1': 1
        }
        count = days * bars_per_day.get(timeframe.upper(), 96)
        
        # Fetch data
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
        
        if rates is None or len(rates) == 0:
            logger.warning(f"No data for {symbol}, using sample data")
            return self._generate_sample_data(symbol, days)
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'tick_volume': 'volume'})
        
        logger.info(f"Fetched {len(df)} bars for {symbol}")
        return df
    
    def _generate_sample_data(
        self, 
        symbol: str, 
        days: int = 90
    ) -> pd.DataFrame:
        """Generate sample OHLC data for testing when MT5 is not available"""
        np.random.seed(42)
        
        # Base price based on symbol
        if 'BTC' in symbol.upper():
            base_price = 45000
            volatility = 500
        elif 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
            base_price = 2000
            volatility = 10
        else:
            base_price = 1.1
            volatility = 0.001
        
        # Generate bars (M15)
        bars = days * 96
        dates = pd.date_range(end=datetime.now(), periods=bars, freq='15min')
        
        # Random walk
        returns = np.random.randn(bars) * volatility / 100
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'time': dates,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.randn(bars)) * 0.001),
            'low': prices * (1 - np.abs(np.random.randn(bars)) * 0.001),
            'close': prices * (1 + np.random.randn(bars) * 0.0005),
            'volume': np.random.randint(100, 10000, bars)
        })
        
        logger.info(f"Generated {len(df)} sample bars for {symbol}")
        return df
    
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicator features.
        
        Returns DataFrame with normalized features.
        """
        features = pd.DataFrame(index=df.index)
        
        close = df['close']
        high = df['high']
        low = df['low']
        
        # RSI (14)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
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
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)
        features['bb_width'] = (bb_upper - bb_lower) / sma20
        features['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower)
        
        # EMAs
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        features['ema_cross'] = (ema_9 - ema_21) / close
        
        # ATR (14)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        features['atr_percent'] = atr / close * 100
        
        # Price changes
        features['price_change'] = close.pct_change() * 100
        features['price_change_5'] = close.pct_change(5) * 100
        
        # Normalize
        for col in features.columns:
            if features[col].std() > 0:
                features[col] = (features[col] - features[col].mean()) / features[col].std()
        
        return features
    
    def create_labels(
        self, 
        df: pd.DataFrame, 
        future_periods: int = 5,
        threshold: float = 0.002
    ) -> pd.Series:
        """
        Create trading labels based on future price movement.
        
        Labels:
            0 = SELL (price goes down)
            1 = HOLD (price stays flat)
            2 = BUY (price goes up)
        """
        future_return = df['close'].shift(-future_periods) / df['close'] - 1
        
        labels = pd.Series(1, index=df.index)  # Default HOLD
        labels[future_return > threshold] = 2   # BUY
        labels[future_return < -threshold] = 0  # SELL
        
        return labels
    
    def train(
        self,
        symbol: str,
        timeframe: str = "M15",
        days: int = 90,
        future_periods: int = 5,
        threshold: float = 0.002,
        params: Optional[Dict] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Train a Random Forest model for the given symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: OHLC timeframe
            days: Days of historical data
            future_periods: Periods to look ahead for labels
            threshold: Price change threshold for buy/sell
            params: Model hyperparameters
        
        Returns:
            (trained_model, metrics_dict)
        """
        logger.info(f"Training model for {symbol} ({timeframe})...")
        
        # Fetch data
        df = self.fetch_historical_data(symbol, timeframe, days)
        if df is None or df.empty:
            raise ValueError(f"No data available for {symbol}")
        
        # Calculate features
        features = self.calculate_features(df)
        
        # Create labels
        labels = self.create_labels(df, future_periods, threshold)
        
        # Align and drop NaN
        data = pd.concat([features, labels.rename('label')], axis=1).dropna()
        
        if len(data) < 100:
            raise ValueError(f"Insufficient data: {len(data)} rows")
        
        X = data[self.FEATURE_COLUMNS].values
        y = data['label'].values
        
        # Split data (80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        model_params = {**self.DEFAULT_PARAMS, **(params or {})}
        model = RandomForestClassifier(**model_params)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X, y, cv=5)
        
        # Calculate class distribution
        unique, counts = np.unique(y, return_counts=True)
        label_dist = dict(zip(unique.astype(int), counts.astype(int)))
        
        metrics = {
            'accuracy': float(accuracy),
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'label_distribution': label_dist,
            'feature_importance': dict(zip(
                self.FEATURE_COLUMNS,
                model.feature_importances_.tolist()
            ))
        }
        
        logger.info(f"Model trained: accuracy={accuracy:.2%}, CV={cv_scores.mean():.2%}±{cv_scores.std():.2%}")
        
        return model, metrics
    
    def save_encrypted(
        self,
        model: Any,
        symbol: str,
        metrics: Dict[str, Any],
        description: str = ""
    ) -> str:
        """
        Save model with encryption.
        
        Returns:
            model_id
        """
        model_id = f"{symbol.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metadata = {
            'symbol': symbol,
            'accuracy': metrics.get('accuracy', 0),
            'cv_mean': metrics.get('cv_mean', 0),
            'trained_at': datetime.now().isoformat(),
            'description': description,
            'feature_columns': self.FEATURE_COLUMNS
        }
        
        # Encrypt and save
        secured = self.security.encrypt_model(model, model_id, metadata)
        path = self.security.save_secured_model(secured)
        
        logger.info(f"Model saved: {model_id} at {path}")
        return model_id
    
    def train_and_save(
        self,
        symbol: str,
        timeframe: str = "M15",
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Train model and save encrypted.
        
        Returns:
            (model_id, metrics)
        """
        model, metrics = self.train(symbol, timeframe, **kwargs)
        model_id = self.save_encrypted(model, symbol, metrics)
        return model_id, metrics


def train_demo_models():
    """Train models for BTC and XAU demo"""
    trainer = ModelTrainer()
    
    results = {}
    
    # Train BTCUSD
    logger.info("=" * 50)
    logger.info("Training BTCUSD model...")
    try:
        model_id, metrics = trainer.train_and_save(
            symbol="BTCUSD",
            timeframe="M15",
            days=90,
            future_periods=5,
            threshold=0.003  # 0.3% for BTC
        )
        results['BTCUSD'] = {'model_id': model_id, 'metrics': metrics}
        logger.info(f"BTCUSD model: {model_id}, accuracy: {metrics['accuracy']:.2%}")
    except Exception as e:
        logger.exception(f"Failed to train BTCUSD: {e}")
        results['BTCUSD'] = {'error': str(e)}
    
    # Train XAUUSD
    logger.info("=" * 50)
    logger.info("Training XAUUSD model...")
    try:
        model_id, metrics = trainer.train_and_save(
            symbol="XAUUSD",
            timeframe="M15",
            days=90,
            future_periods=5,
            threshold=0.001  # 0.1% for Gold
        )
        results['XAUUSD'] = {'model_id': model_id, 'metrics': metrics}
        logger.info(f"XAUUSD model: {model_id}, accuracy: {metrics['accuracy']:.2%}")
    except Exception as e:
        logger.exception(f"Failed to train XAUUSD: {e}")
        results['XAUUSD'] = {'error': str(e)}
    
    logger.info("=" * 50)
    logger.info("Training complete!")
    
    return results


if __name__ == "__main__":
    # Setup logging
    logger.add("logs/training_{time}.log", rotation="10 MB")
    
    # Train demo models
    results = train_demo_models()
    
    # Print summary
    print("\n" + "=" * 50)
    print("TRAINING SUMMARY")
    print("=" * 50)
    for symbol, data in results.items():
        if 'error' in data:
            print(f"{symbol}: FAILED - {data['error']}")
        else:
            print(f"{symbol}: {data['model_id']}")
            print(f"  Accuracy: {data['metrics']['accuracy']:.2%}")
            print(f"  CV Score: {data['metrics']['cv_mean']:.2%} ± {data['metrics']['cv_std']:.2%}")
