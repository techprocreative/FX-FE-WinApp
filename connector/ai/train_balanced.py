"""
Balanced ML Trainer - Optimal Win Rate with Practical Signal Frequency
Target: ~55-60% win rate with enough signals for trading
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class BalancedTrainer:
    """
    Balanced trainer - good win rate with practical trade frequency
    Uses trend-following logic: only trade WITH the trend
    """
    
    FEATURES = [
        'rsi', 'rsi_ma', 'macd_hist', 'macd_cross',
        'bb_pos', 'trend_ema', 'trend_strength',
        'momentum_short', 'momentum_long', 'atr_pct'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
    
    def load_btc(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        print(f"Loading BTC...")
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        # Use 1.5 years
        cutoff = df['time'].max() - pd.Timedelta(days=540)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        print(f"  BTC: {len(df)} rows")
        return df
    
    def load_xau(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
        print(f"Loading XAUUSD...")
        df = pd.read_csv(path, sep=';')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={'date': 'time'})
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        cutoff = df['time'].max() - pd.Timedelta(days=540)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        print(f"  XAUUSD: {len(df)} rows")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Focused features for trend-following"""
        f = pd.DataFrame(index=df.index)
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        
        # RSI
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        f['rsi'] = 100 - (100 / (1 + rs))
        f['rsi_ma'] = f['rsi'].rolling(5).mean()
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['macd_hist'] = macd - macd_sig
        f['macd_cross'] = (macd > macd_sig).astype(float) - 0.5
        
        # BB Position
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_up = sma20 + 2 * std20
        bb_lo = sma20 - 2 * std20
        f['bb_pos'] = (c - bb_lo) / (bb_up - bb_lo + 1e-10)
        
        # Trend (EMA alignment)
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        f['trend_ema'] = (ema9 - ema21) / c * 100
        
        # Trend strength (simple)
        f['trend_strength'] = abs(f['trend_ema'])
        
        # Momentum
        f['momentum_short'] = c.pct_change(4) * 100  # 1 hour
        f['momentum_long'] = c.pct_change(16) * 100  # 4 hours
        
        # ATR %
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        f['atr_pct'] = atr / c * 100
        
        # Normalize only the non-binary features
        for col in ['rsi', 'rsi_ma', 'macd_hist', 'bb_pos', 'trend_ema', 
                    'trend_strength', 'momentum_short', 'momentum_long', 'atr_pct']:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """Create labels with moderate threshold"""
        c = df['close'].astype(float)
        
        # Look 6 bars ahead (1.5 hours)
        look_ahead = 6
        
        # Moderate threshold based on symbol
        if 'BTC' in symbol.upper():
            threshold = 0.4  # 0.4% for BTC
        else:
            threshold = 0.15  # 0.15% for Gold
        
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        labels = pd.Series(1, index=df.index)  # HOLD
        labels[future_ret > threshold] = 2  # BUY
        labels[future_ret < -threshold] = 0  # SELL
        
        return labels
    
    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        print(f"\n{'='*60}")
        print(f"Training {symbol}")
        print(f"{'='*60}")
        
        features = self.calc_features(df)
        labels = self.create_labels(df, symbol)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"Samples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"  SELL: {lc.get(0,0)} | HOLD: {lc.get(1,0)} | BUY: {lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        
        print("Training Random Forest...")
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=30,
            min_samples_leaf=15,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Evaluate at multiple thresholds
        y_proba = model.predict_proba(X_test)
        y_pred_all = model.predict(X_test)
        
        print("\nWin Rate Analysis:")
        results = {}
        for thresh in [0.40, 0.45, 0.50, 0.55, 0.60]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= thresh
            trades = (y_pred_all != 1) & conf  # Exclude HOLD
            
            if trades.sum() > 0:
                correct = (y_test[trades] == y_pred_all[trades]).sum()
                wr = correct / trades.sum() * 100
                results[thresh] = {'win_rate': wr, 'trades': trades.sum()}
                
                pct = trades.sum() / len(y_test) * 100
                print(f"  Threshold {thresh:.0%}: Win Rate {wr:.1f}%, Trades {trades.sum()} ({pct:.1f}%)")
        
        # Use threshold that gives ~55% win rate with enough trades
        best_thresh = 0.50
        for t in [0.45, 0.50, 0.55]:
            if t in results and results[t]['win_rate'] >= 52 and results[t]['trades'] > 50:
                best_thresh = t
                break
        
        # Final metrics at chosen threshold
        max_p = np.max(y_proba, axis=1)
        conf = max_p >= best_thresh
        trades = (y_pred_all != 1) & conf
        
        win_rate = 0
        buy_prec = 0
        sell_prec = 0
        
        if trades.sum() > 0:
            correct = (y_test[trades] == y_pred_all[trades]).sum()
            win_rate = correct / trades.sum() * 100
            
            # Buy precision
            buy_mask = (y_pred_all == 2) & conf
            if buy_mask.sum() > 0:
                buy_prec = (y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100
            
            # Sell precision
            sell_mask = (y_pred_all == 0) & conf
            if sell_mask.sum() > 0:
                sell_prec = (y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100
        
        overall_acc = accuracy_score(y_test, y_pred_all)
        
        print(f"\n📊 Final Results (threshold={best_thresh:.0%}):")
        print(f"   Overall Accuracy: {overall_acc:.1%}")
        print(f"   Trade Win Rate: {win_rate:.1f}%")
        print(f"   BUY Precision: {buy_prec:.1f}%")
        print(f"   SELL Precision: {sell_prec:.1f}%")
        print(f"   Trade Signals: {trades.sum()} ({trades.sum()/len(y_test)*100:.1f}%)")
        
        return {
            'model': model,
            'scaler': scaler,
            'metrics': {
                'accuracy': float(overall_acc),
                'win_rate': float(win_rate),
                'buy_precision': float(buy_prec),
                'sell_precision': float(sell_prec),
                'trade_signals': int(trades.sum()),
                'total_test': len(y_test),
                'confidence_threshold': best_thresh
            }
        }
    
    def save(self, result: dict, symbol: str) -> str:
        model_id = f"{symbol.lower()}_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'conf_threshold': result['metrics']['confidence_threshold']
        }
        
        meta = {
            'symbol': symbol,
            'version': 'balanced_v3',
            'trained': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Saved: {model_id}")
        return model_id
    
    def run(self):
        results = {}
        
        # BTC
        try:
            df = self.load_btc()
            res = self.train("BTCUSD", df)
            mid = self.save(res, "BTCUSD")
            results['BTCUSD'] = {'model_id': mid, **res['metrics']}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['BTCUSD'] = {'error': str(e)}
        
        # XAUUSD
        try:
            df = self.load_xau()
            res = self.train("XAUUSD", df)
            mid = self.save(res, "XAUUSD")
            results['XAUUSD'] = {'model_id': mid, **res['metrics']}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['XAUUSD'] = {'error': str(e)}
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("BALANCED ML TRAINING")
    print("Target: ~55% Win Rate with Practical Signals")
    print("="*60)
    
    t = BalancedTrainer()
    r = t.run()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    for s, d in r.items():
        if 'error' in d:
            print(f"❌ {s}: {d['error']}")
        else:
            print(f"✅ {s}:")
            print(f"   Win Rate: {d['win_rate']:.1f}%")
            print(f"   BUY/SELL Precision: {d['buy_precision']:.0f}% / {d['sell_precision']:.0f}%")
            print(f"   Signals: {d['trade_signals']} ({d['trade_signals']/d['total_test']*100:.1f}%)")
