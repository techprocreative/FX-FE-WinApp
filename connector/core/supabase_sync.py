"""
Supabase Client Helper for Connector
Handles cloud sync for ML models and metadata
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from supabase import create_client, Client
from loguru import logger


class SupabaseModelSync:
    """Handles ML model synchronization with Supabase"""
    
    def __init__(self, supabase_url: str, supabase_key: str, user_id: str):
        self.client: Client = create_client(supabase_url, supabase_key)
        self.user_id = user_id
        self.bucket_name = 'ml-models'
        self.local_models_dir = Path('./models')
        self.local_models_dir.mkdir(parents=True, exist_ok=True)
    
    async def fetch_user_models(self) -> List[Dict[str, Any]]:
        """Fetch all active models for the current user"""
        try:
            response = (self.client.table('ml_models')
                .select('*')
                .eq('user_id', self.user_id)
                .eq('is_active', True)
                .order('created_at', desc=True)
                .execute())
            
            logger.info(f"Fetched {len(response.data)} models from Supabase")
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []
    
    async def download_model(self, model_metadata: Dict[str, Any]) -> Optional[Path]:
        """Download model file from Supabase Storage"""
        try:
            model_id = model_metadata['id']
            storage_path = model_metadata.get('storage_path')
            
            if not storage_path:
                logger.warning(f"No storage path for model {model_id}")
                return None
            
            # Local path
            local_path = self.local_models_dir / f"{model_id}.enc"
            
            # Skip if already exists
            if local_path.exists():
                logger.info(f"Model {model_id} already exists locally")
                return local_path
            
            # Download from Supabase Storage
            logger.info(f"Downloading model {model_id} from {storage_path}")
            data = self.client.storage.from_(self.bucket_name).download(storage_path)
            
            # Save locally
            local_path.write_bytes(data)
            logger.success(f"Downloaded model {model_id} ({len(data)} bytes)")
            
            return local_path
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            return None
    
    async def upload_model(
        self,
        model_path: Path,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Upload model file and metadata to Supabase"""
        try:
            model_id = metadata.get('id')
            if not model_id:
                # Generate new ID
                import uuid
                model_id = str(uuid.uuid4())
                metadata['id'] = model_id
            
            # Storage path: {user_id}/{model_id}.enc
            storage_path = f"{self.user_id}/{model_id}.enc"
            
            # Upload file to Storage
            logger.info(f"Uploading model to {storage_path}")
            with open(model_path, 'rb') as f:
                file_data = f.read()
                (self.client.storage.from_(self.bucket_name)
                    .upload(storage_path, file_data, {'upsert': 'true'}))
            
            # Prepare metadata
            model_size = model_path.stat().st_size
            db_metadata = {
                'id': model_id,
                'user_id': self.user_id,
                'symbol': metadata.get('symbol'),
                'model_type': metadata.get('model_type', 'gru_xgboost_hybrid'),
                'accuracy': metadata.get('accuracy'),
                'win_rate': metadata.get('win_rate'),
                'kelly_fraction': metadata.get('kelly_fraction'),
                'sharpe_ratio': metadata.get('sharpe_ratio'),
                'max_drawdown': metadata.get('max_drawdown'),
                'config': json.dumps(metadata.get('config', {})),
                'features': metadata.get('features', []),
                'timeframe': metadata.get('timeframe'),
                'storage_path': storage_path,
                'model_size_bytes': model_size,
                'model_name': metadata.get('model_name'),
                'description': metadata.get('description'),
                'training_duration_seconds': metadata.get('training_duration'),
                'is_active': True
            }
            
            # Upsert metadata to database
            (self.client.table('ml_models')
                .upsert(db_metadata)
                .execute())
            
            logger.success(f"Uploaded model {model_id} successfully")
            return model_id
        except Exception as e:
            logger.error(f"Failed to upload model: {e}")
            return None
    
    async def update_model_status(self, model_id: str, is_active: bool):
        """Update model active status"""
        try:
            (self.client.table('ml_models')
                .update({'is_active': is_active, 'updated_at': datetime.utcnow().isoformat()})
                .eq('id', model_id)
                .eq('user_id', self.user_id)
                .execute())
            logger.info(f"Updated model {model_id} status to {is_active}")
        except Exception as e:
            logger.error(f"Failed to update model status: {e}")
    
    async def update_last_used(self, model_id: str):
        """Update model last used timestamp"""
        try:
            (self.client.table('ml_models')
                .update({'last_used_at': datetime.utcnow().isoformat()})
                .eq('id', model_id)
                .eq('user_id', self.user_id)
                .execute())
        except Exception as e:
            logger.error(f"Failed to update last used: {e}")
    
    async def delete_model(self, model_id: str):
        """Delete model from Supabase (soft delete)"""
        try:
            # Soft delete - just mark as inactive
            await self.update_model_status(model_id, False)
            logger.info(f"Deleted model {model_id}")
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
    
    async def get_model_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the latest active model for a symbol"""
        try:
            response = (self.client.table('ml_models')
                .select('*')
                .eq('user_id', self.user_id)
                .eq('symbol', symbol)
                .eq('is_active', True)
                .order('created_at', desc=True)
                .limit(1)
                .execute())
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get model for {symbol}: {e}")
            return None
