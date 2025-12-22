"""Quick script to upload shared model using service role key"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add connector to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
connector_dir = project_root / "connector"
sys.path.insert(0, str(connector_dir))

from supabase import create_client

# Config
SUPABASE_URL = "https://jptguprshffbsthbeebe.supabase.co"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpwdGd1cHJzaGZmYnN0aGJlZWJlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjE5OTU3OSwiZXhwIjoyMDgxNzc1NTc5fQ.LHAwE-l0cGUzgpEDGc2eR_rQMcCRZsvgJyA2tGapj4g"

USER_ID = "1e3388e6-8f27-4bbd-9819-daf4c84d3444"
MODEL_ID = "6bf7fc87-8614-4db6-9127-877b64c5955f"
MODEL_PATH = Path.home() / ".nexustrade" / "models" / f"{MODEL_ID}.nexmodel"

def main():
    print("="*60)
    print("UPLOADING SHARED MODEL TO SUPABASE")
    print("="*60)
    
    import httpx
    
    # Storage path
    storage_path = f"{USER_ID}/{MODEL_ID}.nexmodel"
    
    # Direct upload using httpx with long timeout
    print(f"Uploading {MODEL_PATH} to {storage_path}...")
    
    with open(MODEL_PATH, 'rb') as f:
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
    
    # Insert metadata using supabase client
    print("Inserting metadata...")
    client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
    
    # Use columns based on actual DB schema
    metadata = {
        'id': MODEL_ID,
        'user_id': USER_ID,
        'name': 'btcusd_hybrid_shared',  # Required column
        'description': 'Default BTCUSD trading model (shared)',
        'symbol': 'BTCUSD',
        'model_type': 'xgboost',  # Valid check constraint value
        'timeframe': 'M15',  # Required column
        'accuracy': 0.65,
        'storage_path': storage_path,
        'is_active': True
    }
    client.table('ml_models').upsert(metadata).execute()
    print("✓ Metadata inserted!")
    
    print("\n✓ Upload complete!")

if __name__ == "__main__":
    main()
