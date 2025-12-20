'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function HomePage() {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    return (
        <main className="min-h-screen bg-slate-950 text-white selection:bg-indigo-500 selection:text-white overflow-x-hidden">

            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-white/10 shadow-sm">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <div className="flex-shrink-0 cursor-pointer">
                            <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                                NexusTrade
                            </Link>
                        </div>

                        {/* Desktop Menu */}
                        <div className="hidden md:block">
                            <div className="ml-10 flex items-center space-x-8">
                                <a href="#features" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Fitur</a>
                                <a href="#pricing" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Harga</a>
                                <a href="#stats" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">Statistik</a>
                                <Link href="/auth/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                                    Masuk
                                </Link>
                                <Link href="/auth/signup" className="px-4 py-2 text-sm font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all shadow-lg shadow-indigo-500/30">
                                    Daftar Sekarang
                                </Link>
                            </div>
                        </div>

                        {/* Mobile menu button */}
                        <div className="md:hidden">
                            <button
                                onClick={() => setIsMenuOpen(!isMenuOpen)}
                                className="inline-flex items-center justify-center p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
                            >
                                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    {isMenuOpen ? (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    ) : (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                    )}
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Mobile Menu */}
                {isMenuOpen && (
                    <div className="md:hidden bg-slate-900 border-b border-white/10">
                        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                            <a href="#features" className="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Fitur</a>
                            <a href="#pricing" className="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Harga</a>
                            <Link href="/auth/login" className="block px-3 py-2 rounded-md text-base font-medium text-slate-300 hover:text-white hover:bg-slate-800">Masuk</Link>
                            <Link href="/auth/signup" className="block px-3 py-2 rounded-md text-base font-medium bg-indigo-600 text-white">Daftar Sekarang</Link>
                        </div>
                    </div>
                )}
            </nav>

            {/* Hero Section */}
            <header className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
                <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center z-10">
                    <div className="inline-flex items-center px-4 py-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-sm font-medium mb-8">
                        <span className="w-2 h-2 bg-indigo-400 rounded-full mr-2 animate-pulse"></span>
                        AI Trading Live Version 1.0
                    </div>

                    <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white mb-8 leading-tight">
                        Trading Forex Lebih Cerdas <br className="hidden sm:block" />
                        dengan <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">AI Technology</span>
                    </h1>

                    <p className="mt-4 max-w-2xl mx-auto text-xl text-slate-400 mb-10">
                        Automatisasi trading Anda dengan algoritma Machine Learning canggih.
                        Analisis data pasar real-time tanpa emosi, 24/7.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <Link href="/auth/signup"
                            className="px-8 py-4 bg-white text-slate-900 rounded-xl font-bold text-lg hover:bg-gray-100 transition-transform hover:-translate-y-1 shadow-xl shadow-white/10">
                            Coba Demo Gratis
                        </Link>
                        <a href="#features"
                            className="px-8 py-4 bg-slate-800 text-white rounded-xl font-bold text-lg hover:bg-slate-700 transition-colors border border-slate-700">
                            Pelajari Fitur
                        </a>
                    </div>
                </div>

                {/* Background Decor */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl -z-10 opacity-30 pointer-events-none">
                    <div className="absolute top-20 left-10 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob"></div>
                    <div className="absolute top-20 right-10 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl animate-blob animation-delay-2000"></div>
                </div>
            </header>

            {/* Stats Section */}
            <section id="stats" className="py-12 bg-slate-900 border-y border-white/5">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-white mb-1">$1.2M+</div>
                            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Trading Volume</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-white mb-1">98.5%</div>
                            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">AI Accuracy</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-white mb-1">24/7</div>
                            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Market Monitor</div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-white mb-1">&lt;50ms</div>
                            <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Execution Speed</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="py-24 bg-slate-950 relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-white mb-4">Fitur Utama</h2>
                        <p className="text-slate-400 max-w-2xl mx-auto">Semua yang Anda butuhkan untuk trading next-level.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Feature 1 */}
                        <div className="bg-slate-900 p-8 rounded-2xl border border-white/5 hover:border-indigo-500/50 transition-colors group">
                            <div className="w-12 h-12 bg-indigo-500/10 rounded-lg flex items-center justify-center mb-6 group-hover:bg-indigo-500/20 transition-colors">
                                <span className="text-2xl">🧠</span>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-3">AI Strategy Generator</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Buat strategi trading kompleks hanya dengan menjelaskan ide Anda dalam bahasa sehari-hari. AI akan menulis kodenya.
                            </p>
                        </div>

                        {/* Feature 2 */}
                        <div className="bg-slate-900 p-8 rounded-2xl border border-white/5 hover:border-purple-500/50 transition-colors group">
                            <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center mb-6 group-hover:bg-purple-500/20 transition-colors">
                                <span className="text-2xl">⚡</span>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-3">Ultra-Fast Backtesting</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Validasi strategi Anda dengan data historis 5 tahun dalam hitungan detik. Optimasi parameter secara otomatis.
                            </p>
                        </div>

                        {/* Feature 3 */}
                        <div className="bg-slate-900 p-8 rounded-2xl border border-white/5 hover:border-pink-500/50 transition-colors group">
                            <div className="w-12 h-12 bg-pink-500/10 rounded-lg flex items-center justify-center mb-6 group-hover:bg-pink-500/20 transition-colors">
                                <span className="text-2xl">🤖</span>
                            </div>
                            <h3 className="text-xl font-bold text-white mb-3">ML Auto-Trading</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Biarkan model Machine Learning kami mengeksekusi trade 24/7 berdasarkan probabilitas statistik tertinggi.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing */}
            <section id="pricing" className="py-24 bg-slate-900 border-t border-white/5">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-white mb-4">Paket Langganan</h2>
                        <p className="text-slate-400">Pilih paket yang sesuai kebutuhan trading Anda.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                        {/* Free */}
                        <div className="bg-slate-950 p-8 rounded-2xl border border-white/10 flex flex-col">
                            <div className="mb-4">
                                <h3 className="text-lg font-semibold text-slate-300">Starter</h3>
                                <div className="text-3xl font-bold text-white mt-2">Free</div>
                            </div>
                            <ul className="space-y-3 mb-8 flex-1 text-slate-400 text-sm">
                                <li className="flex gap-2">✓ <span>Manual Trading</span></li>
                                <li className="flex gap-2">✓ <span>30 Hari Data History</span></li>
                                <li className="flex gap-2">✓ <span>10 AI Request/hari</span></li>
                            </ul>
                            <Link href="/auth/signup" className="w-full py-3 bg-slate-800 text-white rounded-lg font-semibold hover:bg-slate-700 text-center transition-colors">
                                Mulai Gratis
                            </Link>
                        </div>

                        {/* Pro */}
                        <div className="bg-gradient-to-b from-indigo-900/50 to-slate-900 p-8 rounded-2xl border border-indigo-500/30 flex flex-col relative overflow-hidden">
                            <div className="absolute top-0 right-0 bg-indigo-500 text-white text-xs px-3 py-1 rounded-bl-lg font-bold">POPULAR</div>
                            <div className="mb-4">
                                <h3 className="text-lg font-semibold text-indigo-300">Pro Trader</h3>
                                <div className="text-3xl font-bold text-white mt-2">Rp 449rb<span className="text-sm text-slate-400 font-normal">/bulan</span></div>
                            </div>
                            <ul className="space-y-3 mb-8 flex-1 text-slate-300 text-sm">
                                <li className="flex gap-2 text-white">✓ <span>Semua fitur Starter</span></li>
                                <li className="flex gap-2 text-white">✓ <span>Auto-Trading (ML Models)</span></li>
                                <li className="flex gap-2 text-white">✓ <span>Unlimited Backtesting</span></li>
                                <li className="flex gap-2 text-white">✓ <span>500 AI Request/hari</span></li>
                            </ul>
                            <Link href="/auth/signup" className="w-full py-3 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 text-center transition-colors shadow-lg shadow-indigo-500/20">
                                Upgrade Pro
                            </Link>
                        </div>

                        {/* Enterprise */}
                        <div className="bg-slate-950 p-8 rounded-2xl border border-white/10 flex flex-col">
                            <div className="mb-4">
                                <h3 className="text-lg font-semibold text-slate-300">Enterprise</h3>
                                <div className="text-3xl font-bold text-white mt-2">Contact Us</div>
                            </div>
                            <ul className="space-y-3 mb-8 flex-1 text-slate-400 text-sm">
                                <li className="flex gap-2">✓ <span>Custom AI Models</span></li>
                                <li className="flex gap-2">✓ <span>Dedicated Server</span></li>
                                <li className="flex gap-2">✓ <span>White Label</span></li>
                                <li className="flex gap-2">✓ <span>24/7 Priority Support</span></li>
                            </ul>
                            <Link href="/auth/signup" className="w-full py-3 bg-slate-800 text-white rounded-lg font-semibold hover:bg-slate-700 text-center transition-colors">
                                Hubungi Sales
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-slate-950 border-t border-white/5 py-12">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <p className="text-slate-500 text-sm">
                        &copy; {new Date().getFullYear()} NexusTrade. All rights reserved.
                    </p>
                </div>
            </footer>
        </main>
    );
}
