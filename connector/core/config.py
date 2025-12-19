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
    
    def __post_init__(self):
        """Load configuration from environment"""
        # Create directories
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load .env file
        if self.config_path.exists():
            load_dotenv(self.config_path)
        
        # Load Supabase config
        self.supabase.url = os.getenv("SUPABASE_URL", "")
        self.supabase.anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        
        # Load OpenRouter config
        self.openrouter.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter.default_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4-turbo")
        
        # Load API server config
        self.api_server.host = os.getenv("API_HOST", "127.0.0.1")
        self.api_server.port = int(os.getenv("API_PORT", "8765"))
    
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
"""
        self.config_path.write_text(env_content)
    
    def is_configured(self) -> bool:
        """Check if essential configuration is set"""
        return bool(self.supabase.url and self.supabase.anon_key)
