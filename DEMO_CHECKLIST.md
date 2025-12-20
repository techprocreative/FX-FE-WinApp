# NexusTrade MVP Live Demo Checklist

## Frontend (Vercel)

### Prerequisites
- [ ] Node.js 18+ installed
- [ ] npm or yarn

### Deployment Steps
1. **Create Vercel Account** (if not exists)
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   ```

2. **Configure Environment Variables** (in Vercel Dashboard)
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   ```

3. **Deploy**
   ```bash
   cd frontend
   vercel
   ```

---

## Backend (Windows Connector)

### Prerequisites
- [ ] Python 3.12+
- [ ] MetaTrader 5 installed with demo account
- [ ] MT5 API enabled in settings

### Setup Steps
1. **Create Virtual Environment**
   ```bash
   cd connector
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Settings**
   Create `~/.nexustrade/config.json`:
   ```json
   {
     "supabase": {
       "url": "https://xxx.supabase.co",
       "anon_key": "your-anon-key",
       "service_key": "your-service-key"
     },
     "openrouter": {
       "api_key": "your-openrouter-key"
     },
     "api_server": {
       "host": "127.0.0.1",
       "port": 8000
     }
   }
   ```

4. **Run Application**
   ```bash
   python main.py
   ```

---

## Supabase Database

### Run Migration
```sql
-- Execute 001_initial_schema.sql in Supabase SQL Editor
```

### Required Tables
- `users` - User accounts
- `subscriptions` - Subscription status
- `api_keys` - User API keys
- `trades` - Trade history
- `ml_models` - Model metadata

---

## ML Models Ready for Demo

| Model | Win Rate | Status |
|-------|----------|--------|
| `xauusd_hybrid` | 54.7% | ✅ Ready |
| `btcusd_hybrid` | 46.0% | ✅ Ready |
| `xauusd_emacci_v2` | 36.4% | ✅ Ready |
| `btcusd_emacci_v2` | 46.2% | ✅ Ready |

---

## Demo Flow

1. **Landing Page**
   - Show features and pricing

2. **Login/Signup**
   - Register demo account
   - Login

3. **Dashboard**
   - Connect MT5 via Windows app
   - Show account balance

4. **Auto-Trading**
   - Load ML model
   - Start auto-trading
   - Show live signals and trades

5. **Trade History**
   - View executed trades
   - Show profit/loss
