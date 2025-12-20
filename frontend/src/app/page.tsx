import Link from 'next/link';

export default function HomePage() {
    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)',
            color: 'white',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
            {/* Navbar */}
            <nav style={{
                padding: '1.5rem 2rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(15, 23, 42, 0.8)',
                backdropFilter: 'blur(10px)',
                borderBottom: '1px solid rgba(6, 182, 212, 0.2)'
            }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0, color: '#06b6d4' }}>
                    NexusTrade
                </h1>
                <div style={{ display: 'flex', gap: '1rem' }}>
                    <Link href="/auth/login" style={{
                        padding: '0.5rem 1.5rem',
                        background: 'rgba(6, 182, 212, 0.1)',
                        border: '1px solid rgba(6, 182, 212, 0.3)',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        color: '#06b6d4',
                        fontWeight: '500',
                        transition: 'all 0.3s'
                    }}>
                        Login
                    </Link>
                    <Link href="/auth/signup" style={{
                        padding: '0.5rem 1.5rem',
                        background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                        borderRadius: '8px',
                        textDecoration: 'none',
                        color: 'white',
                        fontWeight: 'bold',
                        boxShadow: '0 4px 20px rgba(6, 182, 212, 0.3)'
                    }}>
                        Daftar Gratis
                    </Link>
                </div>
            </nav>

            {/* Hero */}
            <div style={{
                maxWidth: '1200px',
                margin: '0 auto',
                padding: '6rem 2rem',
                textAlign: 'center'
            }}>
                <div style={{
                    display: 'inline-block',
                    padding: '0.5rem 1rem',
                    background: 'rgba(6, 182, 212, 0.15)',
                    border: '1px solid rgba(6, 182, 212, 0.3)',
                    borderRadius: '20px',
                    fontSize: '0.875rem',
                    marginBottom: '2rem',
                    color: '#06b6d4'
                }}>
                    🚀 AI Trading Platform v1.0
                </div>

                <h1 style={{
                    fontSize: 'clamp(2.5rem, 8vw, 4.5rem)',
                    fontWeight: '900',
                    lineHeight: '1.2',
                    marginBottom: '1.5rem',
                    background: 'linear-gradient(135deg, #ffffff, #06b6d4)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                }}>
                    Trading Forex dengan<br />
                    Kecerdasan Buatan
                </h1>

                <p style={{
                    fontSize: '1.25rem',
                    maxWidth: '600px',
                    margin: '0 auto 3rem',
                    opacity: 0.9,
                    lineHeight: '1.6',
                    color: '#cbd5e1'
                }}>
                    Platform auto-trading yang menggabungkan Machine Learning dengan analisis teknikal untuk hasil maksimal
                </p>

                <div style={{
                    display: 'flex',
                    gap: '1rem',
                    justifyContent: 'center',
                    flexWrap: 'wrap'
                }}>
                    <Link href="/auth/signup" style={{
                        padding: '1rem 2.5rem',
                        background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                        borderRadius: '12px',
                        textDecoration: 'none',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: '1.125rem',
                        boxShadow: '0 10px 40px rgba(6, 182, 212, 0.4)',
                        transition: 'transform 0.3s'
                    }}>
                        Mulai Sekarang →
                    </Link>
                    <a href="#features" style={{
                        padding: '1rem 2.5rem',
                        background: 'rgba(6, 182, 212, 0.1)',
                        border: '2px solid rgba(6, 182, 212, 0.3)',
                        borderRadius: '12px',
                        textDecoration: 'none',
                        color: '#06b6d4',
                        fontWeight: 'bold',
                        fontSize: '1.125rem'
                    }}>
                        Lihat Fitur
                    </a>
                </div>
            </div>

            {/* Stats */}
            <div style={{
                background: 'rgba(15, 23, 42, 0.6)',
                padding: '3rem 2rem',
                borderTop: '1px solid rgba(6, 182, 212, 0.2)',
                borderBottom: '1px solid rgba(6, 182, 212, 0.2)'
            }}>
                <div style={{
                    maxWidth: '1200px',
                    margin: '0 auto',
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '2rem',
                    textAlign: 'center'
                }}>
                    <div>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#06b6d4' }}>$1.2M+</div>
                        <div style={{ opacity: 0.7, marginTop: '0.5rem', color: '#cbd5e1' }}>Trading Volume</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#10b981' }}>98.5%</div>
                        <div style={{ opacity: 0.7, marginTop: '0.5rem', color: '#cbd5e1' }}>AI Accuracy</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#06b6d4' }}>24/7</div>
                        <div style={{ opacity: 0.7, marginTop: '0.5rem', color: '#cbd5e1' }}>Auto Trading</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#14b8a6' }}>&lt;50ms</div>
                        <div style={{ opacity: 0.7, marginTop: '0.5rem', color: '#cbd5e1' }}>Execution</div>
                    </div>
                </div>
            </div>

            {/* Features */}
            <div id="features" style={{
                maxWidth: '1200px',
                margin: '0 auto',
                padding: '6rem 2rem'
            }}>
                <h2 style={{
                    fontSize: '2.5rem',
                    fontWeight: 'bold',
                    textAlign: 'center',
                    marginBottom: '4rem',
                    color: 'white'
                }}>
                    Fitur Unggulan
                </h2>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '2rem'
                }}>
                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        padding: '2rem',
                        borderRadius: '16px',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(6, 182, 212, 0.2)',
                        transition: 'all 0.3s'
                    }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧠</div>
                        <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#06b6d4' }}>
                            AI Strategy Generator
                        </h3>
                        <p style={{ opacity: 0.8, lineHeight: '1.6', color: '#cbd5e1' }}>
                            Buat strategi trading kompleks hanya dengan menjelaskan ide Anda dalam bahasa sehari-hari
                        </p>
                    </div>

                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        padding: '2rem',
                        borderRadius: '16px',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(6, 182, 212, 0.2)',
                        transition: 'all 0.3s'
                    }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚡</div>
                        <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#06b6d4' }}>
                            Ultra-Fast Backtesting
                        </h3>
                        <p style={{ opacity: 0.8, lineHeight: '1.6', color: '#cbd5e1' }}>
                            Validasi strategi dengan data historis 5 tahun dalam hitungan detik
                        </p>
                    </div>

                    <div style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        padding: '2rem',
                        borderRadius: '16px',
                        backdropFilter: 'blur(10px)',
                        border: '1px solid rgba(6, 182, 212, 0.2)',
                        transition: 'all 0.3s'
                    }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🤖</div>
                        <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#06b6d4' }}>
                            ML Auto-Trading
                        </h3>
                        <p style={{ opacity: 0.8, lineHeight: '1.6', color: '#cbd5e1' }}>
                            Model Machine Learning mengeksekusi trade 24/7 berdasarkan probabilitas tertinggi
                        </p>
                    </div>
                </div>
            </div>

            {/* Pricing */}
            <div style={{
                background: 'rgba(15, 23, 42, 0.6)',
                padding: '6rem 2rem',
                borderTop: '1px solid rgba(6, 182, 212, 0.2)'
            }}>
                <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
                    <h2 style={{
                        fontSize: '2.5rem',
                        fontWeight: 'bold',
                        textAlign: 'center',
                        marginBottom: '4rem',
                        color: 'white'
                    }}>
                        Paket Langganan
                    </h2>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                        gap: '2rem',
                        maxWidth: '1000px',
                        margin: '0 auto'
                    }}>
                        {/* Free */}
                        <div style={{
                            background: 'rgba(30, 41, 59, 0.5)',
                            padding: '2rem',
                            borderRadius: '16px',
                            border: '1px solid rgba(6, 182, 212, 0.2)'
                        }}>
                            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#cbd5e1' }}>Starter</h3>
                            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem', color: 'white' }}>
                                Gratis
                            </div>
                            <ul style={{ listStyle: 'none', padding: 0, marginBottom: '2rem', color: '#cbd5e1' }}>
                                <li style={{ marginBottom: '0.75rem' }}>✓ Manual Trading</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ 30 Hari History</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ 10 AI Request/hari</li>
                            </ul>
                            <Link href="/auth/signup" style={{
                                display: 'block',
                                padding: '0.75rem',
                                background: 'rgba(6, 182, 212, 0.1)',
                                border: '1px solid rgba(6, 182, 212, 0.3)',
                                borderRadius: '8px',
                                textAlign: 'center',
                                textDecoration: 'none',
                                color: '#06b6d4',
                                fontWeight: 'bold'
                            }}>
                                Mulai Gratis
                            </Link>
                        </div>

                        {/* Pro */}
                        <div style={{
                            background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(20, 184, 166, 0.1))',
                            padding: '2rem',
                            borderRadius: '16px',
                            border: '2px solid #06b6d4',
                            position: 'relative',
                            transform: 'scale(1.05)',
                            boxShadow: '0 10px 40px rgba(6, 182, 212, 0.3)'
                        }}>
                            <div style={{
                                position: 'absolute',
                                top: '-12px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                                color: 'white',
                                padding: '0.25rem 1rem',
                                borderRadius: '20px',
                                fontSize: '0.75rem',
                                fontWeight: 'bold'
                            }}>
                                POPULER
                            </div>
                            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#06b6d4' }}>Pro Trader</h3>
                            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem', color: 'white' }}>
                                Rp 449K<span style={{ fontSize: '1rem', fontWeight: 'normal', color: '#cbd5e1' }}>/bln</span>
                            </div>
                            <ul style={{ listStyle: 'none', padding: 0, marginBottom: '2rem', color: 'white' }}>
                                <li style={{ marginBottom: '0.75rem' }}>✓ AI Strategy Generator</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ ML Auto-Trading</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ Unlimited Backtesting</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ Priority Support</li>
                            </ul>
                            <Link href="/auth/signup" style={{
                                display: 'block',
                                padding: '0.75rem',
                                background: 'linear-gradient(135deg, #06b6d4, #14b8a6)',
                                borderRadius: '8px',
                                textAlign: 'center',
                                textDecoration: 'none',
                                color: 'white',
                                fontWeight: 'bold',
                                boxShadow: '0 4px 20px rgba(6, 182, 212, 0.4)'
                            }}>
                                Upgrade Pro
                            </Link>
                        </div>

                        {/* Enterprise */}
                        <div style={{
                            background: 'rgba(30, 41, 59, 0.5)',
                            padding: '2rem',
                            borderRadius: '16px',
                            border: '1px solid rgba(6, 182, 212, 0.2)'
                        }}>
                            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: '#cbd5e1' }}>Enterprise</h3>
                            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem', color: 'white' }}>
                                Custom
                            </div>
                            <ul style={{ listStyle: 'none', padding: 0, marginBottom: '2rem', color: '#cbd5e1' }}>
                                <li style={{ marginBottom: '0.75rem' }}>✓ Custom AI Models</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ Dedicated Server</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ White Label</li>
                                <li style={{ marginBottom: '0.75rem' }}>✓ 24/7 Support</li>
                            </ul>
                            <Link href="/auth/signup" style={{
                                display: 'block',
                                padding: '0.75rem',
                                background: 'rgba(6, 182, 212, 0.1)',
                                border: '1px solid rgba(6, 182, 212, 0.3)',
                                borderRadius: '8px',
                                textAlign: 'center',
                                textDecoration: 'none',
                                color: '#06b6d4',
                                fontWeight: 'bold'
                            }}>
                                Hubungi Sales
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer style={{
                padding: '3rem 2rem',
                textAlign: 'center',
                borderTop: '1px solid rgba(6, 182, 212, 0.2)',
                color: '#94a3b8'
            }}>
                <p>© 2024 NexusTrade. All rights reserved.</p>
            </footer>
        </div>
    );
}
