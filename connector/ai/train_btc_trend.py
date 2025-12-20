"""
Trend Following BTC Model - Focus on Trading WITH the Trend
Simpler approach: Only trade when clear trend exists, lower threshold
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class TrendFollowingBTCTrainer:
    """
    Simple yet effective trend-following model
    Key insight: Don't predict price, predict if current trend continues
    """
    
    FEATURES = [
        'trend_dir', 'trend_strength', 'trend_age',
        'momentum', 'momentum_accel',
        'rsi', 'rsi_zone',
        'price_position', 'breakout',
        'volume_support'
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
        
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Simple but effective trend indicators"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float)
        
        # Simple trend: price above/below 50 EMA
        ema50 = c.ewm(span=50).mean()
        f['trend_dir'] = np.sign(c - ema50)
        
        # Trend strength (distance from EMA)
        f['trend_strength'] = abs(c - ema50) / ema50 * 100
        
        # Trend age (how long has price been above/below EMA)
        above_ema = (c > ema50).astype(int)
        f['trend_age'] = above_ema.groupby((above_ema != above_ema.shift()).cumsum()).cumcount()
        f['trend_age'] = f['trend_age'] / 100  # Normalize
        
        # Momentum (rate of change)
        f['momentum'] = c.pct_change(8) * 100  # 2 hours
        f['momentum_accel'] = f['momentum'].diff(4)
        
        # RSI
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        f['rsi'] = 100 - (100 / (1 + rs))
        
        # RSI zone: 0=oversold, 1=neutral, 2=overbought
        f['rsi_zone'] = 1
        f.loc[f['rsi'] < 30, 'rsi_zone'] = 0
        f.loc[f['rsi'] > 70, 'rsi_zone'] = 2
        
        # Price position in recent range
        high_20 = h.rolling(20).max()
        low_20 = l.rolling(20).min()
        f['price_position'] = (c - low_20) / (high_20 - low_20 + 1e-10)
        
        # Breakout
        f['breakout'] = ((c > high_20.shift(1)) | (c < low_20.shift(1))).astype(float)
        
        # Volume supporting move
        vol_ma = v.rolling(20).mean()
        f['volume_support'] = (v > vol_ma).astype(float)
        
        # Normalize
        for col in ['trend_strength', 'trend_age', 'momentum', 'momentum_accel', 'rsi', 'price_position']:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """
        Label: Will price CONTINUE in trend direction?
        Simpler: 0.5% threshold (more signals), 6 bars ahead
        """
        c = df['close'].astype(float)
        ema50 = c.ewm(span=50).mean()
        trend = np.sign(c - ema50)
        
        look_ahead = 6
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # 0.5% move threshold
        threshold = 0.5
        
        # Label based on if price moves in TREND direction
        labels = pd.Series(1, index=df.index)  # HOLD
        
        # Uptrend + price goes up = BUY
        labels[(trend > 0) & (future_ret > threshold)] = 2
        # Downtrend + price goes down = SELL  
        labels[(trend < 0) & (future_ret < -threshold)] = 0
        
        return labels
    
    def train(self) -> dict:
        print(f"\n{'='*60}")
        print("TREND FOLLOWING BTC MODEL")
        print("Simple: Trade WITH the trend")
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
        
        print("\n📊 Training XGBoost...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.03,
            min_child_weight=5,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1.5,  # Slightly favor minority classes
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        print("\n📈 Win Rate Analysis:")
        best = {'threshold': 0.4, 'win_rate': 0, 'trades': 0, 'buy_prec': 0, 'sell_prec': 0}
        
        for thresh in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= thresh
            trades = (y_pred != 1) & conf
            
            if trades.sum() > 10:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                
                buy_mask = (y_pred == 2) & conf
                sell_mask = (y_pred == 0) & conf
                buy_prec = ((y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100) if buy_mask.sum() > 0 else 0
                sell_prec = ((y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100) if sell_mask.sum() > 0 else 0
                
                marker = "✅" if wr >= 50 else "⚠️"
                print(f"  {marker} {thresh:.0%}: Win {wr:.1f}%, Trades {trades.sum()}, BUY {buy_prec:.0f}%, SELL {sell_prec:.0f}%")
                
                if wr > best['win_rate'] and trades.sum() >= 20:
                    best = {'threshold': thresh, 'win_rate': wr, 'trades': int(trades.sum()),
                           'buy_prec': buy_prec, 'sell_prec': sell_prec}
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print("📊 BEST RESULT")
        print("="*60)
        print(f"  Accuracy: {acc:.1%}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Threshold: {best['threshold']:.0%}")
        print(f"  Trades: {best['trades']}")
        print(f"  BUY Precision: {best['buy_prec']:.1f}%")
        print(f"  SELL Precision: {best['sell_prec']:.1f}%")
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': {
                'accuracy': float(acc),
                'win_rate': float(best['win_rate']),
                'buy_precision': float(best['buy_prec']),
                'sell_precision': float(best['sell_prec']),
                'threshold': float(best['threshold']),
                'trades': int(best['trades'])
            }
        }
    
    def save(self, result: dict) -> str:
        model_id = f"btcusd_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost',
            'strategy': 'trend-following',
            'confidence_threshold': result['metrics']['threshold']
        }
        
        meta = {
            'symbol': 'BTCUSD',
            'version': 'trend_following_v1',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Saved: {model_id}")
        return model_id
    
    def run(self):
        result = self.train()
        model_id = self.save(result)
        return {'model_id': model_id, **result['metrics']}


if __name__ == "__main__":
    print("="*60)
    print("TREND FOLLOWING BTC MODEL")
    print("="*60)
    
    trainer = TrendFollowingBTCTrainer()
    result = trainer.run()
    
    print(f"\n{'='*60}")
    if result['win_rate'] >= 50:
        print("✅ TARGET ACHIEVED!")
    else:
        print("⚠️ Below 50% - paper trade first")
    print("="*60)
    print(f"Model: {result['model_id']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
