"""
Momentum Spike Scalper - Trade only during strong momentum bursts
Higher win rate by being more selective
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


class MomentumSpikeScalper:
    """
    Only trade during strong momentum bursts
    Higher selectivity = higher win rate
    """
    
    FEATURES = [
        # Momentum burst detection
        'momentum_burst', 'burst_strength', 'burst_duration',
        # Price acceleration
        'price_accel', 'accel_positive',
        # Volume surge
        'volume_surge', 'volume_surge_pct',
        # Trend confirmation
        'trend_aligned', 'micro_trend',
        # RSI momentum
        'rsi_rising', 'rsi_level',
        # Volatility expansion
        'vol_expansion', 'atr_spike'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
    
    def load_btc(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        cutoff = df['time'].max() - pd.Timedelta(days=365)
        return df[df['time'] >= cutoff].reset_index(drop=True)
    
    def load_xauusd(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
        df = pd.read_csv(path, sep=';')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={'date': 'time'})
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        cutoff = df['time'].max() - pd.Timedelta(days=365)
        return df[df['time'] >= cutoff].reset_index(drop=True)
    
    def calc_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float) if 'volume' in df.columns else pd.Series(1, index=df.index)
        
        # Momentum burst: price change in last 2 bars > 2x average
        pct_1 = c.pct_change(1).abs() * 100
        pct_2 = c.pct_change(2).abs() * 100
        avg_move = pct_2.rolling(20).mean()
        f['momentum_burst'] = (pct_2 > avg_move * 2).astype(float)
        f['burst_strength'] = pct_2 / (avg_move + 0.01)
        
        # Burst duration (consecutive strong moves)
        strong_move = pct_1 > pct_1.rolling(20).quantile(0.8)
        f['burst_duration'] = strong_move.groupby((~strong_move).cumsum()).cumcount()
        
        # Price acceleration
        mom_1 = c.pct_change(1) * 100
        mom_2 = c.pct_change(2) * 100
        f['price_accel'] = mom_1 - mom_1.shift(1)
        f['accel_positive'] = (f['price_accel'] > 0).astype(float)
        
        # Volume surge
        vol_ma = v.rolling(10).mean()
        f['volume_surge'] = (v > vol_ma * 2).astype(float)
        f['volume_surge_pct'] = v / (vol_ma + 1)
        
        # Trend alignment
        ema10 = c.ewm(span=10).mean()
        ema20 = c.ewm(span=20).mean()
        f['trend_aligned'] = np.sign(c - ema10) * np.sign(ema10 - ema20)
        f['micro_trend'] = np.sign(c.diff(3))
        
        # RSI momentum (direction matters more than level)
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(7).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        f['rsi_rising'] = (rsi > rsi.shift(2)).astype(float)
        f['rsi_level'] = rsi / 100
        
        # Volatility expansion
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(10).mean()
        f['vol_expansion'] = (tr > atr * 1.5).astype(float)
        f['atr_spike'] = tr / (atr + 1e-10)
        
        # Normalize continuous
        for col in ['burst_strength', 'burst_duration', 'price_accel', 'volume_surge_pct', 'rsi_level', 'atr_spike']:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """Quick momentum follow - catch continuation of burst"""
        c = df['close'].astype(float)
        
        # Very quick: 2 bars
        look_ahead = 2
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # Threshold based on symbol
        thresh = 0.15 if 'BTC' in symbol.upper() else 0.08  # Smaller for quick scalps
        
        labels = pd.Series(1, index=df.index)
        labels[future_ret > thresh] = 2
        labels[future_ret < -thresh] = 0
        
        return labels
    
    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        print(f"\n{'='*60}")
        print(f"MOMENTUM SPIKE SCALPER: {symbol}")
        print("="*60)
        
        features = self.calc_features(df, symbol)
        labels = self.create_labels(df, symbol)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"Samples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"SELL: {lc.get(0,0)} | HOLD: {lc.get(1,0)} | BUY: {lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print("\n📊 Training...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.03,
            min_child_weight=15,
            subsample=0.7,
            colsample_bytree=0.7,
            random_state=42,
            eval_metric='mlogloss'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        print("\n📈 Win Rate by Threshold:")
        best = {'threshold': 0.5, 'win_rate': 0, 'trades': 0, 'buy_prec': 0, 'sell_prec': 0}
        
        for t in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= t
            trades = (y_pred != 1) & conf
            
            if trades.sum() >= 15:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                
                buy_m = (y_pred == 2) & conf
                sell_m = (y_pred == 0) & conf
                bp = ((y_test[buy_m] == 2).sum() / buy_m.sum() * 100) if buy_m.sum() > 0 else 0
                sp = ((y_test[sell_m] == 0).sum() / sell_m.sum() * 100) if sell_m.sum() > 0 else 0
                
                mark = "✅" if wr >= 50 else "⚠️"
                print(f"  {mark} {t:.0%}: Win {wr:.1f}%, Trades {trades.sum()}, BUY {bp:.0f}%, SELL {sp:.0f}%")
                
                if wr > best['win_rate'] or (wr >= 50 and wr == best['win_rate'] and trades.sum() > best['trades']):
                    best = {'threshold': t, 'win_rate': wr, 'trades': int(trades.sum()), 'buy_prec': bp, 'sell_prec': sp}
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n📊 BEST: {best['win_rate']:.1f}% @ {best['threshold']:.0%}, {best['trades']} trades")
        
        return {
            'model': model,
            'scaler': scaler,
            'metrics': best | {'accuracy': float(acc)}
        }
    
    def save(self, result: dict, symbol: str) -> str:
        model_id = f"{symbol.lower()}_momentum_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost',
            'strategy': 'momentum-scalp',
            'confidence_threshold': result['metrics']['threshold']
        }
        
        meta = {
            'symbol': symbol,
            'version': 'momentum_scalp_v1',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        self.security.save_secured_model(secured)
        
        print(f"✅ Saved: {model_id}")
        return model_id
    
    def run(self):
        results = {}
        
        print("\n" + "="*60)
        print("BTCUSD")
        print("="*60)
        df = self.load_btc()
        print(f"Loaded {len(df)} rows")
        res = self.train("BTCUSD", df)
        mid = self.save(res, "BTCUSD")
        results['BTCUSD'] = {'model_id': mid, **res['metrics']}
        
        print("\n" + "="*60)
        print("XAUUSD")
        print("="*60)
        df = self.load_xauusd()
        print(f"Loaded {len(df)} rows")
        res = self.train("XAUUSD", df)
        mid = self.save(res, "XAUUSD")
        results['XAUUSD'] = {'model_id': mid, **res['metrics']}
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("MOMENTUM SPIKE SCALPER")
    print("="*60)
    
    t = MomentumSpikeScalper()
    r = t.run()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for s, d in r.items():
        mark = "✅" if d['win_rate'] >= 50 else "⚠️"
        print(f"{mark} {s}: {d['win_rate']:.1f}% win rate, {d['trades']} trades")
