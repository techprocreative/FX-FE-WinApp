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
        <div className="min-h-screen bg-dark flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link href="/">
                        <h1 className="text-4xl font-bold text-gradient">NexusTrade</h1>
                    </Link>
                    <p className="text-gray-400 mt-2">Buat akun baru</p>
                </div>

                {/* Form Card */}
                <div className="bg-dark-50 rounded-xl border border-dark-100 p-8">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="p-3 bg-accent-red/20 border border-accent-red rounded-lg text-accent-red text-sm">
                                {error}
                            </div>
                        )}

                        <div>
                            <label htmlFor="fullName" className="block text-sm font-medium mb-2">
                                Nama Lengkap
                            </label>
                            <input
                                id="fullName"
                                name="fullName"
                                type="text"
                                required
                                className="w-full px-4 py-3 bg-dark border border-dark-100 rounded-lg focus:outline-none focus:border-primary"
                                placeholder="John Doe"
                            />
                        </div>

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
                                minLength={8}
                                className="w-full px-4 py-3 bg-dark border border-dark-100 rounded-lg focus:outline-none focus:border-primary"
                                placeholder="Min. 8 karakter"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 bg-primary rounded-lg font-semibold hover:bg-primary-600 transition-colors disabled:opacity-50"
                        >
                            {loading ? 'Mendaftar...' : 'Daftar'}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-gray-400">
                        Sudah punya akun?{' '}
                        <Link href="/auth/login" className="text-primary hover:underline">
                            Login
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
