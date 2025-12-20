"""
Convert existing XGBoost models to NexusTrade encrypted format
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent))
from security.model_security import ModelSecurity


def convert_existing_models():
    """Convert existing models to NexusTrade format"""
    models_dir = Path(__file__).parent.parent.parent / "models"
    security = ModelSecurity()
    
    # Find all pkl files
    model_files = list(models_dir.rglob("*.pkl"))
    print(f"Found {len(model_files)} model files\n")
    
    best_models = {}
    
    for mf in model_files:
        rel_path = mf.relative_to(models_dir)
        print(f"{'='*60}")
        print(f"📦 {rel_path}")
        
        try:
            data = joblib.load(mf)
            
            if isinstance(data, dict):
                # Get accuracy
                acc = data.get('accuracy', 0)
                if isinstance(acc, str):
                    acc = float(acc.replace('%', ''))
                
                symbol = data.get('symbol', 'UNKNOWN')
                if symbol == 'UNKNOWN':
                    if 'btc' in str(mf).lower() or 'crypto' in str(mf).lower():
                        symbol = 'BTCUSD'
                    elif 'xau' in str(mf).lower() or 'gold' in str(mf).lower():
                        symbol = 'XAUUSD'
                    elif 'eur' in str(mf).lower():
                        symbol = 'EURUSD'
                
                model_type = data.get('model_type', type(data.get('model', '')).__name__)
                features = data.get('feature_columns', data.get('features', []))
                strategy = data.get('strategy', 'standard')
                
                print(f"  Symbol: {symbol}")
                print(f"  Model: {model_type}")
                print(f"  Accuracy: {acc:.1f}%")
                print(f"  Features: {len(features)}")
                print(f"  Strategy: {strategy}")
                
                # Prefer crypto-optimized or forex-optimized models
                if 'optimized' in str(mf).lower():
                    priority = 2
                elif 'staging' in str(mf).lower():
                    priority = 1
                else:
                    priority = 0
                
                key = symbol
                if key not in best_models or priority > best_models[key]['priority'] or \
                   (priority == best_models[key]['priority'] and acc > best_models[key]['accuracy']):
                    best_models[key] = {
                        'path': mf,
                        'accuracy': acc,
                        'priority': priority,
                        'data': data
                    }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("🏆 BEST MODELS SELECTED")
    print("="*60)
    
    for symbol, info in best_models.items():
        print(f"\n{symbol}:")
        print(f"  Path: {info['path'].relative_to(models_dir)}")
        print(f"  Accuracy: {info['accuracy']:.1f}%")
    
    # Convert best models
    print(f"\n{'='*60}")
    print("📝 CONVERTING TO NEXUSTRADE FORMAT")
    print("="*60)
    
    converted = {}
    
    for symbol, info in best_models.items():
        data = info['data']
        
        if 'model' in data:
            model_id = f"{symbol.lower()}_prod_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            pkg = {
                'model': data['model'],
                'scaler': data.get('scaler'),
                'features': data.get('feature_columns', data.get('features', [])),
                'confidence_threshold': 0.55,
                'model_type': data.get('model_type', 'xgboost'),
                'strategy': data.get('strategy', 'standard')
            }
            
            meta = {
                'symbol': symbol,
                'source_file': str(info['path'].name),
                'accuracy': info['accuracy'],
                'spread_pips': data.get('spread_pips', 0),
                'profit_target_atr': data.get('profit_target_atr', 1.5),
                'stop_loss_atr': data.get('stop_loss_atr', 1.0),
                'trained_at': data.get('trained_at', 'unknown'),
                'converted_at': datetime.now().isoformat()
            }
            
            try:
                secured = security.encrypt_model(pkg, model_id, meta)
                path = security.save_secured_model(secured)
                
                print(f"\n✅ {symbol}:")
                print(f"   Model ID: {model_id}")
                print(f"   Accuracy: {info['accuracy']:.1f}%")
                print(f"   Saved: {path}")
                
                converted[symbol] = {
                    'model_id': model_id,
                    'accuracy': info['accuracy'],
                    'path': str(path)
                }
            except Exception as e:
                print(f"\n❌ {symbol}: Failed - {e}")
    
    print(f"\n{'='*60}")
    print("✅ CONVERSION COMPLETE")
    print("="*60)
    print(f"Converted {len(converted)} models")
    
    return converted


if __name__ == "__main__":
    convert_existing_models()
