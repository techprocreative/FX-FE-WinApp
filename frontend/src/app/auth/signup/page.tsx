'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

export default function SignupPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const formData = new FormData(e.currentTarget);
        const email = formData.get('email') as string;
        const password = formData.get('password') as string;
        const fullName = formData.get('fullName') as string;

        const supabase = createClient();

        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: fullName,
                },
            },
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        router.push('/auth/login?message=Check your email to confirm your account');
    };

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1rem',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
            <div style={{ width: '100%', maxWidth: '440px' }}>
                {/* Logo */}
                <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                    <Link href="/" style={{ textDecoration: 'none' }}>
                        <h1 style={{
                            fontSize: '3rem',
                            fontWeight: '900',
                            background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text',
                            margin: 0,
                            letterSpacing: '-0.02em'
                        }}>
                            NexusTrade
                        </h1>
                    </Link>
                    <p style={{ color: '#94a3b8', marginTop: '0.75rem', fontSize: '1rem' }}>Buat akun baru</p>
                </div>

                {/* Form Card */}
                <div style={{
                    background: 'rgba(30, 41, 59, 0.6)',
                    borderRadius: '1.5rem',
                    border: '1px solid rgba(6, 182, 212, 0.3)',
                    padding: '2.5rem',
                    backdropFilter: 'blur(16px)',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)'
                }}>
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {error && (
                            <div style={{
                                padding: '1rem',
                                background: 'rgba(244, 63, 94, 0.15)',
                                border: '1px solid rgba(244, 63, 94, 0.4)',
                                borderRadius: '0.75rem',
                                color: '#f43f5e',
                                fontSize: '0.875rem',
                                lineHeight: '1.5'
                            }}>
                                {error}
                            </div>
                        )}

                        <div>
                            <label htmlFor="fullName" style={{
                                display: 'block',
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                marginBottom: '0.5rem',
                                color: '#e2e8f0'
                            }}>
                                Nama Lengkap
                            </label>
                            <input
                                id="fullName"
                                name="fullName"
                                type="text"
                                required
                                style={{
                                    width: '100%',
                                    padding: '0.875rem 1rem',
                                    background: 'rgba(15, 23, 42, 0.6)',
                                    border: '1px solid rgba(6, 182, 212, 0.3)',
                                    borderRadius: '0.75rem',
                                    color: 'white',
                                    fontSize: '1rem',
                                    outline: 'none',
                                    transition: 'all 0.3s',
                                    boxSizing: 'border-box'
                                }}
                                placeholder="John Doe"
                                onFocus={(e) => {
                                    e.target.style.borderColor = '#06b6d4';
                                    e.target.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
                                }}
                                onBlur={(e) => {
                                    e.target.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                                    e.target.style.boxShadow = 'none';
                                }}
                            />
                        </div>

                        <div>
                            <label htmlFor="email" style={{
                                display: 'block',
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                marginBottom: '0.5rem',
                                color: '#e2e8f0'
                            }}>
                                Email
                            </label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                required
                                style={{
                                    width: '100%',
                                    padding: '0.875rem 1rem',
                                    background: 'rgba(15, 23, 42, 0.6)',
                                    border: '1px solid rgba(6, 182, 212, 0.3)',
                                    borderRadius: '0.75rem',
                                    color: 'white',
                                    fontSize: '1rem',
                                    outline: 'none',
                                    transition: 'all 0.3s',
                                    boxSizing: 'border-box'
                                }}
                                placeholder="email@example.com"
                                onFocus={(e) => {
                                    e.target.style.borderColor = '#06b6d4';
                                    e.target.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
                                }}
                                onBlur={(e) => {
                                    e.target.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                                    e.target.style.boxShadow = 'none';
                                }}
                            />
                        </div>

                        <div>
                            <label htmlFor="password" style={{
                                display: 'block',
                                fontSize: '0.875rem',
                                fontWeight: '600',
                                marginBottom: '0.5rem',
                                color: '#e2e8f0'
                            }}>
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                minLength={8}
                                style={{
                                    width: '100%',
                                    padding: '0.875rem 1rem',
                                    background: 'rgba(15, 23, 42, 0.6)',
                                    border: '1px solid rgba(6, 182, 212, 0.3)',
                                    borderRadius: '0.75rem',
                                    color: 'white',
                                    fontSize: '1rem',
                                    outline: 'none',
                                    transition: 'all 0.3s',
                                    boxSizing: 'border-box'
                                }}
                                placeholder="Min. 8 karakter"
                                onFocus={(e) => {
                                    e.target.style.borderColor = '#06b6d4';
                                    e.target.style.boxShadow = '0 0 0 3px rgba(6, 182, 212, 0.1)';
                                }}
                                onBlur={(e) => {
                                    e.target.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                                    e.target.style.boxShadow = 'none';
                                }}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '1rem',
                                marginTop: '0.5rem',
                                background: loading ? 'rgba(6, 182, 212, 0.5)' : 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                                borderRadius: '0.75rem',
                                fontWeight: '700',
                                fontSize: '1rem',
                                color: 'white',
                                border: 'none',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                boxShadow: loading ? 'none' : '0 4px 20px rgba(6, 182, 212, 0.4)',
                                transition: 'all 0.3s',
                                transform: loading ? 'none' : 'translateY(0)'
                            }}
                            onMouseEnter={(e) => {
                                if (!loading) {
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.boxShadow = '0 6px 30px rgba(6, 182, 212, 0.5)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!loading) {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = '0 4px 20px rgba(6, 182, 212, 0.4)';
                                }
                            }}
                        >
                            {loading ? 'Mendaftar...' : 'Daftar'}
                        </button>
                    </form>

                    <div style={{ marginTop: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.875rem' }}>
                        Sudah punya akun?{' '}
                        <Link href="/auth/login" style={{ color: '#06b6d4', textDecoration: 'none', fontWeight: '600' }}>
                            Login
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
