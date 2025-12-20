"""
Custom Model Trainer
Wrapper for train_gru_xgboost_hybrid.py with custom config support
"""

import asyncio
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from loguru import logger

from ai.train_gru_xgboost_hybrid import train_model


class CustomModelTrainer:
    """Trains custom ML models with progress callbacks and cloud sync"""
    
    def __init__(
        self,
        symbol: str,
        llm_config: dict,
        model_name: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        supabase_sync: Optional[Any] = None  # SupabaseModelSync instance
    ):
        self.symbol = symbol
        self.llm_config = llm_config
        self.model_name = model_name or f"{symbol}_custom_{llm_config.get('timeframe', 'M15')}"
        self.progress_callback = progress_callback
        self.supabase_sync = supabase_sync
    
    def _update_progress(self, message: str, percent: int):
        """Update progress via callback"""
        if self.progress_callback:
            self.progress_callback(message, percent)
        logger.info(f"Training progress: {message} ({percent}%)")
    
    async def train(self) -> Dict[str, Any]:
        """Train the model with LLM configuration and sync to cloud"""
        try:
            self._update_progress("Initializing training...", 0)
            
            # Extract config
            timeframe = self.llm_config.get('timeframe', 'M15')
            features = self.llm_config.get('features', [])
            hyperparameters = self.llm_config.get('hyperparameters', {})
            
            self._update_progress("Loading market data...", 10)
            
            # Train model
            self._update_progress("Training GRU-XGBoost hybrid model...", 30)
            result = await asyncio.to_thread(
                train_model,
                symbol=self.symbol,
                timeframe=timeframe,
                features=features,
                **hyperparameters
            )
            
            self._update_progress("Model training complete!", 80)
            
            # Sync to Supabase if available
            if self.supabase_sync:
                self._update_progress("Syncing model to cloud...", 90)
                await self._sync_to_supabase(result)
            
            self._update_progress("Training complete!", 100)
            
            self.result = {
                'model_id': model_id,
                'symbol': self.symbol,
                'model_name': self.model_name,
                **result['metrics']
            }
            
            return self.result
            
        except Exception as e:
            logger.exception(f"Training error: {e}")
            self._update_progress(f"Error: {str(e)}", 0)
            raise
    
    def train(self) -> dict:
        """Train model synchronously (for non-async contexts)"""
        return asyncio.run(self.train_async())
