"""
Train ML Models with OHLCV Data
Optimized for high win rate using real historical data
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class OHLCVModelTrainer:
    """Train models using OHLCV CSV data with optimized win rate"""
    
    FEATURE_COLUMNS = [
        'rsi', 'rsi_ma', 'macd', 'macd_signal', 'macd_hist',
        'bb_width', 'bb_position', 'ema_cross', 'ema_distance',
        'atr_percent', 'price_change', 'price_change_5', 'price_change_10',
        'momentum', 'roc', 'volume_ratio'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
        self.scaler = StandardScaler()
    
    def load_btc_data(self) -> pd.DataFrame:
        """Load BTC 15m data"""
        file_path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        print(f"Loading BTC data from {file_path}...")
        
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        
        # Rename columns
        df = df.rename(columns={
            'open_time': 'time',
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        })
        
        # Parse time
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        
        # Use only last 2 years for more relevant patterns
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"BTC data: {len(df)} rows from {df['time'].min()} to {df['time'].max()}")
        return df
    
    def load_xauusd_data(self) -> pd.DataFrame:
        """Load XAUUSD 15m data"""
        file_path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
        print(f"Loading XAUUSD data from {file_path}...")
        
        df = pd.read_csv(file_path, sep=';')
        df.columns = [c.strip().lower() for c in df.columns]
        
        # Rename
        df = df.rename(columns={'date': 'time'})
        
        # Parse time
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        
        # Use last 2 years
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"XAUUSD data: {len(df)} rows from {df['time'].min()} to {df['time'].max()}")
        return df
    
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators with more features"""
        features = pd.DataFrame(index=df.index)
        
        close = df['close'].astype(float)
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        volume = df['volume'].astype(float) if 'volume' in df.columns else pd.Series(1, index=df.index)
        
        # RSI (14) with smoothing
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-10)
        features['rsi'] = 100 - (100 / (1 + rs))
        features['rsi_ma'] = features['rsi'].rolling(5).mean()
        
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
        features['bb_width'] = (bb_upper - bb_lower) / (sma20 + 1e-10)
        features['bb_position'] = (close - bb_lower) / (bb_upper - bb_lower + 1e-10)
        
        # EMAs with distance
        ema_9 = close.ewm(span=9, adjust=False).mean()
        ema_21 = close.ewm(span=21, adjust=False).mean()
        features['ema_cross'] = (ema_9 - ema_21) / (close + 1e-10)
        features['ema_distance'] = (close - ema_21) / (close + 1e-10)
        
        # ATR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        features['atr_percent'] = atr / (close + 1e-10) * 100
        
        # Price momentum
        features['price_change'] = close.pct_change() * 100
        features['price_change_5'] = close.pct_change(5) * 100
        features['price_change_10'] = close.pct_change(10) * 100
        features['momentum'] = close - close.shift(10)
        features['roc'] = (close / close.shift(10) - 1) * 100
        
        # Volume
        volume_ma = volume.rolling(20).mean()
        features['volume_ratio'] = volume / (volume_ma + 1e-10)
        
        return features
    
    def create_labels(
        self, 
        df: pd.DataFrame, 
        future_periods: int = 8,
        threshold_pct: float = 0.15
    ) -> pd.Series:
        """
        Create labels with configurable threshold
        Higher threshold = more confident signals = better win rate
        
        Labels: 0=SELL, 1=HOLD, 2=BUY
        """
        close = df['close'].astype(float)
        future_return = (close.shift(-future_periods) / close - 1) * 100
        
        threshold = threshold_pct
        
        labels = pd.Series(1, index=df.index)  # HOLD
        labels[future_return > threshold] = 2   # BUY
        labels[future_return < -threshold] = 0  # SELL
        
        return labels
    
    def train_model(
        self,
        symbol: str,
        df: pd.DataFrame,
        future_periods: int = 8,
        threshold_pct: float = 0.15
    ) -> dict:
        """Train model with optimizations for win rate"""
        
        print(f"\n{'='*60}")
        print(f"Training {symbol} model")
        print(f"{'='*60}")
        
        # Calculate features
        features = self.calculate_features(df)
        labels = self.create_labels(df, future_periods, threshold_pct)
        
        # Combine and clean
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"Total samples: {len(data)}")
        
        # Label distribution
        label_counts = data['label'].value_counts().sort_index()
        print(f"Label distribution: SELL={label_counts.get(0, 0)}, HOLD={label_counts.get(1, 0)}, BUY={label_counts.get(2, 0)}")
        
        X = data[self.FEATURE_COLUMNS].values
        y = data['label'].values
        
        # Time series split (more realistic)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False  # No shuffle for time series
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train with optimized parameters for win rate
        print("Training Random Forest...")
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=50,
            min_samples_leaf=20,
            class_weight='balanced',  # Handle imbalanced classes
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        # Predictions
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        # Only count high-confidence predictions for win rate
        confidence_threshold = 0.55
        confident_mask = np.max(y_proba, axis=1) >= confidence_threshold
        
        if confident_mask.sum() > 0:
            y_test_conf = y_test[confident_mask]
            y_pred_conf = y_pred[confident_mask]
            confident_accuracy = accuracy_score(y_test_conf, y_pred_conf)
            
            # Win rate for actual trades (BUY or SELL, not HOLD)
            trade_mask = confident_mask & (y_pred != 1)  # Exclude HOLD
            if trade_mask.sum() > 0:
                trade_correct = (y_test[trade_mask] == y_pred[trade_mask]).sum()
                trade_total = trade_mask.sum()
                win_rate = trade_correct / trade_total * 100
            else:
                win_rate = 0
        else:
            confident_accuracy = 0
            win_rate = 0
        
        # Overall metrics
        overall_accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=tscv)
        
        print(f"\nResults:")
        print(f"  Overall Accuracy: {overall_accuracy:.2%}")
        print(f"  Confident Accuracy (>{confidence_threshold:.0%}): {confident_accuracy:.2%}")
        print(f"  Trade Win Rate: {win_rate:.1f}%")
        print(f"  CV Score: {cv_scores.mean():.2%} ± {cv_scores.std():.2%}")
        print(f"  Confident Signals: {confident_mask.sum()} / {len(y_test)}")
        
        # Classification report
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['SELL', 'HOLD', 'BUY']))
        
        # Feature importance
        importance = dict(zip(self.FEATURE_COLUMNS, model.feature_importances_))
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\nTop 5 Important Features:")
        for feat, imp in top_features:
            print(f"  {feat}: {imp:.4f}")
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': {
                'overall_accuracy': float(overall_accuracy),
                'confident_accuracy': float(confident_accuracy),
                'win_rate': float(win_rate),
                'cv_mean': float(cv_scores.mean()),
                'cv_std': float(cv_scores.std()),
                'confident_signals': int(confident_mask.sum()),
                'total_samples': len(y_test),
                'threshold_pct': threshold_pct,
                'future_periods': future_periods
            },
            'feature_importance': importance
        }
    
    def save_model(self, result: dict, symbol: str) -> str:
        """Save trained model with encryption"""
        model_id = f"{symbol.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Package model with scaler
        model_package = {
            'model': result['model'],
            'scaler': result['scaler'],
            'feature_columns': self.FEATURE_COLUMNS
        }
        
        metadata = {
            'symbol': symbol,
            'accuracy': result['metrics']['overall_accuracy'],
            'win_rate': result['metrics']['win_rate'],
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(model_package, model_id, metadata)
        path = self.security.save_secured_model(secured)
        
        print(f"\nModel saved: {model_id}")
        print(f"Location: {path}")
        
        return model_id
    
    def train_all(self):
        """Train models for BTC and XAUUSD"""
        results = {}
        
        # Train BTC
        print("\n" + "="*60)
        print("TRAINING BTCUSD MODEL")
        print("="*60)
        try:
            btc_df = self.load_btc_data()
            btc_result = self.train_model(
                "BTCUSD", 
                btc_df,
                future_periods=8,   # 2 hours ahead (8 * 15min)
                threshold_pct=0.3   # 0.3% threshold for BTC
            )
            model_id = self.save_model(btc_result, "BTCUSD")
            results['BTCUSD'] = {
                'model_id': model_id,
                'win_rate': btc_result['metrics']['win_rate'],
                'accuracy': btc_result['metrics']['confident_accuracy']
            }
        except Exception as e:
            print(f"BTC training failed: {e}")
            import traceback
            traceback.print_exc()
            results['BTCUSD'] = {'error': str(e)}
        
        # Train XAUUSD
        print("\n" + "="*60)
        print("TRAINING XAUUSD MODEL")
        print("="*60)
        try:
            xau_df = self.load_xauusd_data()
            xau_result = self.train_model(
                "XAUUSD",
                xau_df,
                future_periods=8,   # 2 hours ahead
                threshold_pct=0.1   # 0.1% threshold for Gold
            )
            model_id = self.save_model(xau_result, "XAUUSD")
            results['XAUUSD'] = {
                'model_id': model_id,
                'win_rate': xau_result['metrics']['win_rate'],
                'accuracy': xau_result['metrics']['confident_accuracy']
            }
        except Exception as e:
            print(f"XAUUSD training failed: {e}")
            import traceback
            traceback.print_exc()
            results['XAUUSD'] = {'error': str(e)}
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("NexusTrade ML Model Training")
    print("Using OHLCV Historical Data")
    print("="*60)
    
    trainer = OHLCVModelTrainer()
    results = trainer.train_all()
    
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    for symbol, data in results.items():
        if 'error' in data:
            print(f"❌ {symbol}: FAILED - {data['error']}")
        else:
            print(f"✅ {symbol}:")
            print(f"   Model ID: {data['model_id']}")
            print(f"   Win Rate: {data['win_rate']:.1f}%")
            print(f"   Accuracy: {data['accuracy']:.1%}")
