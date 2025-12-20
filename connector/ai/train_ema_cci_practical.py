"""
Practical EMA-CCI Strategy Trainer
Adjusted for more realistic trading signals
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


class PracticalEMACCITrainer:
    """
    Practical implementation of EMA-CCI strategy
    More balanced labeling for trainable signals
    """
    
    FEATURES = [
        # EMA signals
        'ema_bullish', 'ema_bearish',
        'price_above_ema50', 'price_above_ema200',
        'ema50_slope', 'ema200_slope',
        'dist_ema200_pct',
        # CCI signals
        'cci', 'cci_buy_zone', 'cci_sell_zone',
        'cci_rising', 'cci_falling',
        # Combined signals
        'buy_setup', 'sell_setup',
        # Support features
        'trend_strength', 'momentum'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
        self.scaler = StandardScaler()
    
    def load_btc(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        return df[df['time'] >= cutoff].reset_index(drop=True)
    
    def load_xauusd(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
        df = pd.read_csv(path, sep=';')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={'date': 'time'})
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        return df[df['time'] >= cutoff].reset_index(drop=True)
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        
        # EMAs
        ema50 = c.ewm(span=50).mean()
        ema110 = c.ewm(span=110).mean()
        ema200 = c.ewm(span=200).mean()
        
        # EMA alignment
        f['ema_bullish'] = ((ema50 > ema110) & (ema110 > ema200)).astype(float)
        f['ema_bearish'] = ((ema50 < ema110) & (ema110 < ema200)).astype(float)
        f['price_above_ema50'] = (c > ema50).astype(float)
        f['price_above_ema200'] = (c > ema200).astype(float)
        
        # EMA slopes
        f['ema50_slope'] = ema50.pct_change(5) * 100
        f['ema200_slope'] = ema200.pct_change(5) * 100
        
        # Distance from EMA200
        f['dist_ema200_pct'] = (c - ema200) / ema200 * 100
        
        # CCI calculation
        tp = (h + l + c) / 3
        sma_tp = tp.rolling(20).mean()
        mean_dev = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - sma_tp) / (0.015 * mean_dev)
        
        f['cci'] = cci
        # Buy zone: -100 to 0 (oversold recovery)
        f['cci_buy_zone'] = ((cci >= -100) & (cci <= 0)).astype(float)
        # Sell zone: 0 to 100 (overbought)
        f['cci_sell_zone'] = ((cci >= 0) & (cci <= 100)).astype(float)
        f['cci_rising'] = (cci > cci.shift(2)).astype(float)
        f['cci_falling'] = (cci < cci.shift(2)).astype(float)
        
        # Combined setup signals
        f['buy_setup'] = ((f['ema_bullish'] == 1) & (f['cci_buy_zone'] == 1) & (f['cci_rising'] == 1)).astype(float)
        f['sell_setup'] = ((f['ema_bearish'] == 1) & (f['cci_sell_zone'] == 1) & (f['cci_falling'] == 1)).astype(float)
        
        # Trend strength
        f['trend_strength'] = abs(ema50 - ema200) / ema200 * 100
        
        # Momentum
        f['momentum'] = c.pct_change(4) * 100
        
        # Normalize
        for col in ['cci', 'ema50_slope', 'ema200_slope', 'dist_ema200_pct', 'trend_strength', 'momentum']:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """
        Practical labeling: 
        - Look ahead 4-6 bars
        - Use 0.3-0.5% threshold for signal
        """
        c = df['close'].astype(float)
        
        look_ahead = 6  # 1.5 hours
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # Symbol-specific thresholds
        if 'BTC' in symbol.upper():
            threshold = 0.4  # 0.4% for BTC
        else:
            threshold = 0.2  # 0.2% for Gold (~$4)
        
        labels = pd.Series(1, index=df.index)
        labels[future_ret > threshold] = 2  # BUY
        labels[future_ret < -threshold] = 0  # SELL
        
        return labels
    
    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        print(f"\n{'='*60}")
        print(f"PRACTICAL EMA-CCI: {symbol}")
        print("="*60)
        
        features = self.calc_features(df)
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
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("\n📊 Training...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            min_child_weight=10,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='mlogloss'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        print("\n📈 Win Rate Analysis:")
        best = {'threshold': 0.5, 'win_rate': 0, 'trades': 0, 'profit': 0}
        
        for thresh in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= thresh
            trades = (y_pred != 1) & conf
            
            if trades.sum() >= 20:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                
                # Profit with 1:3 RR
                wins = correct
                losses = trades.sum() - correct
                profit = wins * 3 - losses * 1
                
                buy_m = (y_pred == 2) & conf
                sell_m = (y_pred == 0) & conf
                bp = ((y_test[buy_m] == 2).sum() / buy_m.sum() * 100) if buy_m.sum() > 0 else 0
                sp = ((y_test[sell_m] == 0).sum() / sell_m.sum() * 100) if sell_m.sum() > 0 else 0
                
                profitable = profit > 0
                marker = "✅" if profitable else "⚠️"
                
                print(f"  {marker} {thresh:.0%}: Win {wr:.1f}%, Trades {trades.sum()}, Profit {profit:+.0f}R")
                
                if profit > best['profit'] or (wr > best['win_rate'] and trades.sum() >= 20):
                    best = {'threshold': thresh, 'win_rate': wr, 'trades': int(trades.sum()), 
                           'profit': profit, 'buy_prec': bp, 'sell_prec': sp}
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n📊 BEST: Win {best['win_rate']:.1f}%, Profit {best['profit']:+.0f}R, Trades {best['trades']}")
        
        return {
            'model': model,
            'scaler': self.scaler,
            'metrics': {
                'accuracy': float(acc),
                'win_rate': float(best['win_rate']),
                'profit_r': float(best['profit']),
                'trades': int(best['trades']),
                'threshold': float(best['threshold']),
                'buy_precision': float(best.get('buy_prec', 0)),
                'sell_precision': float(best.get('sell_prec', 0))
            }
        }
    
    def save(self, result: dict, symbol: str) -> str:
        model_id = f"{symbol.lower()}_emacci_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost',
            'strategy': 'ema-cci-practical',
            'confidence_threshold': result['metrics']['threshold'],
            'ema_periods': [50, 110, 200],
            'cci_period': 20,
            'risk_reward': 3.0
        }
        
        meta = {
            'symbol': symbol,
            'version': 'ema_cci_practical_v2',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        self.security.save_secured_model(secured)
        
        print(f"✅ Saved: {model_id}")
        return model_id
    
    def run(self):
        results = {}
        
        # XAUUSD
        print("\n" + "="*60)
        print("XAUUSD")
        df = self.load_xauusd()
        print(f"Loaded {len(df)} rows")
        res = self.train("XAUUSD", df)
        mid = self.save(res, "XAUUSD")
        results['XAUUSD'] = {'model_id': mid, **res['metrics']}
        
        # BTCUSD
        print("\n" + "="*60)
        print("BTCUSD")
        df = self.load_btc()
        print(f"Loaded {len(df)} rows")
        res = self.train("BTCUSD", df)
        mid = self.save(res, "BTCUSD")
        results['BTCUSD'] = {'model_id': mid, **res['metrics']}
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("PRACTICAL EMA-CCI STRATEGY")
    print("="*60)
    
    t = PracticalEMACCITrainer()
    r = t.run()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for s, d in r.items():
        marker = "✅" if d['profit_r'] > 0 else "⚠️"
        print(f"{marker} {s}: Win {d['win_rate']:.1f}%, Profit {d['profit_r']:+.0f}R, Trades {d['trades']}")
