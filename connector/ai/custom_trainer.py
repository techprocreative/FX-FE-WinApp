"""
Custom Model Trainer
Wrapper for train_gru_xgboost_hybrid.py with custom config support
"""

import asyncio
from pathlib import Path
from typing import Callable, Optional, Dict
from loguru import logger

from ai.train_gru_xgboost_hybrid import GRUXGBoostHybrid


class CustomModelTrainer:
    """
    Wrapper for training custom models with LLM-generated configs
    Supports progress callbacks for UI updates
    """
    
    def __init__(self, config: dict, symbol: str, model_name: str, 
                 progress_callback: Optional[Callable[[str, int], None]] = None):
        """
        Args:
            config: LLM-generated training config
            symbol: Trading symbol (BTCUSD, XAUUSD, etc.)
            model_name: Custom model name
            progress_callback: Callback(message, percent)
        """
        self.config = config
        self.symbol = symbol
        self.model_name = model_name
        self.progress_callback = progress_callback or (lambda m, p: None)
        
        self.trainer = GRUXGBoostHybrid()
        self.result = None
    
    def _update_progress(self, message: str, percent: int):
        """Update progress"""
        logger.info(f"Training progress: {message} ({percent}%)")
        self.progress_callback(message, percent)
    
    async def train_async(self) -> dict:
        """Train model asynchronously"""
        try:
            self._update_progress("Loading data...", 10)
            
            # Load data
            df = self.trainer.load_data(self.symbol)
            
            self._update_progress("Preparing features...", 20)
            
            # Train model (this is synchronous, but we update progress)
            self._update_progress("Training GRU model...", 30)
            
            # Run training in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.trainer.train, self.symbol)
            
            self._update_progress("Training XGBoost meta-filter...", 60)
            
            # Training is complete at this point
            self._update_progress("Evaluating model...", 80)
            
            # Save model
            self._update_progress("Saving model...", 90)
            model_id = self.trainer.save(result, self.symbol)
            
            self._update_progress("Syncing to Supabase...", 95)
            
            # TODO: Sync metadata to Supabase
            # This will be implemented when we add model metadata sync
            
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
