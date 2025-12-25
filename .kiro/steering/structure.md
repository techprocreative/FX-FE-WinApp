# Project Structure

## Root Organization

```
nexustrade/
├── frontend/          # Next.js web application
├── connector/         # Python desktop application
├── supabase/          # Database migrations and config
├── models/            # ML model storage (organized by asset)
├── ohlcv/             # Historical market data
├── scripts/           # Utility scripts for deployment
└── docs/              # Documentation
```

## Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── (admin)/           # Admin-only routes
│   │   ├── (dashboard)/       # Dashboard routes
│   │   ├── api/               # API routes
│   │   ├── auth/              # Authentication pages
│   │   └── dashboard/         # Main dashboard
│   ├── components/ui/         # Reusable UI components
│   └── lib/supabase/          # Supabase client configuration
├── package.json
├── next.config.js
├── tailwind.config.js
└── .env.example
```

## Backend Structure (`connector/`)

```
connector/
├── core/                      # Core business logic
│   ├── config.py             # Configuration management
│   ├── mt5_client.py         # MetaTrader 5 integration
│   └── supabase_sync.py      # Database synchronization
├── ui/                       # PyQt6 user interface
│   ├── components/           # Reusable UI components
│   ├── dialogs/              # Modal dialogs
│   ├── pages/                # Main application pages
│   └── widgets/              # Custom widgets
├── trading/                  # Trading logic
│   ├── auto_trader.py        # Automated trading engine
│   └── risk_manager.py       # Risk management
├── ai/                       # Machine learning models
│   └── train_*.py            # Model training scripts
├── api/                      # FastAPI server
│   ├── server.py             # API endpoints
│   └── llm_router.py         # LLM integration
├── security/                 # Security and encryption
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── property/             # Property-based tests
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── nexustrade.spec          # PyInstaller configuration
```

## Data Organization

### Models (`models/`)
```
models/
├── btcusd/                   # Bitcoin models
│   ├── crypto-optimized/     # Production crypto models
│   └── staging/              # Development models
├── eurusd/                   # EUR/USD forex models
│   ├── forex-optimized/      # Production forex models
│   └── staging/              # Development models
├── production/               # Shared production models
└── staging/                  # Shared staging models
```

### Market Data (`ohlcv/`)
```
ohlcv/
├── btc/                      # Bitcoin historical data
├── eurusd/                   # EUR/USD historical data
└── xauusd/                   # Gold historical data
```

## Database Structure (`supabase/`)

```
supabase/
├── migrations/               # SQL migration files
│   ├── 001_initial_schema.sql
│   └── 002_ml_models.sql
├── insert_models.sql         # Model metadata insertion
└── setup_storage.sql         # Storage bucket configuration
```

## Key Architectural Patterns

### UI Architecture (PyQt6)
- **Page-based navigation**: Each major feature is a separate page
- **Component composition**: Reusable components in `ui/components/`
- **Modern design system**: Consistent styling via `design_system.py`
- **Animation system**: Smooth transitions and loading states

### API Architecture (FastAPI)
- **RESTful endpoints**: Standard HTTP methods and status codes
- **Async/await**: Non-blocking operations for better performance
- **Pydantic models**: Type-safe request/response validation
- **Background tasks**: Long-running operations handled asynchronously

### Testing Architecture
- **Property-based testing**: Using Hypothesis for robust test generation
- **Layered testing**: Unit, integration, and property tests
- **Test fixtures**: Shared test data and mocks in `conftest.py`

### Configuration Management
- **Environment-based**: Different configs for dev/staging/production
- **Encrypted storage**: Sensitive data encrypted at rest
- **User preferences**: Saved locally with automatic backup

## Naming Conventions

- **Python files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **UI components**: `PascalCase` (following PyQt conventions)
- **Database tables**: `snake_case`
- **API endpoints**: `kebab-case` in URLs