# Technology Stack

## Architecture

Multi-component system with clear separation of concerns:
- **Frontend**: Next.js 14 web application (deployed to Vercel)
- **Backend**: Python desktop application with embedded API server
- **Database**: Supabase (PostgreSQL) for cloud data storage
- **Trading**: MetaTrader 5 integration for live market access

## Frontend Stack

- **Framework**: Next.js 14 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand
- **UI Components**: Custom components with Lucide React icons
- **Charts**: Recharts for trading visualizations
- **Authentication**: Supabase Auth with SSR support

## Backend Stack

- **Language**: Python 3.12+
- **UI Framework**: PyQt6 with WebEngine support
- **API Server**: FastAPI with uvicorn
- **Trading**: MetaTrader5 Python library
- **ML/AI**: scikit-learn, XGBoost, TensorFlow/Keras
- **Data Processing**: pandas, numpy
- **Security**: cryptography, pycryptodome for model encryption
- **Logging**: loguru with structured logging

## Database & Cloud

- **Primary DB**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage for model files
- **LLM Integration**: OpenRouter API (OpenAI-compatible)

## Development Tools

- **Testing**: pytest with asyncio, coverage, and hypothesis
- **Code Quality**: black formatter
- **Packaging**: PyInstaller for Windows executable
- **Environment**: python-dotenv for configuration

## Common Commands

### Frontend Development
```bash
cd frontend
npm install
npm run dev          # Development server
npm run build        # Production build
npm run lint         # ESLint check
npm run type-check   # TypeScript validation
```

### Backend Development
```bash
cd connector
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py       # Run application
python syntax_check.py  # Validate syntax
```

### Testing
```bash
cd connector
pytest               # Run all tests
pytest tests/unit/   # Unit tests only
pytest tests/property/  # Property-based tests
pytest --cov        # With coverage
```

### Building Windows Executable
```bash
cd connector
build.bat           # Full build with cleanup
# or
pyinstaller nexustrade.spec --clean --noconfirm
```

### Database Migrations
```sql
-- Run in Supabase SQL Editor
-- Files in supabase/migrations/ folder
```

## Configuration

- **Frontend**: `.env.local` with Supabase credentials
- **Backend**: `~/.nexustrade/.env` with API keys and trading config
- **High-DPI**: Automatic scaling support for 4K displays
- **Logging**: Structured logs with rotation (10MB, 7 days retention)