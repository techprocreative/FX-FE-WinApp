"""
Backtest ML Models for Profitability Validation
Simulates actual trading with:
- Spread costs
- Realistic entry/exit
- Position sizing
- Win/Loss tracking
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class ModelBacktester:
    """
    Backtest ML models with realistic trading simulation
    """
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
    
    def load_ohlcv(self, symbol: str) -> pd.DataFrame:
        """Load OHLCV data for backtesting"""
        if 'btc' in symbol.lower():
            path = self.ohlcv_dir / "btc" / "btc_15m_data_2018_to_2025.csv"
            df = pd.read_csv(path)
            df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
            df = df.rename(columns={'open_time': 'time'})
            df['time'] = pd.to_datetime(df['time'].str.strip())
        else:
            path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
            df = pd.read_csv(path, sep=';')
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.rename(columns={'date': 'time'})
            df['time'] = pd.to_datetime(df['time'])
        
        df = df.sort_values('time').reset_index(drop=True)
        return df
    
    def calc_features(self, df: pd.DataFrame, feature_list: list) -> pd.DataFrame:
        """Calculate features based on model requirements"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        o = df['open'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float) if 'volume' in df.columns else pd.Series(1, index=df.index)
        
        # Calculate all possible features
        # Momentum
        f['momentum_1'] = c.pct_change(1) * 100
        f['momentum_2'] = c.pct_change(2) * 100
        f['momentum_4'] = c.pct_change(4) * 100
        f['momentum'] = c.pct_change(8) * 100
        f['accel'] = f['momentum_1'].diff()
        f['jerk'] = f['accel'].diff()
        f['momentum_accel'] = f['momentum'].diff(4) if 'momentum' in f else 0
        
        # RSI variants
        delta = c.diff()
        for period in [5, 7, 14]:
            gain = delta.where(delta > 0, 0).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / (loss + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            f[f'rsi_{period}'] = rsi
        f['rsi'] = f['rsi_14']
        f['rsi_fast'] = f['rsi_5']
        f['rsi_direction'] = f['rsi_fast'].diff(2)
        f['rsi_rising'] = (f['rsi'] > f['rsi'].shift(2)).astype(float)
        f['rsi_level'] = f['rsi'] / 100
        f['rsi_momentum'] = f['rsi'].diff(3)
        f['rsi_setup'] = ((f['rsi'] > 30) & (f['rsi'] < 60) & (f['rsi'] > f['rsi'].shift(3))).astype(float)
        
        # MACD
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['macd'] = macd / c * 100
        f['macd_signal'] = macd_sig / c * 100
        f['macd_hist'] = (macd - macd_sig) / c * 100
        f['macd_cross'] = ((macd > macd_sig) != (macd.shift(1) > macd_sig.shift(1))).astype(float)
        f['macd_bullish'] = (macd > macd_sig).astype(float)
        f['macd_momentum'] = macd - macd_sig
        f['macd_direction'] = np.sign(f['macd_hist'].diff(3))
        
        # EMAs
        ema5 = c.ewm(span=5).mean()
        ema9 = c.ewm(span=9).mean()
        ema10 = c.ewm(span=10).mean()
        ema20 = c.ewm(span=20).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        ema200 = c.ewm(span=200).mean()
        
        f['ema_micro'] = (ema5 - ema10) / c * 100
        f['ema_slope'] = ema5.pct_change(2) * 100
        f['ema_momentum'] = (c - ema21) / ema21 * 100
        f['ema_alignment'] = ((ema9 > ema21) & (ema21 > ema50)).astype(float) - \
                            ((ema9 < ema21) & (ema21 < ema50)).astype(float)
        f['ema_stack'] = ((ema20 > ema50) & (ema50 > ema200)).astype(float)
        f['trend_aligned'] = np.sign(c - ema10) * np.sign(ema10 - ema20)
        f['micro_trend'] = np.sign(c.diff(3))
        f['trend_bullish'] = ((c > ema20) & (ema20 > ema50)).astype(float)
        
        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_up = sma20 + 2 * std20
        bb_lo = sma20 - 2 * std20
        f['bb_position'] = (c - bb_lo) / (bb_up - bb_lo + 1e-10)
        f['bb_width'] = (bb_up - bb_lo) / sma20
        
        # Volume
        vol_ma = v.rolling(10).mean()
        vol_ma_20 = v.rolling(20).mean()
        f['volume_spike'] = v / (vol_ma + 1e-10)
        f['volume_surge'] = (v > vol_ma * 2).astype(float)
        f['volume_surge_pct'] = v / (vol_ma + 1)
        f['volume_trend'] = vol_ma.pct_change(3)
        f['volume_confirms'] = (v > vol_ma_20).astype(float)
        
        # ATR / Volatility
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(10).mean()
        f['volatility_now'] = (h - l) / c * 100
        f['vol_expansion'] = (tr > atr * 1.5).astype(float)
        f['atr_spike'] = tr / (atr + 1e-10)
        
        # Candle
        body = abs(c - o)
        range_ = h - l + 1e-10
        f['candle_body'] = body / range_
        upper_wick = h - np.maximum(c, o)
        lower_wick = np.minimum(c, o) - l
        f['candle_wick_ratio'] = (upper_wick - lower_wick) / range_
        
        # Trend / Price strength
        high_20 = h.rolling(20).max()
        low_20 = l.rolling(20).min()
        f['price_strength'] = (c - low_20) / (high_20 - low_20 + 1e-10)
        f['price_position'] = f['price_strength']
        f['breakout'] = ((c > high_20.shift(1)) | (c < low_20.shift(1))).astype(float)
        f['breakout_up'] = (c > high_20.shift(1)).astype(float)
        
        # Price near support
        low_10 = l.rolling(10).min()
        f['price_near_support'] = (c < low_10 * 1.01).astype(float)
        
        # Momentum burst
        pct_1 = c.pct_change(1).abs() * 100
        pct_2 = c.pct_change(2).abs() * 100
        avg_move = pct_2.rolling(20).mean()
        f['momentum_burst'] = (pct_2 > avg_move * 2).astype(float)
        f['burst_strength'] = pct_2 / (avg_move + 0.01)
        strong_move = pct_1 > pct_1.rolling(20).quantile(0.8)
        f['burst_duration'] = strong_move.groupby((~strong_move).cumsum()).cumcount()
        f['price_accel'] = f['momentum_1'] - f['momentum_1'].shift(1)
        f['accel_positive'] = (f['price_accel'] > 0).astype(float)
        
        # Trend strength
        plus_dm = ((h - h.shift()).where((h - h.shift()) > (l.shift() - l), 0)).rolling(14).mean()
        minus_dm = ((l.shift() - l).where((l.shift() - l) > (h - h.shift()), 0)).rolling(14).mean()
        dx = abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-10)
        f['trend_strength'] = dx
        
        # Normalize
        for col in f.columns:
            if f[col].std() > 0 and f[col].dtype != bool:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f[[c for c in feature_list if c in f.columns]]
    
    def backtest_model(self, model_path: Path) -> dict:
        """Backtest a single model"""
        print(f"\n{'='*60}")
        print(f"Backtesting: {model_path.name}")
        print("="*60)
        
        # Extract model_id (filename without .nexmodel extension)
        model_id = model_path.stem
        
        # Load secured model container
        secured_model = self.security.load_secured_model(model_id)
        if not secured_model:
            return {'error': 'Failed to load model', 'model': model_path.name}
        
        # Decrypt to get actual package
        pkg = self.security.decrypt_model(secured_model)
        if not pkg:
            return {'error': 'Failed to decrypt model', 'model': model_path.name}
        
        meta = secured_model.metadata
        
        symbol = meta.get('symbol', 'BTCUSD')
        features = pkg.get('features', [])
        threshold = pkg.get('confidence_threshold', 0.5)
        model = pkg.get('model')
        scaler = pkg.get('scaler')
        
        print(f"Symbol: {symbol}")
        print(f"Threshold: {threshold:.0%}")
        print(f"Features: {len(features)}")
        
        # Load data
        df = self.load_ohlcv(symbol)
        
        # Use last 20% as test (unseen data)
        test_size = int(len(df) * 0.2)
        df_test = df.iloc[-test_size:].copy().reset_index(drop=True)
        
        print(f"Test period: {df_test['time'].iloc[0]} to {df_test['time'].iloc[-1]}")
        print(f"Test samples: {len(df_test)}")
        
        # Calculate features
        feat_df = self.calc_features(df_test, features)
        
        # Align with close prices
        valid_mask = ~feat_df.isna().any(axis=1)
        df_valid = df_test[valid_mask].reset_index(drop=True)
        feat_valid = feat_df[valid_mask].reset_index(drop=True)
        
        if len(feat_valid) < 100:
            return {'error': 'Not enough valid samples'}
        
        # Scale features
        X = feat_valid.values
        if scaler:
            X = scaler.transform(X)
        
        # Predict
        y_pred = model.predict(X)
        y_proba = model.predict_proba(X)
        max_proba = np.max(y_proba, axis=1)
        
        # Simulate trading
        spread_pct = 0.05 if 'btc' in symbol.lower() else 0.02  # Spread cost %
        
        # Track trades
        trades = []
        total_profit = 0
        wins = 0
        losses = 0
        
        close_prices = df_valid['close'].values
        
        for i in range(len(y_pred) - 4):  # Leave room for exit
            if max_proba[i] >= threshold and y_pred[i] != 1:  # Not HOLD
                signal = 'BUY' if y_pred[i] == 2 else 'SELL'
                entry_price = close_prices[i]
                
                # Exit after 3 bars (simple)
                exit_price = close_prices[i + 3]
                
                if signal == 'BUY':
                    profit_pct = (exit_price / entry_price - 1) * 100 - spread_pct
                else:
                    profit_pct = (entry_price / exit_price - 1) * 100 - spread_pct
                
                trades.append({
                    'signal': signal,
                    'entry': entry_price,
                    'exit': exit_price,
                    'profit_pct': profit_pct
                })
                
                total_profit += profit_pct
                if profit_pct > 0:
                    wins += 1
                else:
                    losses += 1
        
        num_trades = len(trades)
        win_rate = wins / num_trades * 100 if num_trades > 0 else 0
        avg_profit = total_profit / num_trades if num_trades > 0 else 0
        
        # Calculate max drawdown
        cumulative = np.cumsum([t['profit_pct'] for t in trades]) if trades else [0]
        peak = np.maximum.accumulate(cumulative)
        drawdown = peak - cumulative
        max_dd = np.max(drawdown) if len(drawdown) > 0 else 0
        
        result = {
            'symbol': symbol,
            'model': model_path.name,
            'trades': num_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_profit_pct': total_profit,
            'avg_profit_pct': avg_profit,
            'max_drawdown_pct': max_dd,
            'profitable': total_profit > 0,
            'threshold': threshold
        }
        
        print(f"\n📊 Results:")
        print(f"  Trades: {num_trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Total Profit: {total_profit:.2f}%")
        print(f"  Avg Profit: {avg_profit:.3f}%")
        print(f"  Max Drawdown: {max_dd:.2f}%")
        
        status = "✅ PROFITABLE" if total_profit > 0 else "❌ NOT PROFITABLE"
        print(f"\n{status}")
        
        return result
    
    def backtest_all(self):
        """Backtest all available models"""
        models_dir = Path.home() / ".nexustrade" / "models"
        model_files = list(models_dir.glob("*.nexmodel"))
        
        print(f"Found {len(model_files)} models")
        
        results = []
        for mf in model_files:
            try:
                result = self.backtest_model(mf)
                results.append(result)
            except Exception as e:
                print(f"Error: {e}")
                results.append({'model': mf.name, 'error': str(e)})
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("MODEL PROFITABILITY VALIDATION")
    print("="*60)
    
    bt = ModelBacktester()
    results = bt.backtest_all()
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    profitable = []
    unprofitable = []
    
    for r in results:
        if 'error' in r:
            print(f"❌ {r['model']}: ERROR - {r['error']}")
        elif r['profitable']:
            profitable.append(r)
            print(f"✅ {r['model']}: +{r['total_profit_pct']:.2f}% ({r['win_rate']:.1f}% WR)")
        else:
            unprofitable.append(r)
            print(f"⚠️ {r['model']}: {r['total_profit_pct']:.2f}% ({r['win_rate']:.1f}% WR)")
    
    print(f"\n📈 Profitable: {len(profitable)}")
    print(f"📉 Unprofitable: {len(unprofitable)}")
