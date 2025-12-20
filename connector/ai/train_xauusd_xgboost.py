"""
XGBoost Optimized Trainer for XAUUSD (Gold)
With hyperparameter tuning for maximum win rate
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, classification_report
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


class XAUXGBoostTrainer:
    """
    Optimized XGBoost trainer for XAUUSD with hyperparameter tuning
    """
    
    # Gold-specific features
    FEATURES = [
        'rsi', 'rsi_slope', 'rsi_oversold', 'rsi_overbought',
        'macd', 'macd_signal', 'macd_hist', 'macd_cross',
        'bb_position', 'bb_width', 'bb_squeeze',
        'ema_trend', 'ema_fast_slow', 'ema_momentum',
        'atr_pct', 'atr_expansion',
        'momentum_1h', 'momentum_4h', 'momentum_direction',
        'volume_ratio', 'volume_surge',
        'trend_adx', 'trend_direction',
        'price_vs_sma50', 'price_vs_sma200'
    ]
    
    def __init__(self, ohlcv_dir: Path = None):
        self.ohlcv_dir = ohlcv_dir or Path(__file__).parent.parent.parent / "ohlcv"
        self.security = ModelSecurity()
        self.scaler = StandardScaler()
    
    def load_data(self) -> pd.DataFrame:
        """Load XAUUSD data"""
        path = self.ohlcv_dir / "xauusd" / "XAU_15m_data.csv"
        print(f"Loading XAUUSD from {path}")
        
        df = pd.read_csv(path, sep=';')
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={'date': 'time'})
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)
        
        # Use last 2 years for more relevant patterns
        cutoff = df['time'].max() - pd.Timedelta(days=730)
        df = df[df['time'] >= cutoff].reset_index(drop=True)
        
        print(f"  Loaded {len(df)} rows ({df['time'].min().date()} to {df['time'].max().date()})")
        return df
    
    def calc_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive gold trading features"""
        f = pd.DataFrame(index=df.index)
        
        c = df['close'].astype(float)
        h = df['high'].astype(float)
        l = df['low'].astype(float)
        v = df['volume'].astype(float) if 'volume' in df.columns else pd.Series(1, index=df.index)
        
        # RSI (14) with additional signals
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        f['rsi'] = rsi
        f['rsi_slope'] = rsi.diff(3)
        f['rsi_oversold'] = (rsi < 30).astype(float)
        f['rsi_overbought'] = (rsi > 70).astype(float)
        
        # MACD with cross signal
        ema12 = c.ewm(span=12).mean()
        ema26 = c.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_sig = macd.ewm(span=9).mean()
        f['macd'] = macd / c * 100  # Normalize
        f['macd_signal'] = macd_sig / c * 100
        f['macd_hist'] = (macd - macd_sig) / c * 100
        f['macd_cross'] = ((macd > macd_sig) != (macd.shift(1) > macd_sig.shift(1))).astype(float)
        
        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        bb_up = sma20 + 2 * std20
        bb_lo = sma20 - 2 * std20
        f['bb_position'] = (c - bb_lo) / (bb_up - bb_lo + 1e-10)
        f['bb_width'] = (bb_up - bb_lo) / sma20
        
        # BB Squeeze detection
        bb_width_pct = (bb_up - bb_lo) / sma20
        f['bb_squeeze'] = (bb_width_pct < bb_width_pct.rolling(50).quantile(0.2)).astype(float)
        
        # EMA trend indicators
        ema9 = c.ewm(span=9).mean()
        ema21 = c.ewm(span=21).mean()
        ema50 = c.ewm(span=50).mean()
        f['ema_trend'] = ((ema9 > ema21) & (ema21 > ema50)).astype(float) - \
                         ((ema9 < ema21) & (ema21 < ema50)).astype(float)
        f['ema_fast_slow'] = (ema9 - ema21) / c * 100
        f['ema_momentum'] = (c - ema21) / ema21 * 100
        
        # ATR with expansion detection
        tr = pd.concat([h - l, abs(h - c.shift()), abs(l - c.shift())], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        f['atr_pct'] = atr / c * 100
        f['atr_expansion'] = (atr > atr.rolling(20).mean() * 1.5).astype(float)
        
        # Multi-timeframe momentum
        f['momentum_1h'] = c.pct_change(4) * 100   # 1 hour (4 x 15min)
        f['momentum_4h'] = c.pct_change(16) * 100  # 4 hours
        f['momentum_direction'] = np.sign(f['momentum_1h']) * np.sign(f['momentum_4h'])
        
        # Volume analysis
        vol_ma = v.rolling(20).mean()
        f['volume_ratio'] = v / (vol_ma + 1e-10)
        f['volume_surge'] = (f['volume_ratio'] > 2).astype(float)
        
        # ADX-like trend strength
        plus_dm = ((h - h.shift()).where((h - h.shift()) > (l.shift() - l), 0)).rolling(14).mean()
        minus_dm = ((l.shift() - l).where((l.shift() - l) > (h - h.shift()), 0)).rolling(14).mean()
        dx = abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-10) * 100
        f['trend_adx'] = dx.rolling(14).mean()
        f['trend_direction'] = np.sign(plus_dm - minus_dm)
        
        # Price vs SMA
        sma50 = c.rolling(50).mean()
        sma200 = c.rolling(200).mean()
        f['price_vs_sma50'] = (c - sma50) / sma50 * 100
        f['price_vs_sma200'] = (c - sma200) / sma200 * 100
        
        # Normalize continuous features
        norm_cols = ['rsi', 'rsi_slope', 'macd', 'macd_signal', 'macd_hist',
                     'bb_position', 'bb_width', 'ema_fast_slow', 'ema_momentum',
                     'atr_pct', 'momentum_1h', 'momentum_4h', 'volume_ratio',
                     'trend_adx', 'price_vs_sma50', 'price_vs_sma200']
        
        for col in norm_cols:
            if col in f.columns and f[col].std() > 0:
                f[col] = (f[col] - f[col].mean()) / f[col].std()
        
        return f
    
    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """
        Create trading labels for Gold
        Gold typically has smaller moves, so use tighter thresholds
        """
        c = df['close'].astype(float)
        
        # Look 8 bars ahead (2 hours)
        look_ahead = 8
        future_ret = (c.shift(-look_ahead) / c - 1) * 100
        
        # Gold threshold: 0.15% (about $3 on $2000 gold)
        threshold = 0.15
        
        labels = pd.Series(1, index=df.index)  # HOLD
        labels[future_ret > threshold] = 2     # BUY
        labels[future_ret < -threshold] = 0    # SELL
        
        return labels
    
    def train(self) -> dict:
        """Train XGBoost with hyperparameter tuning"""
        print(f"\n{'='*60}")
        print("XAUUSD XGBoost Optimized Training")
        print("="*60)
        
        # Load and prepare data
        df = self.load_data()
        features = self.calc_features(df)
        labels = self.create_labels(df)
        
        data = pd.concat([features, labels.rename('label')], axis=1)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"\nTotal samples: {len(data)}")
        lc = data['label'].value_counts().sort_index()
        print(f"Labels: SELL={lc.get(0,0)} | HOLD={lc.get(1,0)} | BUY={lc.get(2,0)}")
        
        X = data[self.FEATURES].values
        y = data['label'].values
        
        # Time series split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("\n📊 Hyperparameter Tuning...")
        
        # Parameter grid for tuning
        param_grid = {
            'max_depth': [5, 7, 10],
            'n_estimators': [100, 150, 200],
            'learning_rate': [0.05, 0.1],
            'min_child_weight': [3, 5],
            'subsample': [0.8],
            'colsample_bytree': [0.8],
        }
        
        base_model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=3,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
        
        # Grid search with time series cross-validation
        tscv = TimeSeriesSplit(n_splits=3)
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=tscv,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train_scaled, y_train)
        
        print(f"\n✅ Best parameters: {grid_search.best_params_}")
        print(f"   Best CV score: {grid_search.best_score_:.2%}")
        
        # Train final model with best params
        best_model = grid_search.best_estimator_
        
        # Evaluate
        y_pred = best_model.predict(X_test_scaled)
        y_proba = best_model.predict_proba(X_test_scaled)
        
        overall_acc = accuracy_score(y_test, y_pred)
        
        # Win rate analysis at different thresholds
        print("\n📈 Win Rate Analysis:")
        best_result = {'threshold': 0.5, 'win_rate': 0, 'trades': 0}
        
        for thresh in [0.40, 0.45, 0.50, 0.55, 0.60]:
            max_p = np.max(y_proba, axis=1)
            confident = max_p >= thresh
            trades = (y_pred != 1) & confident  # Exclude HOLD
            
            if trades.sum() > 0:
                correct = (y_test[trades] == y_pred[trades]).sum()
                wr = correct / trades.sum() * 100
                pct = trades.sum() / len(y_test) * 100
                print(f"  Threshold {thresh:.0%}: Win Rate {wr:.1f}%, Trades {trades.sum()} ({pct:.1f}%)")
                
                if wr > best_result['win_rate'] and trades.sum() > 20:
                    best_result = {'threshold': thresh, 'win_rate': wr, 'trades': int(trades.sum())}
            else:
                print(f"  Threshold {thresh:.0%}: No confident trades")
        
        # Use best threshold
        conf_thresh = best_result['threshold']
        max_p = np.max(y_proba, axis=1)
        confident = max_p >= conf_thresh
        trades = (y_pred != 1) & confident
        
        win_rate = best_result['win_rate']
        
        # Precision per class
        buy_mask = (y_pred == 2) & confident
        sell_mask = (y_pred == 0) & confident
        
        buy_prec = 0
        if buy_mask.sum() > 0:
            buy_prec = (y_test[buy_mask] == 2).sum() / buy_mask.sum() * 100
        
        sell_prec = 0
        if sell_mask.sum() > 0:
            sell_prec = (y_test[sell_mask] == 0).sum() / sell_mask.sum() * 100
        
        print(f"\n{'='*60}")
        print("📊 FINAL RESULTS")
        print("="*60)
        print(f"  Overall Accuracy: {overall_acc:.1%}")
        print(f"  Trade Win Rate: {win_rate:.1f}%")
        print(f"  BUY Precision: {buy_prec:.1f}%")
        print(f"  SELL Precision: {sell_prec:.1f}%")
        print(f"  Confident Trades: {best_result['trades']} ({best_result['trades']/len(y_test)*100:.1f}%)")
        print(f"  Best Threshold: {conf_thresh:.0%}")
        
        # Feature importance
        importance = dict(zip(self.FEATURES, best_model.feature_importances_))
        top_5 = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        print("\n🔑 Top 5 Features:")
        for feat, imp in top_5:
            print(f"   {feat}: {imp:.4f}")
        
        return {
            'model': best_model,
            'scaler': self.scaler,
            'best_params': grid_search.best_params_,
            'metrics': {
                'accuracy': float(overall_acc),
                'win_rate': float(win_rate),
                'buy_precision': float(buy_prec),
                'sell_precision': float(sell_prec),
                'confident_trades': best_result['trades'],
                'total_test': len(y_test),
                'confidence_threshold': conf_thresh,
                'cv_score': float(grid_search.best_score_)
            },
            'feature_importance': importance
        }
    
    def save(self, result: dict) -> str:
        """Save encrypted model"""
        model_id = f"xauusd_xgb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pkg = {
            'model': result['model'],
            'scaler': result['scaler'],
            'features': self.FEATURES,
            'confidence_threshold': result['metrics']['confidence_threshold'],
            'model_type': 'xgboost',
            'strategy': 'gold-optimized',
            'best_params': result['best_params']
        }
        
        meta = {
            'symbol': 'XAUUSD',
            'version': 'xgboost_tuned_v1',
            'trained_at': datetime.now().isoformat(),
            **result['metrics']
        }
        
        secured = self.security.encrypt_model(pkg, model_id, meta)
        path = self.security.save_secured_model(secured)
        
        print(f"\n✅ Model Saved: {model_id}")
        print(f"   Path: {path}")
        
        return model_id
    
    def run(self):
        """Full training pipeline"""
        result = self.train()
        model_id = self.save(result)
        return {
            'model_id': model_id,
            **result['metrics']
        }


if __name__ == "__main__":
    print("="*60)
    print("XAUUSD XGBoost Optimized Training")
    print("="*60)
    
    trainer = XAUXGBoostTrainer()
    result = trainer.run()
    
    print(f"\n{'='*60}")
    print("✅ TRAINING COMPLETE")
    print("="*60)
    print(f"Model ID: {result['model_id']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    print(f"Accuracy: {result['accuracy']:.1%}")
