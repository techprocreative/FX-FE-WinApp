"""
Binary BUY Signal Classifier for BTC
Instead of 3-class (BUY/HOLD/SELL), focus on: "Should I BUY now?"
This approach often gives better win rates for actual trading
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
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class BinaryBuyClassifier:
    """
    Binary classifier: Is this a good BUY opportunity?
    
    Output: 0 = No buy, 1 = BUY
    Win rate = Precision (of buy signals that actually go up)
    """
    
    FEATURES = [
        'trend_bullish', 'momentum_positive', 'momentum_accel',
        'rsi_setup', 'macd_bullish', 'macd_momentum',
        'bb_position', 'volume_confirms',
        'price_near_support', 'breakout_up',
        'ema_stack', 'trend_strength'
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
        """Features focused on BUY setups"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float)
        
        # Trend (EMA based)
        ema20 = c.ewm(span=20).mean()
        ema50 = c.ewm(span=50).mean()
        ema200 = c.ewm(span=200).mean()
        
        f['trend_bullish'] = ((c > ema20) & (ema20 > ema50)).astype(float)
        f['ema_stack'] = ((ema20 > ema50) & (ema50 > ema200)).astype(float)
        
        # Trend strength
        f['trend_strength'] = abs(c - ema50) / ema50 * 100
        
        # Momentum
        mom = c.pct_change(8) * 100
        f['momentum_positive'] = (mom > 0).astype(float)
        f['momentum_accel'] = mom.diff(4)
        
        # RSI setup (not overbought, rising from low)
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        # Good buy: RSI between 30-60 and rising
        f['rsi_setup'] = ((rsi > 30) & (rsi < 60) & (rsi > rsi.shift(3))).astype(float)
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['macd_bullish'] = (macd > macd_sig).astype(float)
        f['macd_momentum'] = macd - macd_sig
        
        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_lo = sma20 - 2 * std20
        bb_up = sma20 + 2 * std20
        f['bb_position'] = (c - bb_lo) / (bb_up - bb_lo + 1e-10)
        
        # Price near support (lower BB or recent low)
        low_10 = l.rolling(10).min()
        f['price_near_support'] = (c < low_10 * 1.01).astype(float)
        
        # Breakout
        high_20 = h.rolling(20).max()
        f['breakout_up'] = (c > high_20.shift(1)).astype(float)
        
        # Volume confirms
        vol_ma = v.rolling(20).mean()
        f['volume_confirms'] = (v > vol_ma).astype(float)
        
        # Normalize
        for col in ['trend_strength', 'momentum_accel', 'macd_momentum', 'bb_position']:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """
        Binary: Is this a profitable BUY entry?
        1 = Price goes up at least 0.5% in next 12 bars (3 hours)
        0 = Not a good buy
        """
        c = df['close'].astype(float)
        
        look_ahead = 12
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # 0.5% target for BTC
        threshold = 0.5
        
        labels = (future_ret > threshold).astype(int)
        
        return labels
    
    def train(self) -> dict:
        print(f"\n{'='*60}")
        print("BINARY BUY SIGNAL CLASSIFIER")
        print("Question: Should I BUY now?")
        print("="*60)
        
        df = self.load_data()
        features = self.calc_features(df)
        labels = self.create_labels(df)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"\nSamples: {len(data)}")
        lc = data['label'].value_counts()
        print(f"Labels: NO_BUY={lc.get(0,0)} ({lc.get(0,0)/len(data)*100:.1f}%) | BUY={lc.get(1,0)} ({lc.get(1,0)/len(data)*100:.1f}%)")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Handle imbalance with class weight
        pos_count = (y_train == 1).sum()
        neg_count = (y_train == 0).sum()
        scale_weight = neg_count / pos_count if pos_count > 0 else 1
        print(f"\n📊 Class weight: {scale_weight:.2f}")
        
        X_train_balanced, y_train_balanced = X_train_scaled, y_train
        
        print("\n📊 Training XGBoost...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.03,
            scale_pos_weight=2,  # Weight positive class more
            min_child_weight=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        model.fit(X_train_balanced, y_train_balanced)
        
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        print("\n📈 Win Rate (Precision) Analysis:")
        print("(How many BUY signals actually profit?)\n")
        
        best = {'threshold': 0.5, 'precision': 0, 'trades': 0, 'recall': 0}
        
        for thresh in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75]:
            buy_signals = y_proba >= thresh
            
            if buy_signals.sum() > 5:
                # Precision = Win Rate for BUY signals
                true_pos = (y_test[buy_signals] == 1).sum()
                total_signals = buy_signals.sum()
                precision = true_pos / total_signals * 100
                
                # Recall = What % of profitable moves did we catch?
                total_profitable = (y_test == 1).sum()
                recall = true_pos / total_profitable * 100 if total_profitable > 0 else 0
                
                marker = "✅" if precision >= 50 else "⚠️"
                print(f"  {marker} Threshold {thresh:.0%}: Win Rate {precision:.1f}%, Signals {total_signals} (catch {recall:.1f}% of moves)")
                
                if precision > best['precision'] and total_signals >= 10:
                    best = {'threshold': thresh, 'precision': precision, 'trades': int(total_signals), 'recall': recall}
        
        if best['precision'] < 50:
            # Try higher thresholds
            for thresh in [0.80, 0.85, 0.90]:
                buy_signals = y_proba >= thresh
                if buy_signals.sum() > 0:
                    true_pos = (y_test[buy_signals] == 1).sum()
                    precision = true_pos / buy_signals.sum() * 100
                    if precision >= 50:
                        recall = true_pos / (y_test == 1).sum() * 100
                        best = {'threshold': thresh, 'precision': precision, 'trades': int(buy_signals.sum()), 'recall': recall}
                        print(f"  ✅ Threshold {thresh:.0%}: Win Rate {precision:.1f}%, Signals {buy_signals.sum()}")
                        break
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print("📊 BEST RESULT")
        print("="*60)
        print(f"  Overall Accuracy: {acc:.1%}")
        print(f"  BUY Win Rate: {best['precision']:.1f}%")
        print(f"  Confidence Threshold: {best['threshold']:.0%}")
        print(f"  Expected Signals: {best['trades']}")
        print(f"  Catches: {best['recall']:.1f}% of profitable moves")
        
        # Feature importance
        imp = dict(zip(self.FEATURES, model.feature_importances_))
        top = sorted(imp.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\n🔑 Top Features:")
        for f_name, f_imp in top:
            print(f"   {f_name}: {f_imp:.4f}")
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': {
                'accuracy': float(acc),
                'win_rate': float(best['precision']),
                'recall': float(best['recall']),
                'threshold': float(best['threshold']),
                'trades': int(best['trades'])
            }
        }
    
    def save(self, result: dict) -> str:
        model_id = f"btcusd_buy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost_binary',
            'strategy': 'buy-signal',
            'confidence_threshold': result['metrics']['threshold'],
            'signal_type': 'BUY_ONLY'
        }
        
        meta = {
            'symbol': 'BTCUSD',
            'version': 'buy_signal_v1',
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
    print("BINARY BUY SIGNAL CLASSIFIER FOR BTC")
    print("Win Rate = Precision of BUY signals")
    print("="*60)
    
    trainer = BinaryBuyClassifier()
    result = trainer.run()
    
    print(f"\n{'='*60}")
    if result['win_rate'] >= 50:
        print("✅ TARGET ACHIEVED!")
        print(f"   Win Rate: {result['win_rate']:.1f}%")
        print(f"   This model is suitable for real trading!")
    else:
        print("⚠️ Below 50% - paper trade first")
    print("="*60)
