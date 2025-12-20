"""
Custom EMA-CCI Strategy Trainer
Based on user-defined strategy:
- EMA 50, EMA 110, EMA 200 alignment
- CCI 20 range -100 to 0 for entry
- SL 2 points below EMA 200
- Risk:Reward 1:3
- Timeframe: 15M
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


class EMACCIStrategyTrainer:
    """
    Strategy Rules:
    1. Trend: EMA50 > EMA110 > EMA200 (bullish), opposite for bearish
    2. Entry: CCI 20 between -100 and 0 (oversold but not extreme)
    3. SL: 2 points below EMA200
    4. TP: SL * 3 (1:3 RR)
    """
    
    FEATURES = [
        # EMA Alignment
        'ema_bullish_align', 'ema_bearish_align',
        'ema50_above_110', 'ema110_above_200',
        'price_above_ema50', 'price_above_ema200',
        # Distance from EMAs
        'dist_ema50', 'dist_ema110', 'dist_ema200',
        # CCI
        'cci', 'cci_in_buy_zone', 'cci_in_sell_zone',
        'cci_rising', 'cci_momentum',
        # Trend strength
        'ema_slope_50', 'ema_slope_200',
        # Price action
        'candle_bullish', 'candle_bearish',
        'momentum'
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
        # Use 2 years
        cutoff = df['time'].max() - pd.Timedelta(days=730)
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
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        print(f"  Loaded {len(df)} rows")
        return df
    
    def calc_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index"""
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(period).mean()
        mean_dev = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - sma_tp) / (0.015 * mean_dev)
        return cci
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA-CCI strategy features"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        o = df['open'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        
        # EMAs
        ema50 = c.ewm(span=50).mean()
        ema110 = c.ewm(span=110).mean()
        ema200 = c.ewm(span=200).mean()
        
        # EMA Alignment
        f['ema_bullish_align'] = ((ema50 > ema110) & (ema110 > ema200)).astype(float)
        f['ema_bearish_align'] = ((ema50 < ema110) & (ema110 < ema200)).astype(float)
        f['ema50_above_110'] = (ema50 > ema110).astype(float)
        f['ema110_above_200'] = (ema110 > ema200).astype(float)
        f['price_above_ema50'] = (c > ema50).astype(float)
        f['price_above_ema200'] = (c > ema200).astype(float)
        
        # Distance from EMAs (normalized)
        f['dist_ema50'] = (c - ema50) / c * 100
        f['dist_ema110'] = (c - ema110) / c * 100
        f['dist_ema200'] = (c - ema200) / c * 100
        
        # CCI 20
        cci = self.calc_cci(df, 20)
        f['cci'] = cci
        # BUY zone: CCI between -100 and 0 (oversold recovery)
        f['cci_in_buy_zone'] = ((cci >= -100) & (cci <= 0)).astype(float)
        # SELL zone: CCI between 0 and 100 for shorts
        f['cci_in_sell_zone'] = ((cci >= 0) & (cci <= 100)).astype(float)
        f['cci_rising'] = (cci > cci.shift(2)).astype(float)
        f['cci_momentum'] = cci.diff(3)
        
        # EMA Slopes (trend strength)
        f['ema_slope_50'] = ema50.pct_change(5) * 100
        f['ema_slope_200'] = ema200.pct_change(5) * 100
        
        # Candle analysis
        f['candle_bullish'] = (c > o).astype(float)
        f['candle_bearish'] = (c < o).astype(float)
        
        # Momentum
        f['momentum'] = c.pct_change(4) * 100
        
        # Normalize continuous features
        for col in ['dist_ema50', 'dist_ema110', 'dist_ema200', 'cci', 
                    'cci_momentum', 'ema_slope_50', 'ema_slope_200', 'momentum']:
            if f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame, symbol: str) -> pd.Series:
        """
        Create labels based on 1:3 RR achievement
        BUY signal: Goes up more than 3x the distance to SL
        SELL signal: Goes down more than 3x the distance to SL
        """
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        
        ema200 = c.ewm(span=200).mean()
        
        # SL distance (2 points for gold, proportional for BTC)
        if 'BTC' in symbol.upper():
            sl_distance = c * 0.002  # 0.2% for BTC
            rr = 3.0
        else:
            sl_distance = 2.0  # 2 USD points for Gold
            rr = 3.0
        
        # Look ahead 8 bars (2 hours) to see if TP hit
        look_ahead = 8
        
        labels = pd.Series(1, index=df.index)  # HOLD
        
        for i in range(len(df) - look_ahead):
            entry = c.iloc[i]
            sl_long = ema200.iloc[i] - sl_distance if isinstance(sl_distance, float) else ema200.iloc[i] - sl_distance.iloc[i]
            tp_long = entry + (entry - sl_long) * rr
            
            sl_short = ema200.iloc[i] + sl_distance if isinstance(sl_distance, float) else ema200.iloc[i] + sl_distance.iloc[i]
            tp_short = entry - (sl_short - entry) * rr
            
            # Check forward bars
            future_high = h.iloc[i+1:i+look_ahead+1].max()
            future_low = l.iloc[i+1:i+look_ahead+1].min()
            
            # Check if TP hit before SL for BUY
            if future_high >= tp_long and future_low > sl_long:
                labels.iloc[i] = 2  # BUY
            # Check if TP hit before SL for SELL
            elif future_low <= tp_short and future_high < sl_short:
                labels.iloc[i] = 0  # SELL
        
        return labels
    
    def train(self, symbol: str, df: pd.DataFrame) -> dict:
        print(f"\n{'='*60}")
        print(f"EMA-CCI STRATEGY: {symbol}")
        print("EMA 50/110/200 + CCI 20 + RR 1:3")
        print("="*60)
        
        features = self.calc_features(df)
        labels = self.create_labels(df, symbol)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"\nSamples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"SELL: {lc.get(0,0)} | HOLD: {lc.get(1,0)} | BUY: {lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("\n📊 Training XGBoost with EMA-CCI Strategy...")
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            min_child_weight=10,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=2,
            random_state=42,
            eval_metric='mlogloss'
        )
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        y_proba = model.predict_proba(X_test_scaled)
        
        print("\n📈 Win Rate Analysis (with 1:3 RR):")
        best = {'threshold': 0.5, 'win_rate': 0, 'trades': 0, 'profit': 0}
        
        for thresh in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
            max_p = np.max(y_proba, axis=1)
            conf = max_p >= thresh
            trades = (y_pred != 1) & conf
            
            if trades.sum() >= 10:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                
                # Calculate profit with 1:3 RR
                # Win: +3 units, Loss: -1 unit
                wins = correct
                losses = trades.sum() - correct
                profit = wins * 3 - losses * 1
                profit_pct = profit / trades.sum() * 100  # Average per trade
                
                buy_mask = (y_pred == 2) & conf
                sell_mask = (y_pred == 0) & conf
                
                buy_prec = ((y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100) if buy_mask.sum() > 0 else 0
                sell_prec = ((y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100) if sell_mask.sum() > 0 else 0
                
                # With 1:3 RR, even 25% win rate is profitable
                is_profitable = profit > 0
                marker = "✅" if is_profitable else "⚠️"
                
                print(f"  {marker} {thresh:.0%}: Win {wr:.1f}%, Trades {trades.sum()}, Profit {profit:+.0f}R, BUY {buy_prec:.0f}%, SELL {sell_prec:.0f}%")
                
                if profit > best['profit']:
                    best = {'threshold': thresh, 'win_rate': wr, 'trades': int(trades.sum()), 
                           'profit': profit, 'buy_prec': buy_prec, 'sell_prec': sell_prec}
        
        acc = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print("📊 BEST RESULT (1:3 RR Strategy)")
        print("="*60)
        print(f"  Accuracy: {acc:.1%}")
        print(f"  Win Rate: {best['win_rate']:.1f}%")
        print(f"  Trades: {best['trades']}")
        print(f"  Profit: {best['profit']:+.0f}R")
        print(f"  Threshold: {best['threshold']:.0%}")
        
        if best['profit'] > 0:
            print(f"\n✅ STRATEGY IS PROFITABLE!")
        else:
            print(f"\n⚠️ Strategy needs optimization")
        
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
                'win_rate': float(best['win_rate']),
                'profit_r': float(best['profit']),
                'trades': int(best['trades']),
                'threshold': float(best['threshold']),
                'buy_precision': float(best.get('buy_prec', 0)),
                'sell_precision': float(best.get('sell_prec', 0))
            }
        }
    
    def save(self, result: dict, symbol: str) -> str:
        model_id = f"{symbol.lower()}_emacci_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'model_type': 'xgboost',
            'strategy': 'ema-cci-rr13',
            'confidence_threshold': result['metrics']['threshold'],
            'ema_periods': [50, 110, 200],
            'cci_period': 20,
            'risk_reward': 3.0
        }
        
        meta = {
            'symbol': symbol,
            'version': 'ema_cci_v1',
            'strategy_desc': 'EMA50/110/200 + CCI20 + RR 1:3',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Saved: {model_id}")
        print(f"   Path: {path}")
        return model_id
    
    def run(self):
        """Train for both symbols"""
        results = {}
        
        # XAUUSD
        print("\n" + "="*60)
        print("XAUUSD")
        print("="*60)
        try:
            df = self.load_xauusd()
            res = self.train("XAUUSD", df)
            mid = self.save(res, "XAUUSD")
            results['XAUUSD'] = {'model_id': mid, **res['metrics']}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['XAUUSD'] = {'error': str(e)}
        
        # BTC
        print("\n" + "="*60)
        print("BTCUSD")
        print("="*60)
        try:
            df = self.load_btc()
            res = self.train("BTCUSD", df)
            mid = self.save(res, "BTCUSD")
            results['BTCUSD'] = {'model_id': mid, **res['metrics']}
        except Exception as e:
            import traceback
            traceback.print_exc()
            results['BTCUSD'] = {'error': str(e)}
        
        return results


if __name__ == "__main__":
    print("="*60)
    print("EMA-CCI STRATEGY TRAINING")
    print("EMA 50/110/200 + CCI 20 + RR 1:3")
    print("="*60)
    
    trainer = EMACCIStrategyTrainer()
    results = trainer.run()
    
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    
    for symbol, data in results.items():
        if 'error' in data:
            print(f"❌ {symbol}: {data['error']}")
        else:
            marker = "✅" if data['profit_r'] > 0 else "⚠️"
            print(f"\n{marker} {symbol}:")
            print(f"   Model: {data['model_id']}")
            print(f"   Win Rate: {data['win_rate']:.1f}%")
            print(f"   Profit: {data['profit_r']:+.0f}R")
            print(f"   Trades: {data['trades']}")
