-- Insert metadata for uploaded models
-- Run this in Supabase SQL Editor

INSERT INTO ml_models (
    user_id,
    symbol,
    model_type,
    model_name,
    description,
    storage_path,
    model_size_bytes,
    accuracy,
    win_rate,
    is_active,
    timeframe,
    features
) VALUES
(
    '1e3388e6-8f27-4bbd-9819-daf4c84d3444',
    'BTCUSD',
    'gru_xgboost_hybrid',
    'btcusd_hybrid_20251220_104900',
    'Pre-trained GRU-XGBoost hybrid model for BTCUSD',
    '1e3388e6-8f27-4bbd-9819-daf4c84d3444/btcusd_hybrid_20251220_104900.nexmodel',
    679262,
    65.0,
    55.0,
    true,
    'M15',
    ARRAY['rsi', 'macd', 'bollinger', 'ema', 'atr']
),
(
    '1e3388e6-8f27-4bbd-9819-daf4c84d3444',
    'XAUUSD',
    'gru_xgboost_hybrid',
    'xauusd_hybrid_20251220_105109',
    'Pre-trained GRU-XGBoost hybrid model for XAUUSD',
    '1e3388e6-8f27-4bbd-9819-daf4c84d3444/xauusd_hybrid_20251220_105109.nexmodel',
    657600,
    65.0,
    55.0,
    true,
    'M15',
    ARRAY['rsi', 'macd', 'bollinger', 'ema', 'atr']
)
ON CONFLICT (user_id, model_name) 
DO UPDATE SET 
    storage_path = EXCLUDED.storage_path,
    model_size_bytes = EXCLUDED.model_size_bytes,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Verify insertion
SELECT id, symbol, model_name, storage_path, is_active 
FROM ml_models 
WHERE user_id = '1e3388e6-8f27-4bbd-9819-daf4c84d3444';
