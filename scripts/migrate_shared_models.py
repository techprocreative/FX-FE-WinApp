"""
Script to re-encrypt existing models as shared models
This allows default models to be used on any user's machine.
"""

import os
import sys
import pickle
import asyncio
from pathlib import Path
from datetime import datetime

# Add connector to path - handle running from different directories
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
connector_dir = project_root / "connector"
sys.path.insert(0, str(connector_dir))

from security.model_security import ModelSecurity
from core.supabase_sync import SupabaseModelSync
from core.config import Config

# Models to re-encrypt (found in models/ directory)
MODELS_TO_MIGRATE = [
    {
        "raw_pkl_path": "models/btcusd/crypto-optimized/model_crypto_xgboost_20251213_104319.pkl",
        "symbol": "BTCUSD",
        "name": "btcusd_hybrid",
        "accuracy": 0.65,
        "model_type": "gru_xgboost_hybrid"
    },
    # Note: No XAUUSD model found in models/ directory yet
    # If you have one, add it here:
    # {
    #     "raw_pkl_path": "models/xauusd/...",
    #     "symbol": "XAUUSD", 
    #     "name": "xauusd_hybrid",
    #     "accuracy": 0.65,
    #     "model_type": "gru_xgboost_hybrid"
    # },
]


def re_encrypt_as_shared(model_path: Path, symbol: str, name: str, accuracy: float):
    """Load raw pkl, re-encrypt with shared master key"""
    ms = ModelSecurity()
    
    # Load raw model
    print(f"Loading raw model from {model_path}...")
    with open(model_path, "rb") as f:
        raw_model = pickle.load(f)
    
    # Create model ID (use name as base)
    import uuid
    model_id = str(uuid.uuid4())
    
    metadata = {
        "name": name,
        "symbol": symbol,
        "accuracy": accuracy,
        "created_at": datetime.now().isoformat(),
        "model_type": "gru_xgboost_hybrid",
        "version": "1.0.0"
    }
    
    # Encrypt as SHARED model
    print(f"Encrypting as shared model with ID: {model_id}")
    secured = ms.encrypt_model(raw_model, model_id, metadata, is_shared=True)
    
    # Save locally
    file_path = ms.save_secured_model(secured)
    print(f"Saved to: {file_path}")
    
    return file_path, model_id, metadata


async def upload_to_supabase(local_path: Path, model_id: str, metadata: dict, admin_user_id: str):
    """Upload the model to Supabase storage"""
    config = Config()
    
    sync = SupabaseModelSync(
        supabase_url=config.supabase.url,
        supabase_key=config.supabase.anon_key,
        user_id=admin_user_id,
        access_token=None  # Will use anon key for upload
    )
    
    upload_metadata = {
        "id": model_id,
        "symbol": metadata['symbol'],
        "model_type": metadata.get('model_type', 'gru_xgboost_hybrid'),
        "accuracy": metadata.get('accuracy'),
        "model_name": metadata['name'],
        "description": f"Default {metadata['symbol']} trading model (shared)"
    }
    
    result = await sync.upload_model(local_path, upload_metadata)
    if result:
        print(f"✓ Uploaded {model_id} to Supabase")
    else:
        print(f"✗ Failed to upload {model_id}")
    
    return result


async def main():
    print("="*60)
    print("RE-ENCRYPT MODELS AS SHARED")
    print("="*60)
    
    # Get admin user ID from environment or use default
    admin_user_id = os.environ.get("ADMIN_USER_ID", "")
    if not admin_user_id:
        admin_user_id = input("Enter admin user_id (from Supabase auth): ").strip()
    
    if not admin_user_id:
        print("Error: No admin_user_id provided")
        return
    
    base_dir = Path(__file__).parent.parent
    
    for model_info in MODELS_TO_MIGRATE:
        raw_path = base_dir / model_info["raw_pkl_path"]
        
        if not raw_path.exists():
            print(f"⚠ Raw model not found: {raw_path}")
            continue
        
        # Re-encrypt
        local_path, model_id, metadata = re_encrypt_as_shared(
            raw_path,
            model_info["symbol"],
            model_info["name"],
            model_info["accuracy"]
        )
        
        # Upload to Supabase
        await upload_to_supabase(local_path, model_id, metadata, admin_user_id)
    
    print("\n✓ Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())
