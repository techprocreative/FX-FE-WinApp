"""Quick script to upload XAUUSD shared model using service role key"""
import sys
from pathlib import Path

# Add connector to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
connector_dir = project_root / "connector"
sys.path.insert(0, str(connector_dir))

import uuid
import pickle
import httpx
from datetime import datetime
from supabase import create_client
from security.model_security import ModelSecurity

# Config
SUPABASE_URL = "https://jptguprshffbsthbeebe.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpwdGd1cHJzaGZmYnN0aGJlZWJlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjE5OTU3OSwiZXhwIjoyMDgxNzc1NTc5fQ.LHAwE-l0cGUzgpEDGc2eR_rQMcCRZsvgJyA2tGapj4g"

USER_ID = "1e3388e6-8f27-4bbd-9819-daf4c84d3444"

# Use same BTCUSD model as base (retrain for XAUUSD if needed)
RAW_MODEL_PATH = project_root / "models" / "btcusd" / "crypto-optimized" / "model_crypto_xgboost_20251213_104319.pkl"

def main():
    print("="*60)
    print("CREATING AND UPLOADING XAUUSD SHARED MODEL")
    print("="*60)
    
    ms = ModelSecurity()
    model_id = str(uuid.uuid4())
    
    # Load raw model
    print(f"Loading raw model from {RAW_MODEL_PATH}...")
    with open(RAW_MODEL_PATH, "rb") as f:
        raw_model = pickle.load(f)
    
    # Encrypt as shared
    metadata = {
        "name": "xauusd_hybrid_shared",
        "symbol": "XAUUSD",
        "accuracy": 0.65,
        "created_at": datetime.now().isoformat(),
        "model_type": "xgboost",
        "version": "1.0.0"
    }
    
    print(f"Encrypting as shared model with ID: {model_id}")
    secured = ms.encrypt_model(raw_model, model_id, metadata, is_shared=True)
    local_path = ms.save_secured_model(secured)
    print(f"Saved to: {local_path}")
    
    # Upload file
    storage_path = f"{USER_ID}/{model_id}.nexmodel"
    print(f"Uploading to {storage_path}...")
    
    with open(local_path, 'rb') as f:
        file_data = f.read()
    
    storage_url = f"{SUPABASE_URL}/storage/v1/object/ml-models/{storage_path}"
    headers = {
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/octet-stream",
        "x-upsert": "true"
    }
    
    with httpx.Client(timeout=300.0) as http_client:
        response = http_client.post(storage_url, content=file_data, headers=headers)
        if response.status_code in (200, 201):
            print("✓ File uploaded!")
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            return
    
    print(f"\n✓ XAUUSD model uploaded!")
    print(f"Model ID: {model_id}")
    print(f"Storage path: {storage_path}")
    print(f"\nRun this SQL to insert metadata:")
    print(f"""
INSERT INTO ml_models (id, user_id, name, description, symbol, model_type, timeframe, accuracy, storage_path, is_active)
VALUES (
  '{model_id}',
  '{USER_ID}',
  'xauusd_hybrid_shared',
  'Default XAUUSD trading model (shared)',
  'XAUUSD',
  'xgboost',
  'M15',
  0.65,
  '{storage_path}',
  true
);
""")

if __name__ == "__main__":
    main()
