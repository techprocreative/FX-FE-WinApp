import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import OpenAI from 'openai';

// Initialize Supabase client with service key for server-side operations
const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!
);

// Initialize OpenAI client for OpenRouter
const openai = new OpenAI({
    apiKey: process.env.OPENROUTER_API_KEY,
    baseURL: 'https://openrouter.ai/api/v1',
});

const STRATEGY_OPTIMIZER_PROMPT = `You are an expert trading strategy optimizer specializing in forex and cryptocurrency markets.

Given a user's strategy description, generate optimal configuration for ML model training using a GRU-XGBoost hybrid architecture.

Your output MUST be valid JSON with this exact structure:
{
  "features": ["array", "of", "technical", "indicators"],
  "model_type": "gru_xgboost_hybrid",
  "hyperparameters": {
    "gru_units": 64,
    "gru_dropout": 0.2,
    "xgb_max_depth": 5,
    "xgb_learning_rate": 0.05,
    "xgb_n_estimators": 100,
    "confidence_threshold": 0.65
  },
  "risk_config": {
    "sl_pips": 30,
    "tp_pips": 60,
    "max_positions": 1,
    "risk_percent": 1.0
  },
  "reasoning": "Brief explanation of choices"
}

Available features:
- rsi: Relative Strength Index (14)
- macd, macd_signal, macd_hist: MACD indicators
- bb_upper, bb_lower, bb_width, bb_position: Bollinger Bands
- ema_9, ema_21, ema_cross: Exponential Moving Averages
- atr, atr_percent: Average True Range
- price_change, price_change_5: Price momentum
- volume_ma, volume_ratio: Volume indicators

Consider:
1. Symbol characteristics (XAUUSD: high volatility, BTCUSD: crypto volatility, forex pairs: moderate)
2. Timeframe (M1-M5: scalping, M15-H1: intraday, H4-D1: swing)
3. Risk tolerance (conservative: lower risk_percent, aggressive: higher)
4. Strategy type (scalping: tight SL/TP, swing: wider SL/TP)

Output ONLY the JSON, no additional text.`;

interface StrategyRequest {
    description: string;
    symbol: string;
    timeframe?: string;
    risk_level?: 'low' | 'medium' | 'high';
    user_id: string;
}

interface TrainingConfig {
    features: string[];
    model_type: string;
    hyperparameters: {
        gru_units: number;
        gru_dropout: number;
        xgb_max_depth: number;
        xgb_learning_rate: number;
        xgb_n_estimators: number;
        confidence_threshold: number;
    };
    risk_config: {
        sl_pips: number;
        tp_pips: number;
        max_positions: number;
        risk_percent: number;
    };
    reasoning: string;
}

export async function POST(req: NextRequest) {
    try {
        const body: StrategyRequest = await req.json();
        const { description, symbol, timeframe = 'M15', risk_level = 'medium', user_id } = body;

        // Validate input
        if (!description || !symbol || !user_id) {
            return NextResponse.json(
                { error: 'Missing required fields: description, symbol, user_id' },
                { status: 400 }
            );
        }

        // Check user subscription tier
        const { data: subscription, error: subError } = await supabase
            .from('subscriptions')
            .select('tier, status, expires_at')
            .eq('user_id', user_id)
            .eq('status', 'active')
            .gt('expires_at', new Date().toISOString())
            .order('expires_at', { ascending: false })
            .limit(1)
            .single();

        // If no active subscription, check profile for default tier
        let userTier = 'free';
        if (subscription && !subError) {
            userTier = subscription.tier;
        } else {
            const { data: profile } = await supabase
                .from('profiles')
                .select('subscription_tier')
                .eq('id', user_id)
                .single();

            if (profile) {
                userTier = profile.subscription_tier || 'free';
            }
        }

        // Check quota for free tier
        if (userTier === 'free') {
            const startOfMonth = new Date();
            startOfMonth.setDate(1);
            startOfMonth.setHours(0, 0, 0, 0);

            const { count } = await supabase
                .from('llm_logs')
                .select('*', { count: 'exact', head: true })
                .eq('user_id', user_id)
                .eq('request_type', 'strategy_generation')
                .gte('created_at', startOfMonth.toISOString());

            if (count !== null && count >= 10) {
                return NextResponse.json(
                    {
                        error: 'Monthly quota exceeded',
                        message: 'You have reached your monthly limit of 10 AI strategy generations. Upgrade to Pro for unlimited access.',
                        quota_used: count,
                        quota_limit: 10
                    },
                    { status: 403 }
                );
            }
        }

        // Construct user prompt
        const userPrompt = `Strategy Description: ${description}
Symbol: ${symbol}
Timeframe: ${timeframe}
Risk Level: ${risk_level}

Generate optimal training configuration.`;

        // Call LLM
        const completion = await openai.chat.completions.create({
            model: 'anthropic/claude-3.5-sonnet',
            messages: [
                { role: 'system', content: STRATEGY_OPTIMIZER_PROMPT },
                { role: 'user', content: userPrompt }
            ],
            temperature: 0.7,
            max_tokens: 1000,
        });

        const llmResponse = completion.choices[0].message.content;

        if (!llmResponse) {
            throw new Error('Empty response from LLM');
        }

        // Parse JSON response
        let trainingConfig: TrainingConfig;
        try {
            // Remove markdown code blocks if present
            const cleanedResponse = llmResponse.replace(/```json\n?|\n?```/g, '').trim();
            trainingConfig = JSON.parse(cleanedResponse);
        } catch (parseError) {
            console.error('Failed to parse LLM response:', llmResponse);
            throw new Error('Invalid JSON response from LLM');
        }

        // Calculate cost (approximate)
        const promptTokens = completion.usage?.prompt_tokens || 0;
        const completionTokens = completion.usage?.completion_tokens || 0;
        // Claude 3.5 Sonnet pricing: $3/1M input, $15/1M output
        const totalCost = (promptTokens * 0.000003) + (completionTokens * 0.000015);

        // Log usage to Supabase
        await supabase.from('llm_logs').insert({
            user_id,
            provider: 'openrouter',
            model: 'claude-3.5-sonnet',
            prompt_tokens: promptTokens,
            completion_tokens: completionTokens,
            total_cost: totalCost,
            request_type: 'strategy_generation',
        });

        // Return training config
        return NextResponse.json({
            training_config: trainingConfig,
            estimated_duration: '15-20 minutes',
            symbol,
            timeframe,
            quota_info: {
                tier: userTier,
                used: userTier === 'free' ? (await getMonthlyUsage(user_id)) : null,
                limit: userTier === 'free' ? 10 : null
            }
        });

    } catch (error: any) {
        console.error('Strategy optimization error:', error);

        return NextResponse.json(
            {
                error: 'Strategy optimization failed',
                message: error.message || 'An unexpected error occurred',
                details: process.env.NODE_ENV === 'development' ? error.stack : undefined
            },
            { status: 500 }
        );
    }
}

async function getMonthlyUsage(userId: string): Promise<number> {
    const startOfMonth = new Date();
    startOfMonth.setDate(1);
    startOfMonth.setHours(0, 0, 0, 0);

    const { count } = await supabase
        .from('llm_logs')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', userId)
        .eq('request_type', 'strategy_generation')
        .gte('created_at', startOfMonth.toISOString());

    return count || 0;
}
