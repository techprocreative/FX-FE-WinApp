-- NexusTrade Database Schema
-- Migration: 001_initial_schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Profiles (extends Supabase Auth)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'basic', 'pro', 'enterprise')),
    subscription_expires_at TIMESTAMPTZ,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE public.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    permissions JSONB DEFAULT '["read"]',
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tier TEXT NOT NULL CHECK (tier IN ('basic', 'pro', 'enterprise')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'cancelled', 'expired')),
    payment_method TEXT DEFAULT 'bank_transfer',
    payment_proof_url TEXT,
    admin_notes TEXT,
    starts_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES public.profiles(id)
);

-- MT5 Connections
CREATE TABLE public.mt5_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    connection_name TEXT NOT NULL,
    mt5_login TEXT,
    mt5_server TEXT,
    hwid TEXT,
    is_online BOOLEAN DEFAULT false,
    last_heartbeat TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trading History
CREATE TABLE public.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    connection_id UUID REFERENCES public.mt5_connections(id),
    ticket BIGINT NOT NULL,
    symbol TEXT NOT NULL,
    trade_type TEXT NOT NULL CHECK (trade_type IN ('buy', 'sell')),
    volume DECIMAL(10,2) NOT NULL,
    open_price DECIMAL(10,5) NOT NULL,
    close_price DECIMAL(10,5),
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ,
    profit DECIMAL(10,2),
    commission DECIMAL(10,2),
    swap DECIMAL(10,2),
    comment TEXT,
    magic_number INTEGER,
    is_auto_trade BOOLEAN DEFAULT false,
    ml_model_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ML Models
CREATE TABLE public.ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    model_type TEXT NOT NULL CHECK (model_type IN ('scalping', 'swing', 'trend_following', 'mean_reversion')),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL CHECK (timeframe IN ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1')),
    model_hash TEXT,
    version INTEGER DEFAULT 1,
    accuracy DECIMAL(5,2),
    win_rate DECIMAL(5,2),
    profit_factor DECIMAL(10,2),
    is_active BOOLEAN DEFAULT false,
    auto_trade_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Backtest Results
CREATE TABLE public.backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    model_id UUID REFERENCES public.ml_models(id),
    strategy_config JSONB NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_balance DECIMAL(10,2) NOT NULL,
    final_balance DECIMAL(10,2),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    profit_factor DECIMAL(10,2),
    max_drawdown DECIMAL(10,2),
    sharpe_ratio DECIMAL(10,2),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- LLM Usage Logs
CREATE TABLE public.llm_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    provider TEXT NOT NULL DEFAULT 'openrouter',
    model TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_cost DECIMAL(10,6),
    request_type TEXT CHECK (request_type IN ('strategy_generation', 'analysis', 'chat', 'other')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX idx_mt5_connections_user_id ON public.mt5_connections(user_id);
CREATE INDEX idx_trades_user_id ON public.trades(user_id);
CREATE INDEX idx_trades_symbol ON public.trades(symbol);
CREATE INDEX idx_trades_open_time ON public.trades(open_time);
CREATE INDEX idx_ml_models_user_id ON public.ml_models(user_id);
CREATE INDEX idx_backtests_user_id ON public.backtests(user_id);
CREATE INDEX idx_llm_logs_user_id ON public.llm_logs(user_id);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mt5_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ml_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.backtests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.llm_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for profiles
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- RLS Policies for api_keys
CREATE POLICY "Users can view own API keys" ON public.api_keys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own API keys" ON public.api_keys
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own API keys" ON public.api_keys
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for subscriptions
CREATE POLICY "Users can view own subscriptions" ON public.subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create subscription requests" ON public.subscriptions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can manage all subscriptions" ON public.subscriptions
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND is_admin = true)
    );

-- RLS Policies for mt5_connections
CREATE POLICY "Users can manage own connections" ON public.mt5_connections
    FOR ALL USING (auth.uid() = user_id);

-- RLS Policies for trades
CREATE POLICY "Users can view own trades" ON public.trades
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own trades" ON public.trades
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for ml_models
CREATE POLICY "Users can manage own models" ON public.ml_models
    FOR ALL USING (auth.uid() = user_id);

-- RLS Policies for backtests
CREATE POLICY "Users can manage own backtests" ON public.backtests
    FOR ALL USING (auth.uid() = user_id);

-- RLS Policies for llm_logs
CREATE POLICY "Users can view own LLM logs" ON public.llm_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own LLM logs" ON public.llm_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to check subscription status
CREATE OR REPLACE FUNCTION public.check_subscription_status(p_user_id UUID)
RETURNS TABLE (
    is_active BOOLEAN,
    tier TEXT,
    expires_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE WHEN s.expires_at > NOW() AND s.status = 'active' THEN true ELSE false END,
        COALESCE(s.tier, 'free'),
        s.expires_at
    FROM public.profiles p
    LEFT JOIN public.subscriptions s ON s.user_id = p.id 
        AND s.status = 'active' 
        AND s.expires_at > NOW()
    WHERE p.id = p_user_id
    ORDER BY s.expires_at DESC NULLS LAST
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify API key
CREATE OR REPLACE FUNCTION public.verify_api_key(p_key_hash TEXT)
RETURNS TABLE (
    user_id UUID,
    permissions JSONB,
    is_valid BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ak.user_id,
        ak.permissions,
        CASE 
            WHEN ak.is_active = true 
                AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
            THEN true 
            ELSE false 
        END
    FROM public.api_keys ak
    WHERE ak.key_hash = p_key_hash;
    
    -- Update last used timestamp
    UPDATE public.api_keys 
    SET last_used_at = NOW() 
    WHERE key_hash = p_key_hash;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
