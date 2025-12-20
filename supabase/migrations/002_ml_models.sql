-- Migration: Add ML Models table and Storage
-- Description: Support for cloud-synced ML models with metadata and file storage

-- Create ml_models table
CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    model_type VARCHAR(50) NOT NULL DEFAULT 'gru_xgboost_hybrid',
    
    -- Performance metrics
    accuracy DECIMAL(5,2),
    win_rate DECIMAL(5,2),
    kelly_fraction DECIMAL(5,3),
    sharpe_ratio DECIMAL(5,3),
    max_drawdown DECIMAL(5,2),
    
    -- Configuration
    config JSONB,  -- LLM-generated or custom config
    features TEXT[],  -- Technical indicators used
    timeframe VARCHAR(10),
    
    -- Storage
    storage_path TEXT,  -- Path in Supabase Storage
    model_size_bytes BIGINT,
    
    -- Metadata
    model_name VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    training_duration_seconds INTEGER,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    
    -- Indexes
    CONSTRAINT unique_user_model_name UNIQUE(user_id, model_name)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_models_user_id ON ml_models(user_id);
CREATE INDEX IF NOT EXISTS idx_ml_models_symbol ON ml_models(symbol);
CREATE INDEX IF NOT EXISTS idx_ml_models_is_active ON ml_models(is_active);
CREATE INDEX IF NOT EXISTS idx_ml_models_created_at ON ml_models(created_at DESC);

-- Enable RLS
ALTER TABLE ml_models ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view their own models" ON ml_models;
DROP POLICY IF EXISTS "Users can insert their own models" ON ml_models;
DROP POLICY IF EXISTS "Users can update their own models" ON ml_models;
DROP POLICY IF EXISTS "Users can delete their own models" ON ml_models;

-- RLS Policies
CREATE POLICY "Users can view their own models"
    ON ml_models FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own models"
    ON ml_models FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own models"
    ON ml_models FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own models"
    ON ml_models FOR DELETE
    USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ml_models_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS ml_models_updated_at ON ml_models;

-- Trigger for updated_at
CREATE TRIGGER ml_models_updated_at
    BEFORE UPDATE ON ml_models
    FOR EACH ROW
    EXECUTE FUNCTION update_ml_models_updated_at();

-- Create Storage bucket for ML models (run this in Supabase Dashboard or via API)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('ml-models', 'ml-models', false);

-- Storage policies (after bucket creation)
-- CREATE POLICY "Users can upload their own models"
--     ON storage.objects FOR INSERT
--     WITH CHECK (bucket_id = 'ml-models' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users can view their own models"
--     ON storage.objects FOR SELECT
--     USING (bucket_id = 'ml-models' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users can update their own models"
--     ON storage.objects FOR UPDATE
--     USING (bucket_id = 'ml-models' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users can delete their own models"
--     ON storage.objects FOR DELETE
--     USING (bucket_id = 'ml-models' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Add comment
COMMENT ON TABLE ml_models IS 'Stores metadata for user-trained ML models with cloud sync support';
