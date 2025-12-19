# NexusTrade

Platform Trading Forex dengan AI Strategy Generator dan ML Auto-Trading untuk pasar Indonesia.

## 🏗️ Arsitektur

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │  Supabase Cloud │     │  Windows App    │
│   (Next.js)     │◄───►│   (Database)    │◄───►│  (Backend+MT5)  │
│   Vercel        │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │   MT5 Server    │
                                                └─────────────────┘
```

## 📁 Struktur Project

```
nexustrade/
├── frontend/          # Next.js 14 (deploy ke Vercel)
├── supabase/          # Migrations & configurations
├── connector/         # Windows App (Python + PyQt6)
└── docs/              # Documentation
```

## 🚀 Quick Start

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local dengan Supabase credentials
npm run dev
```

### Windows Connector

```bash
cd connector
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Supabase

1. Buat project di [Supabase](https://supabase.com)
2. Copy URL dan anon key ke `.env.local`
3. Jalankan migration di SQL Editor

## 🔐 Environment Variables

### Frontend (.env.local)

```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
```

### Connector (~/.nexustrade/.env)

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
OPENROUTER_API_KEY=xxx
```

## 📦 Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **Windows App**: Python, PyQt6, FastAPI
- **MT5**: MetaTrader5 Python library
- **LLM**: OpenRouter (OpenAI-compatible)
- **ML**: scikit-learn, encrypted models

## 📄 License

Copyright © 2024 NexusTrade. All rights reserved.
