"""
BTC XGBoost Optimized Trainer with GridSearchCV
Crypto-specific tuning for maximum win rate
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class BTCXGBoostTrainer:
    """XGBoost trainer optimized for BTC"""
    
    # Crypto features - optimized set
    FEATURES = [
        'rsi', 'rsi_momentum', 'rsi_extreme',
        'macd', 'macd_hist', 'macd_bullish',
        'bb_position', 'bb_width', 'bb_breakout',
        'ema_alignment', 'ema_momentum',
        'atr_pct', 'volatility_high',
        'momentum_1h', 'momentum_4h', 'momentum_dir',
        'volume_surge', 'volume_trend',
        'trend_adx', 'price_strength'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
        self.scaler = StandardScaler()
    
    def load_data(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        print(f"Loading BTC from {path}")
        
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        
        # Use 2 years for better pattern recognition
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate optimized crypto features"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float)
        
        # RSI with patterns
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        f['rsi'] = rsi
        f['rsi_momentum'] = rsi.diff(3)
        f['rsi_extreme'] = ((rsi < 30) | (rsi > 70)).astype(float)
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['macd'] = macd / c * 100
        f['macd_hist'] = (macd - macd_sig) / c * 100
        f['macd_bullish'] = (macd > macd_sig).astype(float)
        
        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_up = sma20 + 2 * std20
        bb_lo = sma20 - 2 * std20
        f['bb_position'] = (c - bb_lo) / (bb_up - bb_lo + 1e-10)
        f['bb_width'] = (bb_up - bb_lo) / sma20
        f['bb_breakout'] = ((c > bb_up) | (c < bb_lo)).astype(float)
        
        # EMA alignment
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        f['ema_alignment'] = ((ema9 > ema21) & (ema21 > ema50)).astype(float) - \
                            ((ema9 < ema21) & (ema21 < ema50)).astype(float)
        f['ema_momentum'] = (c - ema21) / ema21 * 100
        
        # ATR
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        f['atr_pct'] = atr / c * 100
        f['volatility_high'] = (f['atr_pct'] > f['atr_pct'].rolling(50).quantile(0.75)).astype(float)
        
        # Momentum
        f['momentum_1h'] = c.pct_change(4) * 100
        f['momentum_4h'] = c.pct_change(16) * 100
        f['momentum_dir'] = (np.sign(f['momentum_1h']) == np.sign(f['momentum_4h'])).astype(float)
        
        # Volume
        vol_ma = v.rolling(20).mean()
        f['volume_surge'] = (v > vol_ma * 1.5).astype(float)
        f['volume_trend'] = (vol_ma.diff(5) / (vol_ma + 1e-10))
        
        # ADX
        plus_dm = ((h - h.shift()).where((h - h.shift()) > (l.shift() - l), 0)).rolling(14).mean()
        minus_dm = ((l.shift() - l).where((l.shift() - l) > (h - h.shift()), 0)).rolling(14).mean()
        f['trend_adx'] = abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-10)
        
        # Price strength
        high_20 = h.rolling(20).max()
        low_20 = l.rolling(20).min()
        f['price_strength'] = (c - low_20) / (high_20 - low_20 + 1e-10)
        
        # Normalize continuous
        norm_cols = ['rsi', 'rsi_momentum', 'macd', 'macd_hist', 'bb_position', 
                     'bb_width', 'ema_momentum', 'atr_pct', 'momentum_1h', 
                     'momentum_4h', 'volume_trend', 'trend_adx', 'price_strength']
        for col in norm_cols:
            if col in f.columns and f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """Labels with crypto-appropriate thresholds"""
        c = df['close'].astype(float)
        
        look_ahead = 8  # 2 hours
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # Threshold 0.4% for crypto
        threshold = 0.4
        
        labels = pd.Series(1, index=df.index)
        labels[future_ret > threshold] = 2
        labels[future_ret < -threshold] = 0
        
        return labels
    
    def train(self) -> dict:
        print(f"\n{'='*60}")
        print("BTC XGBoost Optimized Training")
        print("="*60)
        
        df = self.load_data()
        features = self.calc_features(df)
        labels = self.create_labels(df)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"\nSamples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"Labels: SELL={lc.get(0,0)} | HOLD={lc.get(1,0)} | BUY={lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("\n📊 Hyperparameter Tuning...")
        
        param_grid = {
            'max_depth': [5, 7, 10],
            'n_estimators': [100, 150, 200],
            'learning_rate': [0.03, 0.05, 0.1],
            'min_child_weight': [3, 5, 7],
            'subsample': [0.8],
            'colsample_bytree': [0.8],
            'scale_pos_weight': [1, 2]  # Handle class imbalance
        }
        
        base = xgb.XGBClassifier(
            objective='multi:softprob',
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        
        tscv = TimeSeriesSplit(n_splits=3)
        grid = GridSearchCV(base, param_grid, cv=tscv, scoring='accuracy', n_jobs=-1, verbose=1)
        grid.fit(X_train_scaled, y_train)
        
        print(f"\n✅ Best params: {grid.best_params_}")
        print(f"   Best CV: {grid.best_score_:.2%}")
        
        model = grid.best_estimator_
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        print("\n📈 Win Rate Analysis:")
        best_wr, best_thresh, best_trades = 0, 0.5, 0
        
        for t in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= t
            trades = (y_pred != 1) & conf
            
            if trades.sum() > 0:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                pct = trades.sum() / len(y_test) * 100
                print(f"  Threshold {t:.0%}: Win {wr:.1f}%, Trades {trades.sum()} ({pct:.1f}%)")
                
                if wr > best_wr and trades.sum() > 15:
                    best_wr, best_thresh, best_trades = wr, t, trades.sum()
        
        # Precision per class at best threshold
        max_p = np.max(y_proba, axis=1)
        conf = max_p >= best_thresh
        
        buy_mask = (y_pred == 2) & conf
        sell_mask = (y_pred == 0) & conf
        
        buy_prec = ((y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100) if buy_mask.sum() > 0 else 0
        sell_prec = ((y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100) if sell_mask.sum() > 0 else 0
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print("📊 FINAL RESULTS")
        print("="*60)
        print(f"  Accuracy: {acc:.1%}")
        print(f"  Win Rate: {best_wr:.1f}%")
        print(f"  BUY Precision: {buy_prec:.1f}%")
        print(f"  SELL Precision: {sell_prec:.1f}%")
        print(f"  Threshold: {best_thresh:.0%}")
        print(f"  Trades: {best_trades}")
        
        return {
            'model': model,
            'scaler': self.scaler,
            'best_params': {k: int(v) if isinstance(v, (np.integer,)) else float(v) if isinstance(v, (np.floating,)) else v for k, v in grid.best_params_.items()},
            'metrics': {
                'accuracy': float(acc),
                'win_rate': float(best_wr),
                'buy_precision': float(buy_prec),
                'sell_precision': float(sell_prec),
                'threshold': float(best_thresh),
                'trades': int(best_trades),
                'cv_score': float(grid.best_score_)
            }
        }
    
    def save(self, result: dict) -> str:
        model_id = f"btcusd_xgb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost',
            'strategy': 'crypto-optimized',
            'confidence_threshold': result['metrics']['threshold'],
            'best_params': result['best_params']
        }
        
        meta = {
            'symbol': 'BTCUSD',
            'version': 'xgboost_tuned_v1',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Saved: {model_id}")
        print(f"   Path: {path}")
        return model_id
    
    def run(self):
        result = self.train()
        model_id = self.save(result)
        return {'model_id': model_id, **result['metrics']}


if __name__ == "__main__":
    print("="*60)
    print("BTC XGBoost Optimized Training")
    print("="*60)
    
    trainer = BTCXGBoostTrainer()
    result = trainer.run()
    
    print(f"\n{'='*60}")
    print("✅ COMPLETE")
    print("="*60)
    print(f"Model: {result['model_id']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
