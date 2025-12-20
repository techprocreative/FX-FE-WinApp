"""
BTC Multi-Model Trainer
Compares XGBoost, LSTM, Random Forest, Gradient Boosting
Finds the best model for cryptocurrency trading
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# Try to import TensorFlow for LSTM
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False
    print("TensorFlow not available, skipping LSTM")

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class BTCMultiModelTrainer:
    """
    Train and compare multiple models for BTC
    """
    
    # Crypto-specific features
    FEATURES = [
        'rsi', 'rsi_divergence', 'rsi_momentum',
        'macd', 'macd_signal', 'macd_hist', 'macd_cross',
        'bb_position', 'bb_width', 'bb_breakout',
        'ema_trend', 'ema_momentum', 'ema_alignment',
        'atr_pct', 'volatility_regime',
        'momentum_1h', 'momentum_4h', 'momentum_12h',
        'volume_ratio', 'volume_trend',
        'trend_strength', 'price_position'
    ]
    
    LOOKBACK = 20  # For LSTM
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
        self.scaler = StandardScaler()
    
    def load_data(self) -> pd.DataFrame:
        """Load BTC data"""
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        print(f"Loading BTC from {path}")
        
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        
        # Use last 1.5 years
        cutoff = df['time'].max() - pd.Timedelta(days=540)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows ({df['time'].min().date()} to {df['time'].max().date()})")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate crypto-specific features"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float)
        
        # RSI (14) with divergence
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        f['rsi'] = rsi
        f['rsi_divergence'] = rsi.diff(5) - c.pct_change(5) * 100  # Price/RSI divergence
        f['rsi_momentum'] = rsi.diff(3)
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['macd'] = macd / c * 100
        f['macd_signal'] = macd_sig / c * 100
        f['macd_hist'] = (macd - macd_sig) / c * 100
        f['macd_cross'] = ((macd > macd_sig) != (macd.shift(1) > macd_sig.shift(1))).astype(float)
        
        # Bollinger Bands with breakout
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_up = sma20 + 2 * std20
        bb_lo = sma20 - 2 * std20
        f['bb_position'] = (c - bb_lo) / (bb_up - bb_lo + 1e-10)
        f['bb_width'] = (bb_up - bb_lo) / sma20
        f['bb_breakout'] = ((c > bb_up) | (c < bb_lo)).astype(float)
        
        # EMA trend
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        f['ema_trend'] = np.sign(ema9 - ema21)
        f['ema_momentum'] = (c - ema21) / ema21 * 100
        f['ema_alignment'] = ((ema9 > ema21) & (ema21 > ema50)).astype(float) - \
                            ((ema9 < ema21) & (ema21 < ema50)).astype(float)
        
        # ATR and volatility
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        f['atr_pct'] = atr / c * 100
        f['volatility_regime'] = (f['atr_pct'] > f['atr_pct'].rolling(50).quantile(0.7)).astype(float)
        
        # Multi-timeframe momentum
        f['momentum_1h'] = c.pct_change(4) * 100
        f['momentum_4h'] = c.pct_change(16) * 100
        f['momentum_12h'] = c.pct_change(48) * 100
        
        # Volume
        vol_ma = v.rolling(20).mean()
        f['volume_ratio'] = v / (vol_ma + 1e-10)
        f['volume_trend'] = vol_ma.diff(5) / (vol_ma + 1e-10)
        
        # Trend strength
        plus_dm = ((h - h.shift()).where((h - h.shift()) > (l.shift() - l), 0)).rolling(14).mean()
        minus_dm = ((l.shift() - l).where((l.shift() - l) > (h - h.shift()), 0)).rolling(14).mean()
        f['trend_strength'] = abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-10)
        
        # Price position in range
        high_20 = h.rolling(20).max()
        low_20 = l.rolling(20).min()
        f['price_position'] = (c - low_20) / (high_20 - low_20 + 1e-10)
        
        # Normalize
        for col in f.columns:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """Create trading labels for BTC"""
        c = df['close'].astype(float)
        
        # Look 6 bars ahead (1.5 hours)
        look_ahead = 6
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # BTC threshold: 0.5% (significant move for crypto)
        threshold = 0.5
        
        labels = pd.Series(1, index=df.index)  # HOLD
        labels[future_ret > threshold] = 2     # BUY
        labels[future_ret < -threshold] = 0    # SELL
        
        return labels
    
    def prepare_lstm_data(self, X: np.ndarray, y: np.ndarray):
        """Prepare sequences for LSTM"""
        X_seq, y_seq = [], []
        for i in range(self.LOOKBACK, len(X)):
            X_seq.append(X[i-self.LOOKBACK:i])
            y_seq.append(y[i])
        return np.array(X_seq), np.array(y_seq)
    
    def build_lstm_model(self, input_shape):
        """Build LSTM model"""
        model = Sequential([
            LSTM(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')
        ])
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        return model
    
    def train_and_compare(self) -> dict:
        """Train all models and compare"""
        print(f"\n{'='*60}")
        print("BTC Multi-Model Comparison")
        print("="*60)
        
        # Load data
        df = self.load_data()
        features = self.calc_features(df)
        labels = self.create_labels(df)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"\nTotal samples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"Labels: SELL={lc.get(0,0)} | HOLD={lc.get(1,0)} | BUY={lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {}
        
        # 1. XGBoost
        print("\n📊 Training XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=7,
            learning_rate=0.05,
            min_child_weight=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        xgb_model.fit(X_train_scaled, y_train)
        xgb_pred = xgb_model.predict(X_test_scaled)
        xgb_proba = xgb_model.predict_proba(X_test_scaled)
        results['XGBoost'] = self._evaluate(y_test, xgb_pred, xgb_proba, xgb_model)
        
        # 2. Gradient Boosting
        print("\n📊 Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            min_samples_split=50,
            subsample=0.8,
            random_state=42
        )
        gb_model.fit(X_train_scaled, y_train)
        gb_pred = gb_model.predict(X_test_scaled)
        gb_proba = gb_model.predict_proba(X_test_scaled)
        results['GradientBoosting'] = self._evaluate(y_test, gb_pred, gb_proba, gb_model)
        
        # 3. Random Forest
        print("\n📊 Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=30,
            min_samples_leaf=15,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        rf_pred = rf_model.predict(X_test_scaled)
        rf_proba = rf_model.predict_proba(X_test_scaled)
        results['RandomForest'] = self._evaluate(y_test, rf_pred, rf_proba, rf_model)
        
        # 4. LSTM (if available)
        if LSTM_AVAILABLE:
            print("\n📊 Training LSTM...")
            X_lstm_train, y_lstm_train = self.prepare_lstm_data(X_train_scaled, y_train)
            X_lstm_test, y_lstm_test = self.prepare_lstm_data(X_test_scaled, y_test)
            
            lstm_model = self.build_lstm_model((self.LOOKBACK, len(self.FEATURES)))
            
            early_stop = EarlyStopping(patience=5, restore_best_weights=True, verbose=0)
            
            lstm_model.fit(
                X_lstm_train, y_lstm_train,
                epochs=30,
                batch_size=64,
                validation_split=0.1,
                callbacks=[early_stop],
                verbose=0
            )
            
            lstm_proba = lstm_model.predict(X_lstm_test, verbose=0)
            lstm_pred = np.argmax(lstm_proba, axis=1)
            results['LSTM'] = self._evaluate(y_lstm_test, lstm_pred, lstm_proba, lstm_model)
        
        # Compare results
        print(f"\n{'='*60}")
        print("📈 MODEL COMPARISON")
        print("="*60)
        print(f"{'Model':<20} {'Accuracy':>10} {'Win Rate':>10} {'Trades':>10}")
        print("-"*50)
        
        best_model = None
        best_win_rate = 0
        
        for name, res in results.items():
            print(f"{name:<20} {res['accuracy']:>9.1%} {res['win_rate']:>9.1f}% {res['trades']:>10}")
            if res['win_rate'] > best_win_rate and res['trades'] > 20:
                best_win_rate = res['win_rate']
                best_model = name
        
        print(f"\n🏆 Best Model: {best_model} (Win Rate: {best_win_rate:.1f}%)")
        
        return results, best_model
    
    def _evaluate(self, y_true, y_pred, y_proba, model) -> dict:
        """Evaluate model with win rate analysis"""
        acc = accuracy_score(y_true, y_pred)
        
        # Find best threshold for win rate
        best_wr = 0
        best_thresh = 0.5
        best_trades = 0
        
        for thresh in [0.40, 0.45, 0.50, 0.55, 0.60]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= thresh
            trades = (y_pred != 1) & conf
            
            if trades.sum() > 0:
                correct = (y_true[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                
                if wr > best_wr and trades.sum() > 20:
                    best_wr = wr
                    best_thresh = thresh
                    best_trades = trades.sum()
        
        return {
            'model': model,
            'accuracy': acc,
            'win_rate': best_wr,
            'trades': best_trades,
            'threshold': best_thresh
        }
    
    def train_best(self) -> dict:
        """Train and save the best model"""
        results, best_name = self.train_and_compare()
        
        if best_name is None:
            print("No suitable model found!")
            return None
        
        best = results[best_name]
        model_id = f"btcusd_{best_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # For LSTM, we need special handling
        if best_name == 'LSTM':
            # Save LSTM as h5 separately (can't pickle)
            lstm_path = Path.home() / ".nexustrade" / "models" / f"{model_id}.h5"
            best['model'].save(lstm_path)
            
            pkg = {
                'model_path': str(lstm_path),
                'model_type': 'lstm',
                'scaler': self.scaler,
                'features': self.FEATURES,
                'lookback': self.LOOKBACK,
                'confidence_threshold': best['threshold']
            }
        else:
            pkg = {
                'model': best['model'],
                'scaler': self.scaler,
                'features': self.FEATURES,
                'model_type': best_name.lower(),
                'confidence_threshold': best['threshold']
            }
        
        meta = {
            'symbol': 'BTCUSD',
            'model_type': best_name,
            'accuracy': best['accuracy'],
            'win_rate': best['win_rate'],
            'confidence_threshold': best['threshold'],
            'trained_at': datetime.now().isoformat()
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Best Model Saved: {model_id}")
        print(f"   Type: {best_name}")
        print(f"   Win Rate: {best['win_rate']:.1f}%")
        print(f"   Path: {path}")
        
        return {
            'model_id': model_id,
            'model_type': best_name,
            'win_rate': best['win_rate'],
            'accuracy': best['accuracy']
        }


if __name__ == "__main__":
    print("="*60)
    print("BTC Multi-Model Training")
    print("Finding the Best Model for Cryptocurrency Trading")
    print("="*60)
    
    trainer = BTCMultiModelTrainer()
    result = trainer.train_best()
    
    if result:
        print(f"\n{'='*60}")
        print("✅ TRAINING COMPLETE")
        print("="*60)
        print(f"Model: {result['model_id']}")
        print(f"Type: {result['model_type']}")
        print(f"Win Rate: {result['win_rate']:.1f}%")
