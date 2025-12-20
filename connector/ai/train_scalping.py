"""
Scalping Model Trainer for BTC and XAUUSD
Optimized for:
- Quick entries (1-4 bars / 15-60 minutes hold time)
- Small price targets (0.2-0.3%)
- High win rate (>50%)
- Momentum-based signals
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


class ScalpingTrainer:
    """
    Scalping model trainer - optimized for quick trades
    
    Key differences from swing trading:
    1. Shorter lookback features (fast indicators)
    2. Smaller profit targets
    3. Focus on momentum and volume spikes
    4. Avoid trading during low volatility
    """
    
    FEATURES = [
        # Fast momentum (1-4 bars)
        'momentum_1', 'momentum_2', 'momentum_4',
        'accel', 'jerk',
        # Fast RSI (5 period)
        'rsi_fast', 'rsi_direction',
        # Volume spike
        'volume_spike', 'volume_trend',
        # Price action
        'candle_body', 'candle_wick_ratio',
        # Micro trend
        'ema_micro', 'ema_slope',
        # Volatility
        'volatility_now', 'volatility_expanding'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
        self.scaler = StandardScaler()
    
    def load_btc(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        print(f"Loading BTC from {path}")
        
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        
        # Use 1 year for scalping (patterns change faster)
        cutoff = df['time'].max() - pd.Timedelta(days=365)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows")
        return df
    
    def load_xauusd(self) -> pd.DataFrame:
        path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
        print(f"Loading XAUUSD from {path}")
        
        df = pd.read_csv(path, sep=';')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={'date': 'time'})
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        
        cutoff = df['time'].max() - pd.Timedelta(days=365)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fast scalping features"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        o = df['open'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float) if 'volume' in df.columns else pd.Series(1, index=df.index)
        
        # Fast momentum (immediate price action)
        f['momentum_1'] = c.pct_change(1) * 100
        f['momentum_2'] = c.pct_change(2) * 100
        f['momentum_4'] = c.pct_change(4) * 100
        
        # Acceleration and jerk (rate of change of momentum)
        f['accel'] = f['momentum_1'].diff()
        f['jerk'] = f['accel'].diff()
        
        # Fast RSI (5 period for scalping)
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(5).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(5).mean()
        rs = gain / (loss + 1e-10)
        f['rsi_fast'] = 100 - (100 / (1 + rs))
        f['rsi_direction'] = f['rsi_fast'].diff(2)
        
        # Volume spike (critical for scalping)
        vol_ma = v.rolling(10).mean()
        f['volume_spike'] = v / (vol_ma + 1e-10)
        f['volume_trend'] = vol_ma.pct_change(3)
        
        # Candle analysis
        body = abs(c - o)
        range_ = h - l + 1e-10
        f['candle_body'] = body / range_  # Body to range ratio
        
        upper_wick = h - np.maximum(c, o)
        lower_wick = np.minimum(c, o) - l
        f['candle_wick_ratio'] = (upper_wick - lower_wick) / range_  # Wick imbalance
        
        # Micro trend (very fast EMA)
        ema5 = c.ewm(span=5).mean()
        ema10 = c.ewm(span=10).mean()
        f['ema_micro'] = (ema5 - ema10) / c * 100
        f['ema_slope'] = ema5.pct_change(2) * 100
        
        # Instant volatility
        f['volatility_now'] = (h - l) / c * 100
        vol_ma_10 = f['volatility_now'].rolling(10).mean()
        f['volatility_expanding'] = (f['volatility_now'] > vol_ma_10 * 1.2).astype(float)
        
        # Normalize
        for col in ['momentum_1', 'momentum_2', 'momentum_4', 'accel', 'jerk',
                    'rsi_fast', 'rsi_direction', 'volume_spike', 'volume_trend',
                    'candle_body', 'candle_wick_ratio', 'ema_micro', 'ema_slope', 'volatility_now']:
            if col in f.columns and f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """
        Scalping labels: Quick profit in 2-4 bars
        """
        c = df['close'].astype(float)
        
        # Quick target: 2 bars ahead (30 min on M15)
        look_ahead = 2
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # Small scalping target
        if 'BTC' in symbol.upper():
            threshold = 0.2  # 0.2% for BTC scalp
        else:
            threshold = 0.1  # 0.1% for Gold scalp
        
        labels = pd.Series(1, index=df.index)  # HOLD
        labels[future_ret > threshold] = 2     # Quick BUY
        labels[future_ret < -threshold] = 0    # Quick SELL
        
        return labels
    
    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        print(f"\n{'='*60}")
        print(f"SCALPING MODEL: {symbol}")
        print("="*60)
        
        features = self.calc_features(df)
        labels = self.create_labels(df, symbol)
        
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
        
        print("\n📊 Training XGBoost for Scalping...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            min_child_weight=10,  # Conservative for scalping
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=1.5,
            random_state=42,
            eval_metric='mlogloss'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        print("\n📈 Scalping Win Rate Analysis:")
        best = {'threshold': 0.5, 'win_rate': 0, 'trades': 0, 'buy_prec': 0, 'sell_prec': 0}
        
        for thresh in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
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
                
                freq = trades.sum() / len(y_test) * 100
                marker = "✅" if wr >= 50 else "⚠️"
                print(f"  {marker} {thresh:.0%}: Win {wr:.1f}%, {trades.sum()} trades ({freq:.1f}%), BUY {buy_prec:.0f}%, SELL {sell_prec:.0f}%")
                
                if wr >= 50 and trades.sum() >= 20:
                    if wr > best['win_rate'] or (wr == best['win_rate'] and trades.sum() > best['trades']):
                        best = {'threshold': thresh, 'win_rate': wr, 'trades': int(trades.sum()),
                               'buy_prec': buy_prec, 'sell_prec': sell_prec}
                elif best['win_rate'] < 50 and wr > best['win_rate'] and trades.sum() >= 20:
                    best = {'threshold': thresh, 'win_rate': wr, 'trades': int(trades.sum()),
                           'buy_prec': buy_prec, 'sell_prec': sell_prec}
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print("📊 BEST SCALPING RESULT")
        print("="*60)
        print(f"  Accuracy: {acc:.1%}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Threshold: {best['threshold']:.0%}")
        print(f"  Trades: {best['trades']}")
        print(f"  BUY Win: {best['buy_prec']:.1f}%")
        print(f"  SELL Win: {best['sell_prec']:.1f}%")
        
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
    
    def save(self, result: dict, symbol: str) -> str:
        model_id = f"{symbol.lower()}_scalp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost',
            'strategy': 'scalping',
            'confidence_threshold': result['metrics']['threshold'],
            'lookback_bars': 2,
            'target_pips': 20 if 'btc' in symbol.lower() else 10
        }
        
        meta = {
            'symbol': symbol,
            'version': 'scalping_v1',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Saved: {model_id}")
        return model_id
    
    def train_all(self):
        """Train scalping models for BTC and XAUUSD"""
        results = {}
        
        # BTC Scalping
        print("\n" + "="*60)
        print("BTCUSD SCALPING MODEL")
        print("="*60)
        try:
            df = self.load_btc()
            res = self.train("BTCUSD", df)
            model_id = self.save(res, "BTCUSD")
            results['BTCUSD'] = {'model_id': model_id, **res['metrics']}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['BTCUSD'] = {'error': str(e)}
        
        # XAUUSD Scalping
        print("\n" + "="*60)
        print("XAUUSD SCALPING MODEL")
        print("="*60)
        try:
            df = self.load_xauusd()
            res = self.train("XAUUSD", df)
            model_id = self.save(res, "XAUUSD")
            results['XAUUSD'] = {'model_id': model_id, **res['metrics']}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['XAUUSD'] = {'error': str(e)}
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("SCALPING MODEL TRAINING")
    print("Quick entries, small targets, high win rate")
    print("="*60)
    
    trainer = ScalpingTrainer()
    results = trainer.train_all()
    
    print("\n" + "="*60)
    print("📊 SCALPING TRAINING SUMMARY")
    print("="*60)
    
    for symbol, data in results.items():
        if 'error' in data:
            print(f"❌ {symbol}: {data['error']}")
        else:
            marker = "✅" if data['win_rate'] >= 50 else "⚠️"
            print(f"\n{marker} {symbol}:")
            print(f"   Model: {data['model_id']}")
            print(f"   Win Rate: {data['win_rate']:.1f}%")
            print(f"   Trades: {data['trades']}")
            print(f"   Threshold: {data['threshold']:.0%}")
