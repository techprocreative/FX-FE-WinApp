"""
NexusTrade Configuration Manager
Handles persistence of application configuration to JSON file.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from decimal import Decimal
from loguru import logger


@dataclass
class MT5ConfigData:
    """MT5 connection configuration (password excluded for security)"""
    login: Optional[int] = None
    server: Optional[str] = None
    timeout: int = 60000


@dataclass
class TradingConfigData:
    """Trading configuration for a symbol"""
    symbol: str = ""
    timeframe: str = "M15"
    volume: float = 0.01
    risk_percent: float = 1.0
    max_positions: int = 1
    confidence_threshold: float = 0.6
    sl_pips: float = 50.0
    tp_pips: float = 100.0
    magic_number: int = 88888


@dataclass
class ConfigData:
    """Complete application configuration"""
    mt5: MT5ConfigData = field(default_factory=MT5ConfigData)
    trading_configs: Dict[str, TradingConfigData] = field(default_factory=dict)
    last_sync_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'mt5': asdict(self.mt5),
            'trading_configs': {
                symbol: asdict(config) 
                for symbol, config in self.trading_configs.items()
            },
            'last_sync_time': self.last_sync_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigData':
        """Create ConfigData from dictionary"""
        config = cls()
        
        if 'mt5' in data:
            mt5_data = data['mt5']
            config.mt5 = MT5ConfigData(
                login=mt5_data.get('login'),
                server=mt5_data.get('server'),
                timeout=mt5_data.get('timeout', 60000)
            )
        
        if 'trading_configs' in data:
            for symbol, tc_data in data['trading_configs'].items():
                config.trading_configs[symbol] = TradingConfigData(
                    symbol=tc_data.get('symbol', symbol),
                    timeframe=tc_data.get('timeframe', 'M15'),
                    volume=tc_data.get('volume', 0.01),
                    risk_percent=tc_data.get('risk_percent', 1.0),
                    max_positions=tc_data.get('max_positions', 1),
                    confidence_threshold=tc_data.get('confidence_threshold', 0.6),
                    sl_pips=tc_data.get('sl_pips', 50.0),
                    tp_pips=tc_data.get('tp_pips', 100.0),
                    magic_number=tc_data.get('magic_number', 88888)
                )
        
        config.last_sync_time = data.get('last_sync_time')
        
        return config


class ConfigManager:
    """
    Manages application configuration persistence.
    Stores configuration in JSON format at ~/.nexustrade/config.json
    """
    
    DEFAULT_CONFIG_PATH = Path.home() / ".nexustrade" / "config.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigManager.
        
        Args:
            config_path: Optional custom path for config file.
                        Defaults to ~/.nexustrade/config.json
        """
        self._config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Optional[ConfigData] = None
        
        # Ensure directory exists
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
    
    @property
    def config_path(self) -> Path:
        """Get the configuration file path"""
        return self._config_path
    
    def load(self) -> ConfigData:
        """
        Load configuration from JSON file.
        
        Returns:
            ConfigData object with loaded or default configuration
        """
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = ConfigData.from_dict(data)
                logger.info(f"Configuration loaded from {self._config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}")
                self._config = ConfigData()
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self._config = ConfigData()
        else:
            logger.info(f"Config file not found, using defaults")
            self._config = ConfigData()
        
        return self._config
    
    def save(self, config: ConfigData) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config: ConfigData object to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            self._config = config
            logger.info(f"Configuration saved to {self._config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_mt5_config(self) -> MT5ConfigData:
        """
        Get MT5 connection configuration.
        
        Returns:
            MT5ConfigData with server info (password excluded)
        """
        if self._config is None:
            self.load()
        return self._config.mt5
    
    def set_mt5_config(self, config: MT5ConfigData) -> bool:
        """
        Set MT5 connection configuration.
        
        Args:
            config: MT5ConfigData to save (password should not be included)
            
        Returns:
            True if save successful
        """
        if self._config is None:
            self.load()
        
        self._config.mt5 = config
        return self.save(self._config)
    
    def get_trading_config(self, symbol: str) -> TradingConfigData:
        """
        Get trading configuration for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSD', 'XAUUSD')
            
        Returns:
            TradingConfigData for the symbol, or default if not found
        """
        if self._config is None:
            self.load()
        
        if symbol in self._config.trading_configs:
            return self._config.trading_configs[symbol]
        
        # Return default config for symbol
        return TradingConfigData(symbol=symbol)
    
    def set_trading_config(self, symbol: str, config: TradingConfigData) -> bool:
        """
        Set trading configuration for a symbol.
        
        Args:
            symbol: Trading symbol
            config: TradingConfigData to save
            
        Returns:
            True if save successful
        """
        if self._config is None:
            self.load()
        
        config.symbol = symbol  # Ensure symbol is set
        self._config.trading_configs[symbol] = config
        return self.save(self._config)
    
    def get_last_sync_time(self) -> Optional[str]:
        """Get the last model sync time"""
        if self._config is None:
            self.load()
        return self._config.last_sync_time
    
    def set_last_sync_time(self, sync_time: str) -> bool:
        """Set the last model sync time"""
        if self._config is None:
            self.load()
        self._config.last_sync_time = sync_time
        return self.save(self._config)
