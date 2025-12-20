'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';

export default function StrategyBuilderPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [generating, setGenerating] = useState(false);
    const [config, setConfig] = useState<any>(null);

    // Form state
    const [description, setDescription] = useState('');
    const [symbol, setSymbol] = useState('XAUUSD');
    const [timeframe, setTimeframe] = useState('M15');
    const [riskLevel, setRiskLevel] = useState<'low' | 'medium' | 'high'>('medium');
    const [modelName, setModelName] = useState('');

    const [error, setError] = useState('');
    const [quotaError, setQuotaError] = useState(false);

    const handleGenerateStrategy = async () => {
        if (!description.trim()) {
            setError('Please describe your strategy');
            return;
        }

        setGenerating(true);
        setError('');
        setQuotaError(false);

        try {
            const supabase = createClient();
            const { data: { user } } = await supabase.auth.getUser();

            if (!user) {
                router.push('/auth/login');
                return;
            }

            const response = await fetch('/api/optimize-strategy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description,
                    symbol,
                    timeframe,
                    risk_level: riskLevel,
                    user_id: user.id
                })
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 403) {
                    setQuotaError(true);
                    setError(data.message || 'Monthly quota exceeded');
                } else {
                    setError(data.message || 'Failed to generate strategy');
                }
                return;
            }

            setConfig(data.training_config);
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setGenerating(false);
        }
    };

    const handleStartTraining = () => {
        // TODO: Implement training initiation
        // This will require backend integration with Windows connector
        alert('Training feature will be available soon. Please use the Windows connector for now.');
    };

    return (
        <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', padding: '2rem' }}>
            {/* Header */}
            <div style={{ maxWidth: '1200px', margin: '0 auto', marginBottom: '2rem' }}>
                <Link href="/dashboard" style={{ color: '#06b6d4', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                    ← Back to Dashboard
                </Link>
                <h1 style={{ fontSize: '2rem', fontWeight: '700', color: '#fff', marginBottom: '0.5rem' }}>
                    🎯 AI Strategy Builder
                </h1>
                <p style={{ color: '#94a3b8', fontSize: '1rem' }}>
                    Create custom trading strategies with AI-powered optimization
                </p>
            </div>

            <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'grid', gridTemplateColumns: config ? '1fr 1fr' : '1fr', gap: '2rem' }}>
                {/* Input Form */}
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(10px)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.2)', padding: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#fff', marginBottom: '1.5rem' }}>
                        Strategy Configuration
                    </h2>

                    {/* Strategy Description */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                            Strategy Description *
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Describe your trading strategy in natural language...&#10;Example: 'Scalping strategy using RSI oversold/overbought levels with tight stop loss'"
                            style={{
                                width: '100%',
                                minHeight: '120px',
                                background: 'rgba(15, 23, 42, 0.8)',
                                border: '1px solid rgba(148, 163, 184, 0.2)',
                                borderRadius: '0.5rem',
                                padding: '0.75rem',
                                color: '#fff',
                                fontSize: '0.875rem',
                                resize: 'vertical'
                            }}
                        />
                    </div>

                    {/* Symbol */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                            Trading Symbol
                        </label>
                        <select
                            value={symbol}
                            onChange={(e) => setSymbol(e.target.value)}
                            style={{
                                width: '100%',
                                background: 'rgba(15, 23, 42, 0.8)',
                                border: '1px solid rgba(148, 163, 184, 0.2)',
                                borderRadius: '0.5rem',
                                padding: '0.75rem',
                                color: '#fff',
                                fontSize: '0.875rem'
                            }}
                        >
                            <option value="XAUUSD">XAUUSD (Gold)</option>
                            <option value="BTCUSD">BTCUSD (Bitcoin)</option>
                            <option value="EURUSD">EURUSD</option>
                            <option value="GBPUSD">GBPUSD</option>
                            <option value="USDJPY">USDJPY</option>
                        </select>
                    </div>

                    {/* Timeframe */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                            Timeframe
                        </label>
                        <select
                            value={timeframe}
                            onChange={(e) => setTimeframe(e.target.value)}
                            style={{
                                width: '100%',
                                background: 'rgba(15, 23, 42, 0.8)',
                                border: '1px solid rgba(148, 163, 184, 0.2)',
                                borderRadius: '0.5rem',
                                padding: '0.75rem',
                                color: '#fff',
                                fontSize: '0.875rem'
                            }}
                        >
                            <option value="M1">M1 (1 Minute)</option>
                            <option value="M5">M5 (5 Minutes)</option>
                            <option value="M15">M15 (15 Minutes)</option>
                            <option value="M30">M30 (30 Minutes)</option>
                            <option value="H1">H1 (1 Hour)</option>
                            <option value="H4">H4 (4 Hours)</option>
                            <option value="D1">D1 (Daily)</option>
                        </select>
                    </div>

                    {/* Risk Level */}
                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                            Risk Level
                        </label>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            {(['low', 'medium', 'high'] as const).map((level) => (
                                <button
                                    key={level}
                                    onClick={() => setRiskLevel(level)}
                                    style={{
                                        flex: 1,
                                        padding: '0.75rem',
                                        background: riskLevel === level ? 'rgba(6, 182, 212, 0.2)' : 'rgba(15, 23, 42, 0.8)',
                                        border: `1px solid ${riskLevel === level ? '#06b6d4' : 'rgba(148, 163, 184, 0.2)'}`,
                                        borderRadius: '0.5rem',
                                        color: riskLevel === level ? '#06b6d4' : '#94a3b8',
                                        fontSize: '0.875rem',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        textTransform: 'capitalize'
                                    }}
                                >
                                    {level}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div style={{
                            padding: '1rem',
                            background: quotaError ? 'rgba(234, 179, 8, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                            border: `1px solid ${quotaError ? '#eab308' : '#ef4444'}`,
                            borderRadius: '0.5rem',
                            marginBottom: '1.5rem'
                        }}>
                            <p style={{ color: quotaError ? '#eab308' : '#ef4444', fontSize: '0.875rem', margin: 0 }}>
                                {error}
                            </p>
                            {quotaError && (
                                <Link href="/dashboard?tab=settings" style={{ color: '#06b6d4', fontSize: '0.875rem', marginTop: '0.5rem', display: 'inline-block' }}>
                                    Upgrade to Pro →
                                </Link>
                            )}
                        </div>
                    )}

                    {/* Generate Button */}
                    <button
                        onClick={handleGenerateStrategy}
                        disabled={generating || !description.trim()}
                        style={{
                            width: '100%',
                            padding: '1rem',
                            background: generating || !description.trim() ? 'rgba(148, 163, 184, 0.2)' : 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
                            border: 'none',
                            borderRadius: '0.5rem',
                            color: '#fff',
                            fontSize: '1rem',
                            fontWeight: '600',
                            cursor: generating || !description.trim() ? 'not-allowed' : 'pointer',
                            opacity: generating || !description.trim() ? 0.5 : 1
                        }}
                    >
                        {generating ? '🤖 Generating Strategy...' : '✨ Generate Strategy with AI'}
                    </button>
                </div>

                {/* Config Preview */}
                {config && (
                    <div style={{ background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(10px)', borderRadius: '1rem', border: '1px solid rgba(6, 182, 212, 0.2)', padding: '2rem' }}>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: '600', color: '#fff', marginBottom: '1.5rem' }}>
                            AI-Optimized Configuration
                        </h2>

                        {/* Features */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h3 style={{ color: '#06b6d4', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                                Technical Indicators
                            </h3>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                {config.features.map((feature: string) => (
                                    <span key={feature} style={{
                                        padding: '0.25rem 0.75rem',
                                        background: 'rgba(6, 182, 212, 0.1)',
                                        border: '1px solid rgba(6, 182, 212, 0.3)',
                                        borderRadius: '9999px',
                                        color: '#06b6d4',
                                        fontSize: '0.75rem'
                                    }}>
                                        {feature}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Hyperparameters */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h3 style={{ color: '#06b6d4', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                                Model Hyperparameters
                            </h3>
                            <div style={{ background: 'rgba(15, 23, 42, 0.8)', borderRadius: '0.5rem', padding: '1rem' }}>
                                {Object.entries(config.hyperparameters).map(([key, value]) => (
                                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(148, 163, 184, 0.1)' }}>
                                        <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{key.replace(/_/g, ' ')}</span>
                                        <span style={{ color: '#fff', fontSize: '0.875rem', fontWeight: '500' }}>{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Risk Config */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <h3 style={{ color: '#06b6d4', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                                Risk Management
                            </h3>
                            <div style={{ background: 'rgba(15, 23, 42, 0.8)', borderRadius: '0.5rem', padding: '1rem' }}>
                                {Object.entries(config.risk_config).map(([key, value]) => (
                                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(148, 163, 184, 0.1)' }}>
                                        <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{key.replace(/_/g, ' ')}</span>
                                        <span style={{ color: '#fff', fontSize: '0.875rem', fontWeight: '500' }}>{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Reasoning */}
                        {config.reasoning && (
                            <div style={{ marginBottom: '1.5rem' }}>
                                <h3 style={{ color: '#06b6d4', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                                    AI Reasoning
                                </h3>
                                <p style={{ color: '#94a3b8', fontSize: '0.875rem', lineHeight: '1.6' }}>
                                    {config.reasoning}
                                </p>
                            </div>
                        )}

                        {/* Model Name Input */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{ display: 'block', color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                                Model Name (Optional)
                            </label>
                            <input
                                type="text"
                                value={modelName}
                                onChange={(e) => setModelName(e.target.value)}
                                placeholder="e.g., XAUUSD Scalper v1"
                                style={{
                                    width: '100%',
                                    background: 'rgba(15, 23, 42, 0.8)',
                                    border: '1px solid rgba(148, 163, 184, 0.2)',
                                    borderRadius: '0.5rem',
                                    padding: '0.75rem',
                                    color: '#fff',
                                    fontSize: '0.875rem'
                                }}
                            />
                        </div>

                        {/* Start Training Button */}
                        <button
                            onClick={handleStartTraining}
                            style={{
                                width: '100%',
                                padding: '1rem',
                                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                border: 'none',
                                borderRadius: '0.5rem',
                                color: '#fff',
                                fontSize: '1rem',
                                fontWeight: '600',
                                cursor: 'pointer'
                            }}
                        >
                            🚀 Start Training (Windows Connector Required)
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
