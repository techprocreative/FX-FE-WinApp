import Link from 'next/link';
import Image from 'next/image';

export default function HomePage() {
    return (
        <main className="min-h-screen bg-[#0f172a] selection:bg-indigo-500 selection:text-white">

            {/* Navbar */}
            <nav className="fixed top-0 w-full z-50 glass border-b border-white/5">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex-shrink-0">
                            <span className="text-2xl font-bold text-gradient">NexusTrade</span>
                        </div>
                        <div className="hidden md:block">
                            <div className="ml-10 flex items-baseline space-x-8">
                                <a href="#features" className="text-gray-300 hover:text-white transition-colors duration-300">Fitur</a>
                                <a href="#pricing" className="text-gray-300 hover:text-white transition-colors duration-300">Harga</a>
                                <a href="#stats" className="text-gray-300 hover:text-white transition-colors duration-300">Statistik</a>
                            </div>
                        </div>
                        <div className="flex gap-4">
                            <Link href="/auth/login" className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors">
                                Log in
                            </Link>
                            <Link href="/auth/signup" className="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-all shadow-lg shadow-indigo-500/20">
                                Mulai Gratis
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="relative min-h-screen flex items-center pt-20 overflow-hidden">
                {/* Animated Background Blobs */}
                <div className="absolute top-0 -left-4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
                <div className="absolute top-0 -right-4 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
                <div className="absolute -bottom-8 left-20 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>

                <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center text-center">
                    <div className="inline-flex items-center px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-sm font-medium mb-8 backdrop-blur-sm animate-float">
                        <span className="flex w-2 h-2 bg-indigo-500 rounded-full mr-2 animate-pulse"></span>
                        New: GRU-XGBoost Hybrid Model Live!
                    </div>

                    <h1 className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tight mb-8">
                        Trading Forex dengan <br />
                        <span className="text-gradient">Kecerdasan Buatan</span>
                    </h1>

                    <p className="mt-4 max-w-2xl text-xl text-slate-400 mb-10 leading-relaxed">
                        Platform auto-trading revolusioner yang menggabungkan analisis teknikal klasik dengan Machine Learning canggih untuk profitabilitas maksimal.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-5 w-full justify-center">
                        <Link href="/auth/signup"
                            className="px-8 py-4 bg-white text-slate-900 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-xl shadow-white/10">
                            Coba Demo Gratis
                        </Link>
                        <Link href="#features"
                            className="px-8 py-4 glass text-white rounded-xl font-bold text-lg hover:bg-white/10 transition-all backdrop-blur-md border border-white/10">
                            Pelajari Cara Kerja
                        </Link>
                    </div>

                    {/* Dashboard Preview Overlay */}
                    <div className="mt-20 relative w-full max-w-5xl group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-pink-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000"></div>
                        <div className="relative glass rounded-xl border border-white/10 p-4 aspect-video flex items-center justify-center overflow-hidden">
                            <div className="text-center">
                                <span className="text-6xl mb-4 block">📊</span>
                                <h3 className="text-2xl font-bold text-white mb-2">Interactive Trading Dashboard</h3>
                                <p className="text-slate-400">Real-time charts, AI signals, and portfolio tracking</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section id="stats" className="py-12 border-y border-white/5 bg-slate-900/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                        <div>
                            <div className="text-4xl font-bold text-white mb-2">$1B+</div>
                            <div className="text-sm text-slate-400 uppercase tracking-wider">Trading Volume</div>
                        </div>
                        <div>
                            <div className="text-4xl font-bold text-white mb-2">50k+</div>
                            <div className="text-sm text-slate-400 uppercase tracking-wider">Active Traders</div>
                        </div>
                        <div>
                            <div className="text-4xl font-bold text-white mb-2">99.9%</div>
                            <div className="text-sm text-slate-400 uppercase tracking-wider">Uptime</div>
                        </div>
                        <div>
                            <div className="text-4xl font-bold text-white mb-2">24/7</div>
                            <div className="text-sm text-slate-400 uppercase tracking-wider">AI Analysis</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-32 relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-5xl font-bold mb-6">Fitur <span className="text-indigo-500">Unggulan</span></h2>
                        <p className="text-xl text-slate-400 max-w-2xl mx-auto">Teknologi trading paling mutakhir di ujung jari Anda.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="glass-card p-8 rounded-3xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-bl-full -mr-8 -mt-8 transition-all group-hover:bg-indigo-500/20"></div>
                            <div className="w-14 h-14 bg-indigo-500/20 rounded-2xl flex items-center justify-center mb-6 text-2xl">
                                🧠
                            </div>
                            <h3 className="text-2xl font-bold mb-4">AI Strategy Generator</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Cukup ketik strategi dalam bahasa manusia, AI kami akan menerjemahkannya menjadi kode algoritma siap pakai.
                            </p>
                        </div>

                        <div className="glass-card p-8 rounded-3xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-pink-500/10 rounded-bl-full -mr-8 -mt-8 transition-all group-hover:bg-pink-500/20"></div>
                            <div className="w-14 h-14 bg-pink-500/20 rounded-2xl flex items-center justify-center mb-6 text-2xl">
                                🤖
                            </div>
                            <h3 className="text-2xl font-bold mb-4">ML Auto-Trading</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Model GRU-XGBoost Hybrid yang terus belajar dari pasar untuk memberikan sinyal entry/exit dengan probabilitas tinggi.
                            </p>
                        </div>

                        <div className="glass-card p-8 rounded-3xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-bl-full -mr-8 -mt-8 transition-all group-hover:bg-purple-500/20"></div>
                            <div className="w-14 h-14 bg-purple-500/20 rounded-2xl flex items-center justify-center mb-6 text-2xl">
                                ⚡
                            </div>
                            <h3 className="text-2xl font-bold mb-4">Lightning Backtest</h3>
                            <p className="text-slate-400 leading-relaxed">
                                Uji strategi Anda pada data historis 5 tahun terakhir dalam hitungan detik. Validasi sebelum meresikokan modal.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="py-32 relative bg-slate-900/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-5xl font-bold mb-6">Investasi <span className="text-indigo-500">Cerdas</span></h2>
                        <p className="text-xl text-slate-400">Pilih paket yang sesuai dengan perjalanan trading Anda.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
                        {/* Basic */}
                        <div className="glass p-8 rounded-3xl border border-white/5 flex flex-col">
                            <h3 className="text-xl font-semibold mb-2 text-slate-300">Starter</h3>
                            <div className="text-4xl font-bold mb-6">Gratis<span className="text-lg font-normal text-slate-500">/selamanya</span></div>
                            <ul className="space-y-4 mb-8 flex-1 text-slate-400">
                                <li className="flex items-center">✓ Manual Trading</li>
                                <li className="flex items-center">✓ Basic Charts</li>
                                <li className="flex items-center">✓ 1 Active Strategy</li>
                            </ul>
                            <Link href="/auth/signup" className="w-full py-4 rounded-xl border border-white/10 hover:bg-white/5 text-center transition-colors font-semibold">
                                Mulai Sekarang
                            </Link>
                        </div>

                        {/* Pro */}
                        <div className="p-1 rounded-3xl bg-gradient-to-b from-indigo-500 to-purple-500 relative transform md:-translate-y-4">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-4 py-1 rounded-full text-sm font-bold shadow-lg">
                                POPULAR CHOICE
                            </div>
                            <div className="bg-[#0f172a] p-8 rounded-[22px] h-full flex flex-col">
                                <h3 className="text-xl font-semibold mb-2 text-indigo-400">Pro Trader</h3>
                                <div className="text-4xl font-bold mb-6">$29<span className="text-lg font-normal text-slate-500">/bulan</span></div>
                                <ul className="space-y-4 mb-8 flex-1 text-slate-300">
                                    <li className="flex items-center text-white">✓ AI Strategy Generator</li>
                                    <li className="flex items-center text-white">✓ ML Auto-Trading (5 models)</li>
                                    <li className="flex items-center text-white">✓ Unlimited Backtesting</li>
                                    <li className="flex items-center text-white">✓ Priority Support</li>
                                </ul>
                                <Link href="/auth/signup" className="w-full py-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-center transition-colors font-bold shadow-lg shadow-indigo-500/25">
                                    Get Pro Access
                                </Link>
                            </div>
                        </div>

                        {/* Enterprise */}
                        <div className="glass p-8 rounded-3xl border border-white/5 flex flex-col">
                            <h3 className="text-xl font-semibold mb-2 text-slate-300">Institutional</h3>
                            <div className="text-4xl font-bold mb-6">$99<span className="text-lg font-normal text-slate-500">/bulan</span></div>
                            <ul className="space-y-4 mb-8 flex-1 text-slate-400">
                                <li className="flex items-center">✓ Custom ML Models</li>
                                <li className="flex items-center">✓ Dedicated Server</li>
                                <li className="flex items-center">✓ API Access</li>
                                <li className="flex items-center">✓ 24/7 Account Manager</li>
                            </ul>
                            <Link href="/auth/signup" className="w-full py-4 rounded-xl border border-white/10 hover:bg-white/5 text-center transition-colors font-semibold">
                                Contact Sales
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 border-t border-white/5 bg-slate-950">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid md:grid-cols-4 gap-12 mb-12">
                        <div className="col-span-2">
                            <span className="text-2xl font-bold text-gradient mb-6 block">NexusTrade</span>
                            <p className="text-slate-400 max-w-sm">
                                Membawa kecerdasan buatan ke dunia trading ritel. Aman, transparan, dan terbukti secara matematis.
                            </p>
                        </div>
                        <div>
                            <h4 className="font-bold mb-6 text-white">Platform</h4>
                            <ul className="space-y-4 text-slate-400">
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">Features</a></li>
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">Pricing</a></li>
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">API</a></li>
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">Status</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold mb-6 text-white">Legal</h4>
                            <ul className="space-y-4 text-slate-400">
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">Privacy Policy</a></li>
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">Terms of Service</a></li>
                                <li><a href="#" className="hover:text-indigo-400 transition-colors">Risk Disclaimer</a></li>
                            </ul>
                        </div>
                    </div>
                    <div className="pt-8 border-t border-white/5 text-center text-slate-500 text-sm">
                        &copy; 2024 NexusTrade Financial Technologies. All rights reserved.
                    </div>
                </div>
            </footer>
        </main>
    );
}
