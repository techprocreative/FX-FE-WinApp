'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { createClient } from '@/lib/supabase/client';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        const checkAuth = async () => {
            const supabase = createClient();
            const { data: { user } } = await supabase.auth.getUser();

            if (!user) {
                router.push('/auth/login');
                return;
            }

            setUser(user);
            setLoading(false);
        };

        checkAuth();
    }, [router]);

    const handleLogout = async () => {
        const supabase = createClient();
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
                                { label: 'MT5 Status', value: 'Disconnected', color: '#94a3b8', icon: '🔌' },
                                { label: 'Account Balance', value: '$0.00', color: '#06b6d4', icon: '💰' },
                                { label: 'Active Models', value: '0', color: '#10b981', icon: '🤖' },
                                { label: 'Today P/L', value: '$0.00', color: '#94a3b8', icon: '📊' }
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
                            Connect MT5 and load ML models to enable automated trading
                        </p>
                    </div>
                )}

                {/* ML Models Tab */}
                {activeTab === 'models' && (
                    <div>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                            gap: '1.5rem'
                        }}>
                            {[
                                { name: 'XAUUSD Hybrid', winRate: '54.7%', status: 'Ready', color: '#10b981' },
                                { name: 'BTCUSD Hybrid', winRate: '46.0%', status: 'Ready', color: '#10b981' },
                                { name: 'XAUUSD EMA-CCI v2', winRate: '36.4%', status: 'Ready', color: '#10b981' },
                                { name: 'BTCUSD EMA-CCI v2', winRate: '46.2%', status: 'Ready', color: '#10b981' }
                            ].map((model, idx) => (
                                <div key={idx} style={{
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
                                            background: `rgba(16, 185, 129, 0.15)`,
                                            border: `1px solid rgba(16, 185, 129, 0.3)`,
                                            borderRadius: '1rem',
                                            fontSize: '0.75rem',
                                            color: model.color,
                                            fontWeight: '600'
                                        }}>
                                            {model.status}
                                        </span>
                                    </div>
                                    <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginBottom: '1rem' }}>
                                        Win Rate: <span style={{ color: '#06b6d4', fontWeight: '600' }}>{model.winRate}</span>
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
                                        Load Model
                                    </button>
                                </div>
                            ))}
                        </div>
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
                        <p style={{ textAlign: 'center', color: '#94a3b8', padding: '3rem' }}>
                            No trades yet. Start auto-trading to see your trade history here.
                        </p>
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
                                    fontWeight: '600'
                                }}>
                                    Free Tier
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
                                Upgrade to Pro
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
