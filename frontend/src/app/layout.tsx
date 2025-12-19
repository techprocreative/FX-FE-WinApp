import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'NexusTrade - Forex Trading Platform',
    description: 'Platform trading forex dengan AI dan ML auto-trading',
    keywords: ['forex', 'trading', 'AI', 'ML', 'auto-trading', 'Indonesia'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="id">
            <body className={inter.className}>
                {children}
            </body>
        </html>
    );
}
