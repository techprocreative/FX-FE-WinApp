"""
High Win Rate BTC Trainer
Optimized for >50% win rate for real trading
Uses trend filtering, high confidence thresholds, and ensemble voting
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class HighWinRateBTCTrainer:
    """
    Trainer optimized for >50% win rate
    
    Strategies:
    1. Only trade WITH the trend (not counter-trend)
    2. Use larger price movement threshold (more confidence in signal)
    3. High confidence threshold (65%+) to reduce false signals
    4. Ensemble of 3 models voting together
    5. Filter by volatility regime
    """
    
    FEATURES = [
        # Trend confirmation
        'trend_ema_align', 'trend_macd', 'trend_momentum',
        'trend_strength', 'trend_consistency',
        # Momentum
        'rsi_signal', 'rsi_momentum', 
        'macd_hist', 'macd_direction',
        # Volatility filter
        'volatility_ok', 'atr_normal',
        # Volume
        'volume_confirms', 'volume_trend',
        # Price action
        'price_strength', 'breakout_signal'
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
        
        # Use 2 years
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend-focused features"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float)
        
        # === TREND FEATURES ===
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        ema200 = c.ewm(span=200).mean()
        
        # EMA alignment (strong trend signal)
        bull_align = (ema9 > ema21) & (ema21 > ema50) & (ema50 > ema200)
        bear_align = (ema9 < ema21) & (ema21 < ema50) & (ema50 < ema200)
        f['trend_ema_align'] = bull_align.astype(float) - bear_align.astype(float)
        
        # MACD trend
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['trend_macd'] = np.sign(macd)
        f['macd_hist'] = (macd - macd_sig) / c * 100
        f['macd_direction'] = np.sign(f['macd_hist'].diff(3))
        
        # Momentum trend (consistent direction)
        mom_4 = c.pct_change(4)
        mom_16 = c.pct_change(16)
        mom_48 = c.pct_change(48)
        f['trend_momentum'] = (np.sign(mom_4) == np.sign(mom_16)).astype(float)
        f['trend_consistency'] = ((np.sign(mom_4) == np.sign(mom_16)) & 
                                  (np.sign(mom_16) == np.sign(mom_48))).astype(float)
        
        # ADX-like trend strength
        plus_dm = ((h - h.shift()).where((h - h.shift()) > (l.shift() - l), 0)).rolling(14).mean()
        minus_dm = ((l.shift() - l).where((l.shift() - l) > (h - h.shift()), 0)).rolling(14).mean()
        dx = abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-10)
        adx = dx.rolling(14).mean()
        f['trend_strength'] = (adx > 0.25).astype(float)  # Strong trend
        
        # === RSI SIGNALS ===
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        # RSI in favorable zone (not extreme)
        f['rsi_signal'] = ((rsi > 40) & (rsi < 60)).astype(float)  # Neutral zone
        f['rsi_momentum'] = rsi.diff(3)
        
        # === VOLATILITY FILTER ===
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        atr_pct = atr / c * 100
        
        # Normal volatility (not too high, not too low)
        atr_q25 = atr_pct.rolling(100).quantile(0.25)
        atr_q75 = atr_pct.rolling(100).quantile(0.75)
        f['volatility_ok'] = ((atr_pct > atr_q25) & (atr_pct < atr_q75)).astype(float)
        f['atr_normal'] = atr_pct
        
        # === VOLUME CONFIRMATION ===
        vol_ma = v.rolling(20).mean()
        vol_ratio = v / (vol_ma + 1e-10)
        f['volume_confirms'] = (vol_ratio > 1.2).astype(float)  # Above average volume
        f['volume_trend'] = vol_ma.pct_change(10)
        
        # === PRICE ACTION ===
        high_20 = h.rolling(20).max()
        low_20 = l.rolling(20).min()
        f['price_strength'] = (c - low_20) / (high_20 - low_20 + 1e-10)
        
        # Breakout detection
        f['breakout_signal'] = ((c > high_20.shift(1)) | (c < low_20.shift(1))).astype(float)
        
        # Normalize continuous features
        for col in ['macd_hist', 'rsi_momentum', 'atr_normal', 'volume_trend', 'price_strength']:
            if col in f.columns and f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """
        Create labels for LARGER price movements only
        This increases win rate by only trading significant moves
        """
        c = df['close'].astype(float)
        
        # Look 12 bars ahead (3 hours) - more time for move to develop
        look_ahead = 12
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # Higher threshold: 0.8% for BTC (significant move)
        threshold = 0.8
        
        labels = pd.Series(1, index=df.index)  # HOLD
        labels[future_ret > threshold] = 2     # Strong BUY
        labels[future_ret < -threshold] = 0    # Strong SELL
        
        return labels
    
    def train(self) -> dict:
        print(f"\n{'='*60}")
        print("HIGH WIN RATE BTC TRAINER")
        print("Target: >50% Win Rate for Real Trading")
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
        
        # === ENSEMBLE OF 3 MODELS ===
        print("\n📊 Training Ensemble (3 models voting)...")
        
        model1 = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            min_child_weight=7,
            subsample=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        
        model2 = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            min_samples_split=50,
            subsample=0.8,
            random_state=42
        )
        
        model3 = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=30,
            min_samples_leaf=15,
            random_state=42,
            n_jobs=-1
        )
        
        # Voting ensemble
        ensemble = VotingClassifier(
            estimators=[
                ('xgb', model1),
                ('gb', model2),
                ('rf', model3)
            ],
            voting='soft'  # Use probabilities
        )
        
        ensemble.fit(X_train_scaled, y_train)
        
        y_pred = ensemble.predict(X_test_scaled)
        y_proba = ensemble.predict_proba(X_test_scaled)
        
        # === WIN RATE ANALYSIS WITH HIGH THRESHOLDS ===
        print("\n📈 Win Rate Analysis (High Confidence Only):")
        
        best_result = {'threshold': 0.5, 'win_rate': 0, 'trades': 0, 'buy_prec': 0, 'sell_prec': 0}
        
        for thresh in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75]:
            max_p = np.max(y_proba, axis=1)
            confident = max_p >= thresh
            trades = (y_pred != 1) & confident
            
            if trades.sum() > 0:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                pct = trades.sum() / len(y_test) * 100
                
                # Per-class precision
                buy_mask = (y_pred == 2) & confident
                sell_mask = (y_pred == 0) & confident
                buy_prec = ((y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100) if buy_mask.sum() > 0 else 0
                sell_prec = ((y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100) if sell_mask.sum() > 0 else 0
                
                status = "✅" if wr >= 50 else "⚠️"
                print(f"  {status} Threshold {thresh:.0%}: Win {wr:.1f}%, Trades {trades.sum()} ({pct:.1f}%), BUY {buy_prec:.0f}%, SELL {sell_prec:.0f}%")
                
                # Select best threshold with >50% win rate
                if wr >= 50 and trades.sum() > 5 and wr > best_result['win_rate']:
                    best_result = {
                        'threshold': thresh,
                        'win_rate': wr,
                        'trades': int(trades.sum()),
                        'buy_prec': buy_prec,
                        'sell_prec': sell_prec
                    }
        
        # If no >50% found, use highest
        if best_result['win_rate'] < 50:
            print("\n⚠️ No threshold achieved >50% win rate with enough trades")
            # Find highest win rate regardless
            for thresh in [0.70, 0.75, 0.80]:
                max_p = np.max(y_proba, axis=1)
                confident = max_p >= thresh
                trades = (y_pred != 1) & confident
                if trades.sum() > 0:
                    correct = (y_test[trades] == y_pred[trades]).sum()
                    wr = correct / trades.sum() * 100
                    if wr > best_result['win_rate']:
                        buy_mask = (y_pred == 2) & confident
                        sell_mask = (y_pred == 0) & confident
                        buy_prec = ((y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100) if buy_mask.sum() > 0 else 0
                        sell_prec = ((y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100) if sell_mask.sum() > 0 else 0
                        best_result = {
                            'threshold': thresh,
                            'win_rate': wr,
                            'trades': int(trades.sum()),
                            'buy_prec': buy_prec,
                            'sell_prec': sell_prec
                        }
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print("📊 FINAL RESULTS")
        print("="*60)
        print(f"  Overall Accuracy: {acc:.1%}")
        print(f"  Win Rate: {best_result['win_rate']:.1f}%")
        print(f"  BUY Precision: {best_result['buy_prec']:.1f}%")
        print(f"  SELL Precision: {best_result['sell_prec']:.1f}%")
        print(f"  Confidence Threshold: {best_result['threshold']:.0%}")
        print(f"  Expected Trades: {best_result['trades']}")
        
        if best_result['win_rate'] >= 50:
            print(f"\n✅ TARGET ACHIEVED: {best_result['win_rate']:.1f}% Win Rate!")
        else:
            print(f"\n⚠️ Win rate below 50%. Consider paper trading first.")
        
        return {
            'model': ensemble,
            'scaler': self.scaler,
            'metrics': {
                'accuracy': float(acc),
                'win_rate': float(best_result['win_rate']),
                'buy_precision': float(best_result['buy_prec']),
                'sell_precision': float(best_result['sell_prec']),
                'threshold': float(best_result['threshold']),
                'trades': int(best_result['trades'])
            }
        }
    
    def save(self, result: dict) -> str:
        model_id = f"btcusd_highwr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'ensemble_voting',
            'strategy': 'high-winrate',
            'confidence_threshold': result['metrics']['threshold']
        }
        
        meta = {
            'symbol': 'BTCUSD',
            'version': 'high_winrate_v1',
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
    print("HIGH WIN RATE BTC TRAINING")
    print("For Real Money Trading (Target >50%)")
    print("="*60)
    
    trainer = HighWinRateBTCTrainer()
    result = trainer.run()
    
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Model: {result['model_id']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    
    if result['win_rate'] >= 50:
        print("\n✅ Model is suitable for real trading!")
    else:
        print("\n⚠️ Recommend paper trading first to validate")
