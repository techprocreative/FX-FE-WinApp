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
        <div className="w-full max-w-md">
            {/* Logo */}
            <div className="text-center mb-8">
                <Link href="/">
                    <h1 className="text-4xl font-bold text-gradient">NexusTrade</h1>
                </Link>
                <p className="text-gray-400 mt-2">Login ke akun Anda</p>
            </div>

            {/* Form Card */}
            <div className="bg-dark-50 rounded-xl border border-dark-100 p-8">
                {message && (
                    <div className="mb-6 p-3 bg-accent-green/20 border border-accent-green rounded-lg text-accent-green text-sm">
                        {message}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    {error && (
                        <div className="p-3 bg-accent-red/20 border border-accent-red rounded-lg text-accent-red text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label htmlFor="email" className="block text-sm font-medium mb-2">
                            Email
                        </label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            required
                            className="w-full px-4 py-3 bg-dark border border-dark-100 rounded-lg focus:outline-none focus:border-primary"
                            placeholder="email@example.com"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium mb-2">
                            Password
                        </label>
                        <input
                            id="password"
                            name="password"
                            type="password"
                            required
                            className="w-full px-4 py-3 bg-dark border border-dark-100 rounded-lg focus:outline-none focus:border-primary"
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 bg-primary rounded-lg font-semibold hover:bg-primary-600 transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </form>

                <div className="mt-6 text-center text-gray-400">
                    Belum punya akun?{' '}
                    <Link href="/auth/signup" className="text-primary hover:underline">
                        Daftar
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <div className="min-h-screen bg-dark flex items-center justify-center p-4">
            <Suspense fallback={
                <div className="w-full max-w-md text-center">
                    <div className="text-4xl font-bold text-gradient">NexusTrade</div>
                    <p className="text-gray-400 mt-4">Loading...</p>
                </div>
            }>
                <LoginForm />
            </Suspense>
        </div>
    );
}
