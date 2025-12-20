'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';

function LoginForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const message = searchParams.get('message');

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const formData = new FormData(e.currentTarget);
        const email = formData.get('email') as string;
        const password = formData.get('password') as string;

        const supabase = createClient();

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        router.push('/dashboard');
    };

    return (
        <div style={{ width: '100%', maxWidth: '28rem' }}>
            {/* Logo */}
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <Link href="/" style={{ textDecoration: 'none' }}>
                    <h1 style={{
                        fontSize: '2.5rem',
                        fontWeight: 'bold',
                        background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        margin: 0
                    }}>
                        NexusTrade
                    </h1>
                </Link>
                <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>Login ke akun Anda</p>
            </div>

            {/* Form Card */}
            <div style={{
                background: 'rgba(30, 41, 59, 0.5)',
                borderRadius: '1rem',
                border: '1px solid rgba(6, 182, 212, 0.2)',
                padding: '2rem',
                backdropFilter: 'blur(10px)'
            }}>
                {message && (
                    <div style={{
                        marginBottom: '1.5rem',
                        padding: '0.75rem',
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        borderRadius: '0.5rem',
                        color: '#10b981',
                        fontSize: '0.875rem'
                    }}>
                        {message}
                    </div>
                )}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {error && (
                        <div style={{
                            padding: '0.75rem',
                            background: 'rgba(244, 63, 94, 0.1)',
                            border: '1px solid rgba(244, 63, 94, 0.3)',
                            borderRadius: '0.5rem',
                            color: '#f43f5e',
                            fontSize: '0.875rem'
                        }}>
                            {error}
                        </div>
                    )}

                    <div>
                        <label htmlFor="email" style={{
                            display: 'block',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            marginBottom: '0.5rem',
                            color: '#cbd5e1'
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
                                padding: '0.75rem 1rem',
                                background: 'rgba(15, 23, 42, 0.5)',
                                border: '1px solid rgba(6, 182, 212, 0.2)',
                                borderRadius: '0.5rem',
                                color: 'white',
                                fontSize: '1rem',
                                outline: 'none',
                                transition: 'border-color 0.3s'
                            }}
                            placeholder="email@example.com"
                            onFocus={(e) => e.target.style.borderColor = '#06b6d4'}
                            onBlur={(e) => e.target.style.borderColor = 'rgba(6, 182, 212, 0.2)'}
                        />
                    </div>

                    <div>
                        <label htmlFor="password" style={{
                            display: 'block',
                            fontSize: '0.875rem',
                            fontWeight: '500',
                            marginBottom: '0.5rem',
                            color: '#cbd5e1'
                        }}>
                            Password
                        </label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            required
                            style={{
                                width: '100%',
                                padding: '0.75rem 1rem',
                                background: 'rgba(15, 23, 42, 0.5)',
                                border: '1px solid rgba(6, 182, 212, 0.2)',
                                borderRadius: '0.5rem',
                                color: 'white',
                                fontSize: '1rem',
                                outline: 'none',
                                transition: 'border-color 0.3s'
                            }}
                            placeholder="••••••••"
                            onFocus={(e) => e.target.style.borderColor = '#06b6d4'}
                            onBlur={(e) => e.target.style.borderColor = 'rgba(6, 182, 212, 0.2)'}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            background: loading ? 'rgba(6, 182, 212, 0.5)' : 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                            borderRadius: '0.5rem',
                            fontWeight: 'bold',
                            color: 'white',
                            border: 'none',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '1rem',
                            boxShadow: '0 4px 20px rgba(6, 182, 212, 0.3)',
                            transition: 'all 0.3s'
                        }}
                    >
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>

                <div style={{ marginTop: '1.5rem', textAlign: 'center', color: '#94a3b8' }}>
                    Belum punya akun?{' '}
                    <Link href="/auth/signup" style={{ color: '#06b6d4', textDecoration: 'none', fontWeight: '500' }}>
                        Daftar
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default function LoginPage() {
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
            <Suspense fallback={
                <div style={{ textAlign: 'center', color: 'white' }}>
                    <div style={{
                        fontSize: '2.5rem',
                        fontWeight: 'bold',
                        background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text'
                    }}>
                        NexusTrade
                    </div>
                    <p style={{ color: '#94a3b8', marginTop: '1rem' }}>Loading...</p>
                </div>
            }>
                <LoginForm />
            </Suspense>
        </div>
    );
}
