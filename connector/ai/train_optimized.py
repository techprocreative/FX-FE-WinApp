"""
Optimized ML Trainer for High Win Rate
Uses stricter thresholds and binary classification (BUY vs NOT_BUY, SELL vs NOT_SELL)
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class OptimizedTrainer:
    """
    Optimized trainer focused on WIN RATE over trade frequency.
    Strategy: Only trade when confidence is VERY high.
    """
    
    FEATURES = [
        'rsi', 'rsi_slope', 'macd', 'macd_signal', 'macd_hist',
        'bb_position', 'bb_squeeze', 'ema_trend', 'ema_momentum',
        'atr_norm', 'price_momentum', 'price_acceleration',
        'volume_surge', 'trend_strength'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
    
    def load_btc(self) -> pd.DataFrame:
        """Load BTC 15m data"""
        path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
        print(f"Loading BTC from {path}")
        
        df = pd.read_csv(path)
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df = df.rename(columns={'open_time': 'time'})
        df['time'] = pd.to_datetime(df['time'].str.strip())
        df = df.sort_values('time').reset_index(drop=True)
        
        # Last 1 year only - more relevant
        cutoff = df['time'].max() - pd.Timedelta(days=365)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows")
        return df
    
    def load_xau(self) -> pd.DataFrame:
        """Load XAUUSD 15m data"""
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
        """Calculate optimized features for trend detection"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float) if 'volume' in df.columns else pd.Series(1, index=df.index)
        
        # RSI with slope
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        f['rsi'] = 100 - (100 / (1 + rs))
        f['rsi_slope'] = f['rsi'].diff(3)
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        f['macd'] = ema12 - ema26
        f['macd_signal'] = f['macd'].ewm(span=9).mean()
        f['macd_hist'] = f['macd'] - f['macd_signal']
        
        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        f['bb_position'] = (c - bb_lower) / (bb_upper - bb_lower + 1e-10)
        
        # BB Squeeze (low volatility precedes breakout)
        bb_width = (bb_upper - bb_lower) / sma20
        f['bb_squeeze'] = bb_width.rolling(20).apply(lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min() + 1e-10))
        
        # EMA trend
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        f['ema_trend'] = ((ema9 > ema21) & (ema21 > ema50)).astype(float) - ((ema9 < ema21) & (ema21 < ema50)).astype(float)
        f['ema_momentum'] = (c - ema21) / (ema21 + 1e-10) * 100
        
        # ATR normalized
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        f['atr_norm'] = atr / c * 100
        
        # Price momentum and acceleration
        f['price_momentum'] = c.pct_change(12) * 100  # 3 hours
        f['price_acceleration'] = f['price_momentum'].diff(4)
        
        # Volume surge
        v_ma = v.rolling(20).mean()
        f['volume_surge'] = (v / (v_ma + 1e-10)).rolling(3).mean()
        
        # Trend strength (ADX-like)
        plus_dm = ((h - h.shift()).where((h - h.shift()) > (l.shift() - l), 0)).rolling(14).mean()
        minus_dm = ((l.shift() - l).where((l.shift() - l) > (h - h.shift()), 0)).rolling(14).mean()
        f['trend_strength'] = abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-10)
        
        # Normalize
        for col in f.columns:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """
        Create binary labels with STRICT thresholds for high win rate.
        
        For high win rate, we need to:
        1. Use larger price movement threshold
        2. Look further ahead
        3. Only label the STRONGEST signals
        """
        c = df['close'].astype(float)
        
        # Settings per symbol
        if 'BTC' in symbol.upper():
            look_ahead = 12  # 3 hours
            threshold = 0.8   # 0.8% move for BTC (high volatility)
        else:
            look_ahead = 12
            threshold = 0.3   # 0.3% move for Gold
        
        future_return = (c.shift(-look_ahead) / c - 1) * 100
        
        # Labels: 0=SELL signal, 1=NEUTRAL/HOLD, 2=BUY signal
        labels = pd.Series(1, index=df.index)  # Default HOLD
        labels[future_return > threshold] = 2   # Strong BUY
        labels[future_return < -threshold] = 0  # Strong SELL
        
        return labels
    
    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        """Train with optimization for WIN RATE"""
        print(f"\n{'='*60}")
        print(f"Training {symbol}")
        print(f"{'='*60}")
        
        features = self.calc_features(df)
        labels = self.create_labels(df, symbol)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"Samples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"Labels: SELL={lc.get(0,0)}, HOLD={lc.get(1,0)}, BUY={lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        # Time series split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Scale
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        
        # Train with parameters optimized for PRECISION (win rate)
        print("Training optimized model...")
        model = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            min_samples_split=100,
            min_samples_leaf=50,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate with HIGH confidence threshold
        y_proba = model.predict_proba(X_test)
        
        # For win rate, we only care about HIGH confidence predictions
        conf_threshold = 0.65  # Very high threshold
        
        # Get predictions only when confident
        y_pred_raw = model.predict(X_test)
        max_proba = np.max(y_proba, axis=1)
        confident = max_proba >= conf_threshold
        
        # Trade signals (exclude HOLD)
        trade_signals = (y_pred_raw != 1) & confident
        
        if trade_signals.sum() > 0:
            trade_correct = (y_test[trade_signals] == y_pred_raw[trade_signals]).sum()
            win_rate = trade_correct / trade_signals.sum() * 100
            
            # Precision per class
            buy_signals = (y_pred_raw == 2) & confident
            sell_signals = (y_pred_raw == 0) & confident
            
            buy_precision = 0
            if buy_signals.sum() > 0:
                buy_correct = ((y_test[buy_signals] == 2)).sum()
                buy_precision = buy_correct / buy_signals.sum() * 100
            
            sell_precision = 0
            if sell_signals.sum() > 0:
                sell_correct = ((y_test[sell_signals] == 0)).sum()
                sell_precision = sell_correct / sell_signals.sum() * 100
        else:
            win_rate = 0
            buy_precision = 0
            sell_precision = 0
        
        overall_acc = accuracy_score(y_test, y_pred_raw)
        
        print(f"\nResults (confidence threshold: {conf_threshold:.0%}):")
        print(f"  Overall Accuracy: {overall_acc:.1%}")
        print(f"  Trade Win Rate: {win_rate:.1f}%")
        print(f"  BUY Precision: {buy_precision:.1f}%")
        print(f"  SELL Precision: {sell_precision:.1f}%")
        print(f"  Confident Trades: {trade_signals.sum()} / {len(y_test)} ({trade_signals.sum()/len(y_test)*100:.1f}%)")
        
        return {
            'model': model,
            'scaler': scaler,
            'metrics': {
                'overall_accuracy': float(overall_acc),
                'win_rate': float(win_rate),
                'buy_precision': float(buy_precision),
                'sell_precision': float(sell_precision),
                'confident_trades': int(trade_signals.sum()),
                'total_test': len(y_test),
                'confidence_threshold': conf_threshold
            }
        }
    
    def save(self, result: dict, symbol: str) -> str:
        """Save encrypted model"""
        model_id = f"{symbol.lower()}_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        package = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'confidence_threshold': result['metrics']['confidence_threshold']
        }
        
        metadata = {
            'symbol': symbol,
            'version': 'optimized_v2',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(package, model_id, metadata)
        path = self.security.save_secured_model(secured)
        
        print(f"\nSaved: {model_id}")
        print(f"Path: {path}")
        return model_id
    
    def run(self):
        """Train both models"""
        results = {}
        
        # BTC
        print("\n" + "="*60)
        print("BTCUSD")
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
        
        # XAUUSD
        print("\n" + "="*60)
        print("XAUUSD")
        print("="*60)
        try:
            df = self.load_xau()
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
    print("OPTIMIZED ML TRAINING FOR HIGH WIN RATE")
    print("="*60)
    
    trainer = OptimizedTrainer()
    results = trainer.run()
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    for sym, data in results.items():
        if 'error' in data:
            print(f"❌ {sym}: {data['error']}")
        else:
            print(f"✅ {sym}:")
            print(f"   Win Rate: {data['win_rate']:.1f}%")
            print(f"   BUY Precision: {data['buy_precision']:.1f}%")
            print(f"   SELL Precision: {data['sell_precision']:.1f}%")
            print(f"   Model: {data['model_id']}")
