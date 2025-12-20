"""
NexusTrade Configuration Module
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class SupabaseConfig:
    """Supabase connection configuration"""
    url: str = ""
    anon_key: str = ""
    

@dataclass
class OpenRouterConfig:
    """OpenRouter API configuration"""
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-4-turbo"


@dataclass  
class MT5Config:
    """MetaTrader 5 configuration"""
    login: Optional[int] = None
    password: Optional[str] = None
    server: Optional[str] = None
    timeout: int = 60000
    

@dataclass
class APIServerConfig:
    """Local API server configuration"""
    host: str = "127.0.0.1"
    port: int = 8765


@dataclass
class Config:
    """Main application configuration"""
    
    supabase: SupabaseConfig = field(default_factory=SupabaseConfig)
    openrouter: OpenRouterConfig = field(default_factory=OpenRouterConfig)
    mt5: MT5Config = field(default_factory=MT5Config)
    api_server: APIServerConfig = field(default_factory=APIServerConfig)
    
    # App paths
    app_dir: Path = field(default_factory=lambda: Path.home() / ".nexustrade")
    models_dir: Path = field(default_factory=lambda: Path.home() / ".nexustrade" / "models")
    logs_dir: Path = field(default_factory=lambda: Path.home() / ".nexustrade" / "logs")
    
    config_path: Path = field(default_factory=lambda: Path.home() / ".nexustrade" / ".env")
    
    def __init__(self, config_path: Optional[str] = None):
        """Load configuration from .env file"""
        # Initialize dataclass fields first
        self.supabase = SupabaseConfig()
        self.openrouter = OpenRouterConfig()
        self.mt5 = MT5Config()
        self.api_server = APIServerConfig()
        self.app_dir = Path.home() / ".nexustrade"
        self.models_dir = self.app_dir / "models"
        self.logs_dir = self.app_dir / "logs"

        # Create directories
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        if config_path is None:
            # Default config path
            config_dir = Path.home() / '.nexustrade'
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / '.env'
        
        self.config_path = Path(config_path)
        
        # Load environment variables
        if self.config_path.exists():
            load_dotenv(self.config_path)
            logger.info(f"Configuration loaded from {self.config_path}")
        else:
            logger.info(f"Configuration file not found: {self.config_path}")
            logger.info("Using default configuration...")
        
        # Hardcoded Supabase credentials (same as frontend)
        # Users don't need to configure this - they just login with email/password
        self.supabase = SupabaseConfig(
            url="https://jptguprshffbsthbeebe.supabase.co",
            anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpwdGd1cHJzaGZmYnN0aGJlZWJlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxOTk1NzksImV4cCI6MjA4MTc3NTU3OX0.xuqKeVrqfIRcOSQgmuIgpaegy3hgiC2GS7iq5XVRHzU"
        )
        
        logger.info(f"✓ Supabase configured")
        
        # Load OpenRouter config
        self.openrouter.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter.default_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4-turbo")
        
        # Load API server config
        self.api_server.host = os.getenv("API_HOST", "127.0.0.1")
        self.api_server.port = int(os.getenv("API_PORT", "8765"))

        logger.info(f"✓ Supabase URL: {self.supabase.url[:30]}...")
        logger.info(f"✓ API Host: {self.api_server.host}")
        logger.info(f"✓ API Port: {self.api_server.port}")
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = """# NexusTrade Connector Configuration
# 
# Get your Supabase credentials from:
# https://supabase.com/dashboard → Your Project → Settings → API
#
# IMPORTANT: Replace the placeholder values below with your actual credentials!

# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here

# OpenRouter Configuration (Optional)
# OPENROUTER_API_KEY=your_openrouter_api_key
# OPENROUTER_MODEL=openai/gpt-4-turbo

# API Configuration
API_HOST=127.0.0.1
API_PORT=8765

# MT5 Configuration (Optional - can be set in UI)
# MT5_LOGIN=
# MT5_PASSWORD=
# MT5_SERVER=
"""
        
        self.config_path.write_text(default_config)
        logger.info(f"Created default configuration file: {self.config_path}")
        logger.warning("⚠️  Please edit the configuration file and add your Supabase credentials!")
    
    def save(self):
        """Save configuration to .env file"""
        env_content = f"""# NexusTrade Configuration

# Supabase
SUPABASE_URL={self.supabase.url}
SUPABASE_ANON_KEY={self.supabase.anon_key}

# OpenRouter
OPENROUTER_API_KEY={self.openrouter.api_key}
OPENROUTER_MODEL={self.openrouter.default_model}

# API Server
API_HOST={self.api_server.host}
API_PORT={self.api_server.port}

# MT5
MT5_LOGIN={self.mt5.login if self.mt5.login is not None else ''}
MT5_PASSWORD={self.mt5.password if self.mt5.password is not None else ''}
MT5_SERVER={self.mt5.server if self.mt5.server is not None else ''}
"""
        self.config_path.write_text(env_content)
    
    def is_configured(self) -> bool:
        """Check if essential configuration is set"""
        return bool(self.supabase.url and self.supabase.anon_key)
