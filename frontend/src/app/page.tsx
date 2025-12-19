import Link from 'next/link';

export default function HomePage() {
    return (
        <main className="min-h-screen bg-dark">
            {/* Hero Section */}
            <section className="relative overflow-hidden">
                {/* Background gradient */}
                <div className="absolute inset-0 bg-gradient-to-br from-dark via-dark-50 to-dark-100 opacity-80" />

                {/* Content */}
                <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
                    <div className="text-center">
                        {/* Logo */}
                        <h1 className="text-5xl md:text-7xl font-bold mb-6">
                            <span className="text-gradient">NexusTrade</span>
                        </h1>

                        <p className="text-xl md:text-2xl text-gray-400 mb-8 max-w-3xl mx-auto">
                            Platform Trading Forex dengan AI Strategy Generator dan ML Auto-Trading
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <Link
                                href="/auth/signup"
                                className="px-8 py-4 bg-primary rounded-lg font-semibold text-white hover:bg-primary-600 transition-colors"
                            >
                                Mulai Gratis
                            </Link>
                            <Link
                                href="/auth/login"
                                className="px-8 py-4 bg-dark-50 border border-dark-100 rounded-lg font-semibold text-white hover:bg-dark-100 transition-colors"
                            >
                                Login
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-dark-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-center mb-12">
                        Fitur <span className="text-primary">Unggulan</span>
                    </h2>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div className="p-6 bg-dark rounded-xl border border-dark-100 hover:border-primary transition-colors">
                            <div className="w-12 h-12 bg-primary/20 rounded-lg flex items-center justify-center mb-4">
                                <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-2">AI Strategy Generator</h3>
                            <p className="text-gray-400">
                                Generate strategi trading menggunakan AI dengan prompt natural language
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div className="p-6 bg-dark rounded-xl border border-dark-100 hover:border-primary transition-colors">
                            <div className="w-12 h-12 bg-accent-green/20 rounded-lg flex items-center justify-center mb-4">
                                <svg className="w-6 h-6 text-accent-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-2">ML Auto-Trading</h3>
                            <p className="text-gray-400">
                                Trading otomatis dengan model Machine Learning yang terenkripsi dan aman
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div className="p-6 bg-dark rounded-xl border border-dark-100 hover:border-primary transition-colors">
                            <div className="w-12 h-12 bg-accent-yellow/20 rounded-lg flex items-center justify-center mb-4">
                                <svg className="w-6 h-6 text-accent-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-semibold mb-2">Backtesting</h3>
                            <p className="text-gray-400">
                                Test strategi trading pada data historis sebelum trading dengan uang nyata
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section className="py-20">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-3xl font-bold text-center mb-12">
                        Pilih <span className="text-primary">Paket</span>
                    </h2>

                    <div className="grid md:grid-cols-4 gap-6">
                        {/* Free */}
                        <div className="p-6 bg-dark-50 rounded-xl border border-dark-100">
                            <h3 className="text-lg font-semibold mb-2">Free</h3>
                            <p className="text-3xl font-bold mb-4">Rp 0</p>
                            <ul className="space-y-2 text-sm text-gray-400 mb-6">
                                <li>✓ Trading Manual</li>
                                <li>✓ History 30 hari</li>
                                <li>✓ 1 API Key</li>
                                <li>✓ 10 LLM request/hari</li>
                            </ul>
                            <Link href="/auth/signup" className="block text-center py-2 border border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition-colors">
                                Daftar Gratis
                            </Link>
                        </div>

                        {/* Basic */}
                        <div className="p-6 bg-dark-50 rounded-xl border border-dark-100">
                            <h3 className="text-lg font-semibold mb-2">Basic</h3>
                            <p className="text-3xl font-bold mb-4">Rp 449K<span className="text-sm font-normal">/bln</span></p>
                            <ul className="space-y-2 text-sm text-gray-400 mb-6">
                                <li>✓ Semua fitur Free</li>
                                <li>✓ History 1 tahun</li>
                                <li>✓ 3 API Keys</li>
                                <li>✓ 100 LLM request/hari</li>
                                <li>✓ 10 Backtest/hari</li>
                            </ul>
                            <Link href="/auth/signup" className="block text-center py-2 bg-dark-100 rounded-lg hover:bg-primary transition-colors">
                                Pilih Basic
                            </Link>
                        </div>

                        {/* Pro - Recommended */}
                        <div className="p-6 bg-gradient-to-b from-primary/20 to-dark-50 rounded-xl border-2 border-primary relative">
                            <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-xs font-semibold rounded-full">
                                POPULER
                            </span>
                            <h3 className="text-lg font-semibold mb-2">Pro</h3>
                            <p className="text-3xl font-bold mb-4">Rp 1.2JT<span className="text-sm font-normal">/bln</span></p>
                            <ul className="space-y-2 text-sm text-gray-400 mb-6">
                                <li>✓ Semua fitur Basic</li>
                                <li>✓ History Unlimited</li>
                                <li>✓ 10 API Keys</li>
                                <li>✓ 500 LLM request/hari</li>
                                <li>✓ 50 Backtest/hari</li>
                                <li>✓ Auto-Trading 5 Model</li>
                            </ul>
                            <Link href="/auth/signup" className="block text-center py-2 bg-primary rounded-lg hover:bg-primary-600 transition-colors">
                                Pilih Pro
                            </Link>
                        </div>

                        {/* Enterprise */}
                        <div className="p-6 bg-dark-50 rounded-xl border border-dark-100">
                            <h3 className="text-lg font-semibold mb-2">Enterprise</h3>
                            <p className="text-3xl font-bold mb-4">Rp 3JT<span className="text-sm font-normal">/bln</span></p>
                            <ul className="space-y-2 text-sm text-gray-400 mb-6">
                                <li>✓ Semua fitur Pro</li>
                                <li>✓ Unlimited API Keys</li>
                                <li>✓ Unlimited LLM</li>
                                <li>✓ Unlimited Backtest</li>
                                <li>✓ Unlimited Auto-Trading</li>
                                <li>✓ Support Dedicated</li>
                            </ul>
                            <Link href="/auth/signup" className="block text-center py-2 bg-dark-100 rounded-lg hover:bg-primary transition-colors">
                                Hubungi Kami
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 border-t border-dark-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-500">
                    <p>&copy; 2024 NexusTrade. All rights reserved.</p>
                </div>
            </footer>
        </main>
    );
}
