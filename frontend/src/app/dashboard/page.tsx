'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

interface MT5Connection {
    id: string;
    connection_name: string;
    is_online: boolean;
    mt5_login: string;
    mt5_server: string;
    last_heartbeat: string;
}

interface Trade {
    id: string;
    symbol: string;
    trade_type: string;
    volume: number;
    open_price: number;
    close_price: number | null;
    open_time: string;
    close_time: string | null;
    profit: number | null;
    is_auto_trade: boolean;
}

interface MLModel {
    id: string;
    name: string;
    symbol: string;
    win_rate: number;
    is_active: boolean;
    auto_trade_enabled: boolean;
}

interface Subscription {
    tier: string;
    status: string;
    expires_at: string;
}

export default function DashboardPage() {
    const router = useRouter();
    const supabase = createClient();

    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    // Data states
    const [mt5Connection, setMt5Connection] = useState<any>(null);
    const [trades, setTrades] = useState<any[]>([]);
    const [mlModels, setMlModels] = useState<any[]>([]);
    const [subscription, setSubscription] = useState<any>(null);
    const [llmUsage, setLlmUsage] = useState<number>(0);
    const [accountBalance, setAccountBalance] = useState(0);
    const [todayPL, setTodayPL] = useState(0);

    useEffect(() => {
        const checkAuth = async () => {
            const { data: { user } } = await supabase.auth.getUser();

            if (!user) {
                router.push('/auth/login');
                return;
            }

            setUser(user);
            await fetchDashboardData(user.id);
            setLoading(false);
        };

        checkAuth();
    }, [router]);

    const fetchDashboardData = async (userId: string) => {
        // Fetch MT5 connection
        const { data: connections } = await supabase
            .from('mt5_connections')
            .select('*')
            .eq('user_id', userId)
            .order('created_at', { ascending: false })
            .limit(1);

        if (connections && connections.length > 0) {
            setMt5Connection(connections[0]);
        }

        // Fetch trades
        const { data: tradesData } = await supabase
            .from('trades')
            .select('*')
            .eq('user_id', userId)
            .order('open_time', { ascending: false })
            .limit(50);

        if (tradesData) {
            setTrades(tradesData);

            // Calculate today's P/L
            const today = new Date().toISOString().split('T')[0];
            const todayTrades = tradesData.filter(t =>
                t.close_time && t.close_time.startsWith(today)
            );
            const pl = todayTrades.reduce((sum, t) => sum + (t.profit || 0), 0);
            setTodayPL(pl);
        }

        // Fetch ML models
        const { data: modelsData } = await supabase
            .from('ml_models')
            .select('*')
            .eq('user_id', userId);

        if (modelsData) {
            setMlModels(modelsData);
        }

        // Fetch subscription
        const { data: subData } = await supabase
            .from('subscriptions')
            .select('*')
            .eq('user_id', userId)
            .eq('status', 'active')
            .order('expires_at', { ascending: false })
            .limit(1);

        if (subData && subData.length > 0) {
            setSubscription(subData[0]);
        }

        // Fetch profile for subscription tier
        const { data: profileData } = await supabase
            .from('profiles')
            .select('subscription_tier')
            .eq('id', userId)
            .single();

        if (profileData && !subscription) {
            setSubscription({
                tier: profileData.subscription_tier || 'free',
                status: 'active',
                expires_at: ''
            });
        }

        // Fetch LLM usage (current month)
        const startOfMonth = new Date();
        startOfMonth.setDate(1);
        startOfMonth.setHours(0, 0, 0, 0);

        const { count } = await supabase
            .from('llm_logs')
            .select('*', { count: 'exact', head: true })
            .eq('user_id', userId)
            .eq('request_type', 'strategy_generation')
            .gte('created_at', startOfMonth.toISOString());

        setLlmUsage(count || 0);
    };

    const handleLogout = async () => {
        await supabase.auth.signOut();
        router.push('/');
    };

    if (loading) {
        return (
            <div style={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontFamily: 'system-ui, -apple-system, sans-serif'
            }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
                    <p>Loading...</p>
                </div>
            </div>
        );
    }

    const activeModelsCount = mlModels.filter(m => m.is_active).length;
    const mt5Status = mt5Connection?.is_online ? 'Connected' : 'Disconnected';
    const mt5StatusColor = mt5Connection?.is_online ? '#10b981' : '#94a3b8';

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            color: 'white'
        }}>
            {/* Sidebar */}
            <div style={{
                position: 'fixed',
                left: 0,
                top: 0,
                bottom: 0,
                width: '260px',
                background: 'rgba(15, 23, 42, 0.8)',
                backdropFilter: 'blur(16px)',
                borderRight: '1px solid rgba(6, 182, 212, 0.2)',
                padding: '2rem 0',
                display: 'flex',
                flexDirection: 'column'
            }}>
                {/* Logo */}
                <div style={{ padding: '0 1.5rem', marginBottom: '3rem' }}>
                    <h1 style={{
                        fontSize: '1.75rem',
                        fontWeight: '900',
                        background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        margin: 0
                    }}>
                        NexusTrade
                    </h1>
                </div>

                {/* Navigation */}
                <nav style={{ flex: 1, padding: '0 1rem' }}>
                    {[
                        { id: 'overview', icon: '📊', label: 'Overview' },
                        { id: 'trading', icon: '🤖', label: 'Auto-Trading' },
                        { id: 'models', icon: '🧠', label: 'ML Models' },
                        { id: 'history', icon: '📈', label: 'Trade History' },
                        { id: 'settings', icon: '⚙️', label: 'Settings' }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                width: '100%',
                                padding: '0.875rem 1rem',
                                marginBottom: '0.5rem',
                                background: activeTab === tab.id ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                                border: activeTab === tab.id ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid transparent',
                                borderRadius: '0.75rem',
                                color: activeTab === tab.id ? '#06b6d4' : '#94a3b8',
                                fontSize: '0.9375rem',
                                fontWeight: activeTab === tab.id ? '600' : '500',
                                cursor: 'pointer',
                                textAlign: 'left',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.75rem',
                                transition: 'all 0.3s'
                            }}
                            onMouseEnter={(e) => {
                                if (activeTab !== tab.id) {
                                    e.currentTarget.style.background = 'rgba(6, 182, 212, 0.05)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (activeTab !== tab.id) {
                                    e.currentTarget.style.background = 'transparent';
                                }
                            }}
                        >
                            <span style={{ fontSize: '1.25rem' }}>{tab.icon}</span>
                            {tab.label}
                        </button>
                    ))}

                    {/* Strategy Builder Link */}
                    <Link href="/dashboard/strategy-builder" style={{ textDecoration: 'none', display: 'block', marginTop: '0.5rem' }}>
                        <div style={{
                            width: '100%',
                            padding: '0.875rem 1rem',
                            background: 'transparent',
                            border: '1px solid transparent',
                            borderRadius: '0.75rem',
                            color: '#94a3b8',
                            fontSize: '0.9375rem',
                            fontWeight: '500',
                            cursor: 'pointer',
                            textAlign: 'left',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            transition: 'all 0.3s'
                        }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.background = 'rgba(6, 182, 212, 0.05)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.background = 'transparent';
                            }}
                        >
                            <span>🎯</span>
                            <span>Strategy Builder</span>
                        </div>
                    </Link>
                </nav>

                {/* User Section */}
                <div style={{ padding: '0 1.5rem', borderTop: '1px solid rgba(6, 182, 212, 0.2)', paddingTop: '1.5rem' }}>
                    <div style={{ marginBottom: '1rem' }}>
                        <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Logged in as</p>
                        <p style={{ fontSize: '0.9375rem', fontWeight: '600', color: 'white' }}>{user?.email}</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            background: 'rgba(244, 63, 94, 0.1)',
                            border: '1px solid rgba(244, 63, 94, 0.3)',
                            borderRadius: '0.75rem',
                            color: '#f43f5e',
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            transition: 'all 0.3s'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(244, 63, 94, 0.2)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'rgba(244, 63, 94, 0.1)';
                        }}
                    >
                        Logout
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div style={{ marginLeft: '260px', padding: '2rem' }}>
                {/* Header */}
                <div style={{ marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '0.5rem' }}>
                        {activeTab === 'overview' && 'Dashboard Overview'}
                        {activeTab === 'trading' && 'Auto-Trading'}
                        {activeTab === 'models' && 'ML Models'}
                        {activeTab === 'history' && 'Trade History'}
                        {activeTab === 'settings' && 'Settings'}
                    </h2>
                    <p style={{ color: '#94a3b8' }}>
                        {activeTab === 'overview' && 'Monitor your trading performance and account status'}
                        {activeTab === 'trading' && 'Manage automated trading with ML models'}
                        {activeTab === 'models' && 'Load and configure machine learning models'}
                        {activeTab === 'history' && 'View your complete trading history'}
                        {activeTab === 'settings' && 'Configure your account and preferences'}
                    </p>
                </div>

                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div>
                        {/* Stats Grid */}
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                            gap: '1.5rem',
                            marginBottom: '2rem'
                        }}>
                            {[
                                { label: 'MT5 Status', value: mt5Status, color: mt5StatusColor, icon: '🔌' },
                                { label: 'Account Balance', value: `$${accountBalance.toFixed(2)}`, color: '#06b6d4', icon: '💰' },
                                { label: 'Active Models', value: activeModelsCount.toString(), color: '#10b981', icon: '🤖' },
                                { label: 'Today P/L', value: `$${todayPL.toFixed(2)}`, color: todayPL >= 0 ? '#10b981' : '#f43f5e', icon: '📊' }
                            ].map((stat, idx) => (
                                <div key={idx} style={{
                                    background: 'rgba(30, 41, 59, 0.6)',
                                    borderRadius: '1.25rem',
                                    border: '1px solid rgba(6, 182, 212, 0.2)',
                                    padding: '1.5rem',
                                    backdropFilter: 'blur(16px)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                        <span style={{ fontSize: '1.5rem' }}>{stat.icon}</span>
                                        <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>{stat.label}</p>
                                    </div>
                                    <p style={{ fontSize: '1.75rem', fontWeight: '700', color: stat.color, margin: 0 }}>
                                        {stat.value}
                                    </p>
                                </div>
                            ))}
                        </div>

                        {/* Quick Actions */}
                        <div style={{ marginBottom: '2rem' }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#fff' }}>
                                Quick Actions
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                                {/* Strategy Builder Card */}
                                <Link href="/dashboard/strategy-builder" style={{ textDecoration: 'none' }}>
                                    <div style={{
                                        background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
                                        borderRadius: '1.25rem',
                                        border: '1px solid rgba(6, 182, 212, 0.3)',
                                        padding: '1.5rem',
                                        backdropFilter: 'blur(16px)',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s'
                                    }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.transform = 'translateY(-4px)';
                                            e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.5)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.transform = 'translateY(0)';
                                            e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                                        }}
                                    >
                                        <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>🎯</div>
                                        <h4 style={{ fontSize: '1.125rem', fontWeight: '600', color: '#fff', marginBottom: '0.5rem' }}>
                                            AI Strategy Builder
                                        </h4>
                                        <p style={{ color: '#94a3b8', fontSize: '0.875rem', lineHeight: '1.5' }}>
                                            Create custom trading strategies with AI-powered optimization
                                        </p>
                                        <div style={{ marginTop: '1rem', color: '#06b6d4', fontSize: '0.875rem', fontWeight: '500' }}>
                                            Get Started →
                                        </div>
                                    </div>
                                </Link>
                            </div>
                        </div>

                        {/* Connection Card */}
                        <div style={{
                            background: 'rgba(30, 41, 59, 0.6)',
                            borderRadius: '1.25rem',
                            border: '1px solid rgba(6, 182, 212, 0.2)',
                            padding: '2rem',
                            backdropFilter: 'blur(16px)',
                            marginBottom: '2rem'
                        }}>
                            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1rem' }}>
                                🔌 MT5 Connection
                            </h3>
                            {mt5Connection ? (
                                <div>
                                    <p style={{ color: '#94a3b8', marginBottom: '0.5rem' }}>
                                        <strong>Account:</strong> {mt5Connection.mt5_login} ({mt5Connection.mt5_server})
                                    </p>
                                    <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>
                                        <strong>Status:</strong> <span style={{ color: mt5StatusColor }}>{mt5Status}</span>
                                    </p>
                                </div>
                            ) : (
                                <>
                                    <p style={{ color: '#94a3b8', marginBottom: '1.5rem' }}>
                                        Connect your MetaTrader 5 account via the Windows connector application to start trading.
                                    </p>
                                    <div style={{
                                        padding: '1rem',
                                        background: 'rgba(251, 191, 36, 0.1)',
                                        border: '1px solid rgba(251, 191, 36, 0.3)',
                                        borderRadius: '0.75rem',
                                        color: '#fbbf24',
                                        fontSize: '0.875rem',
                                        marginBottom: '1.5rem'
                                    }}>
                                        ⚠️ Please download and run the Windows connector application to connect MT5
                                    </div>
                                    <button style={{
                                        padding: '0.875rem 1.5rem',
                                        background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                                        border: 'none',
                                        borderRadius: '0.75rem',
                                        color: 'white',
                                        fontWeight: '700',
                                        cursor: 'pointer',
                                        fontSize: '0.9375rem',
                                        boxShadow: '0 4px 20px rgba(6, 182, 212, 0.3)'
                                    }}>
                                        Download Windows Connector
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                )}

                {/* Auto-Trading Tab */}
                {activeTab === 'trading' && (
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.6)',
                        borderRadius: '1.25rem',
                        border: '1px solid rgba(6, 182, 212, 0.2)',
                        padding: '2rem',
                        backdropFilter: 'blur(16px)',
                        textAlign: 'center',
                        minHeight: '400px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🤖</div>
                        <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '1rem' }}>
                            Auto-Trading Controls
                        </h3>
                        <p style={{ color: '#94a3b8', maxWidth: '500px' }}>
                            {mt5Connection ?
                                `${activeModelsCount} model(s) active. Trading is ${activeModelsCount > 0 ? 'running' : 'stopped'}.` :
                                'Connect MT5 and load ML models to enable automated trading'
                            }
                        </p>
                    </div>
                )}

                {/* ML Models Tab */}
                {activeTab === 'models' && (
                    <div>
                        {mlModels.length > 0 ? (
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                                gap: '1.5rem'
                            }}>
                                {mlModels.map((model) => (
                                    <div key={model.id} style={{
                                        background: 'rgba(30, 41, 59, 0.6)',
                                        borderRadius: '1.25rem',
                                        border: '1px solid rgba(6, 182, 212, 0.2)',
                                        padding: '1.5rem',
                                        backdropFilter: 'blur(16px)'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                                            <h4 style={{ fontSize: '1.125rem', fontWeight: '700', margin: 0 }}>{model.name}</h4>
                                            <span style={{
                                                padding: '0.25rem 0.75rem',
                                                background: model.is_active ? 'rgba(16, 185, 129, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                                                border: model.is_active ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(148, 163, 184, 0.3)',
                                                borderRadius: '1rem',
                                                fontSize: '0.75rem',
                                                color: model.is_active ? '#10b981' : '#94a3b8',
                                                fontWeight: '600'
                                            }}>
                                                {model.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </div>
                                        <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                                            Symbol: <span style={{ color: '#06b6d4', fontWeight: '600' }}>{model.symbol}</span>
                                        </p>
                                        <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1rem' }}>
                                            Win Rate: <span style={{ color: '#06b6d4', fontWeight: '600' }}>{model.win_rate?.toFixed(1)}%</span>
                                        </p>
                                        <button style={{
                                            width: '100%',
                                            padding: '0.75rem',
                                            background: 'rgba(6, 182, 212, 0.1)',
                                            border: '1px solid rgba(6, 182, 212, 0.3)',
                                            borderRadius: '0.75rem',
                                            color: '#06b6d4',
                                            fontWeight: '600',
                                            cursor: 'pointer',
                                            fontSize: '0.875rem'
                                        }}>
                                            {model.is_active ? 'Stop Model' : 'Start Model'}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{
                                background: 'rgba(30, 41, 59, 0.6)',
                                borderRadius: '1.25rem',
                                border: '1px solid rgba(6, 182, 212, 0.2)',
                                padding: '3rem',
                                backdropFilter: 'blur(16px)',
                                textAlign: 'center'
                            }}>
                                <p style={{ color: '#94a3b8' }}>
                                    No ML models found. Models will appear here once loaded via the Windows connector.
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Trade History Tab */}
                {activeTab === 'history' && (
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.6)',
                        borderRadius: '1.25rem',
                        border: '1px solid rgba(6, 182, 212, 0.2)',
                        padding: '2rem',
                        backdropFilter: 'blur(16px)'
                    }}>
                        {trades.length > 0 ? (
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '1px solid rgba(6, 182, 212, 0.2)' }}>
                                            <th style={{ padding: '1rem', textAlign: 'left', color: '#94a3b8', fontSize: '0.875rem' }}>Symbol</th>
                                            <th style={{ padding: '1rem', textAlign: 'left', color: '#94a3b8', fontSize: '0.875rem' }}>Type</th>
                                            <th style={{ padding: '1rem', textAlign: 'right', color: '#94a3b8', fontSize: '0.875rem' }}>Volume</th>
                                            <th style={{ padding: '1rem', textAlign: 'right', color: '#94a3b8', fontSize: '0.875rem' }}>Entry</th>
                                            <th style={{ padding: '1rem', textAlign: 'right', color: '#94a3b8', fontSize: '0.875rem' }}>Exit</th>
                                            <th style={{ padding: '1rem', textAlign: 'right', color: '#94a3b8', fontSize: '0.875rem' }}>P/L</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {trades.slice(0, 20).map((trade) => (
                                            <tr key={trade.id} style={{ borderBottom: '1px solid rgba(6, 182, 212, 0.1)' }}>
                                                <td style={{ padding: '1rem', color: 'white' }}>{trade.symbol}</td>
                                                <td style={{ padding: '1rem', color: trade.trade_type === 'buy' ? '#10b981' : '#f43f5e', textTransform: 'uppercase' }}>
                                                    {trade.trade_type}
                                                </td>
                                                <td style={{ padding: '1rem', textAlign: 'right', color: 'white' }}>{trade.volume}</td>
                                                <td style={{ padding: '1rem', textAlign: 'right', color: 'white' }}>{trade.open_price.toFixed(5)}</td>
                                                <td style={{ padding: '1rem', textAlign: 'right', color: 'white' }}>
                                                    {trade.close_price ? trade.close_price.toFixed(5) : '-'}
                                                </td>
                                                <td style={{
                                                    padding: '1rem',
                                                    textAlign: 'right',
                                                    color: (trade.profit || 0) >= 0 ? '#10b981' : '#f43f5e',
                                                    fontWeight: '600'
                                                }}>
                                                    ${(trade.profit || 0).toFixed(2)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p style={{ textAlign: 'center', color: '#94a3b8', padding: '3rem' }}>
                                No trades yet. Start auto-trading to see your trade history here.
                            </p>
                        )}
                    </div>
                )}

                {/* Settings Tab */}
                {activeTab === 'settings' && (
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.6)',
                        borderRadius: '1.25rem',
                        border: '1px solid rgba(6, 182, 212, 0.2)',
                        padding: '2rem',
                        backdropFilter: 'blur(16px)'
                    }}>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: '700', marginBottom: '1.5rem' }}>
                            Account Settings
                        </h3>
                        <div style={{ maxWidth: '500px' }}>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#e2e8f0' }}>
                                    Email
                                </label>
                                <input
                                    type="email"
                                    value={user?.email || ''}
                                    disabled
                                    style={{
                                        width: '100%',
                                        padding: '0.875rem 1rem',
                                        background: 'rgba(15, 23, 42, 0.6)',
                                        border: '1px solid rgba(6, 182, 212, 0.2)',
                                        borderRadius: '0.75rem',
                                        color: '#94a3b8',
                                        fontSize: '1rem',
                                        boxSizing: 'border-box'
                                    }}
                                />
                            </div>
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#e2e8f0' }}>
                                    Subscription
                                </label>
                                <div style={{
                                    padding: '0.875rem 1rem',
                                    background: 'rgba(15, 23, 42, 0.6)',
                                    border: '1px solid rgba(6, 182, 212, 0.2)',
                                    borderRadius: '0.75rem',
                                    color: '#06b6d4',
                                    fontSize: '1rem',
                                    fontWeight: '600',
                                    textTransform: 'capitalize'
                                }}>
                                    {subscription?.tier || 'Free'} Tier
                                </div>
                            </div>

                            {/* LLM Usage */}
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', color: '#e2e8f0' }}>
                                    AI Strategy Generations
                                </label>
                                <div style={{
                                    padding: '0.875rem 1rem',
                                    background: 'rgba(15, 23, 42, 0.6)',
                                    border: '1px solid rgba(6, 182, 212, 0.2)',
                                    borderRadius: '0.75rem',
                                    fontSize: '1rem'
                                }}>
                                    {subscription?.tier === 'free' || !subscription ? (
                                        <div>
                                            <p style={{ color: '#06b6d4', fontWeight: '600', margin: 0 }}>
                                                {llmUsage}/10 used this month
                                            </p>
                                            <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '0.5rem', marginBottom: 0 }}>
                                                Upgrade to Pro for unlimited AI generations
                                            </p>
                                        </div>
                                    ) : (
                                        <p style={{ color: '#10b981', fontWeight: '600', margin: 0 }}>
                                            ∞ Unlimited
                                        </p>
                                    )}
                                </div>
                            </div>

                            <Link href="/" style={{
                                display: 'inline-block',
                                padding: '0.875rem 1.5rem',
                                background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                                border: 'none',
                                borderRadius: '0.75rem',
                                color: 'white',
                                fontWeight: '700',
                                textDecoration: 'none',
                                fontSize: '0.9375rem',
                                boxShadow: '0 4px 20px rgba(6, 182, 212, 0.3)'
                            }}>
                                {subscription?.tier === 'free' || !subscription ? 'Upgrade to Pro' : 'Manage Subscription'}
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
