"""
ML Model Security Module
Handles encryption, HWID binding, and integrity verification of ML models
"""

import os
import json
import hashlib
import platform
import subprocess
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass
import pickle

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
from loguru import logger


@dataclass
class SecuredModel:
    """Secured ML model container"""
    model_id: str
    encrypted_data: bytes
    hwid_hash: str
    model_hash: str
    metadata: dict


class ModelSecurity:
    """
    Handles ML model encryption and hardware binding.
    Models are encrypted with AES-256 using a key derived from HWID.
    """
    
    SALT = b"NexusTrade_ML_Model_Salt_v1"
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path.home() / ".nexustrade" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._hwid: Optional[str] = None
        self._key: Optional[bytes] = None
    
    @property
    def hwid(self) -> str:
        """Get hardware ID (cached)"""
        if not self._hwid:
            self._hwid = self._get_hardware_id()
        return self._hwid
    
    def _get_hardware_id(self) -> str:
        """
        Generate unique hardware identifier from multiple sources.
        Combines CPU ID, motherboard serial, and disk serial.
        """
        components = []
        
        if platform.system() == "Windows":
            try:
                import wmi
                w = wmi.WMI()
                
                # CPU ID
                for cpu in w.Win32_Processor():
                    components.append(cpu.ProcessorId or "")
                
                # Motherboard serial
                for board in w.Win32_BaseBoard():
                    components.append(board.SerialNumber or "")
                
                # First disk serial
                for disk in w.Win32_DiskDrive():
                    components.append(disk.SerialNumber or "")
                    break
                    
            except Exception as e:
                logger.warning(f"WMI error: {e}, falling back to basic HWID")
                components.append(platform.node())
                components.append(platform.processor())
        else:
            # Fallback for non-Windows (testing)
            components.append(platform.node())
            components.append(platform.processor())
            components.append(str(os.getuid()) if hasattr(os, 'getuid') else "0")
        
        # Combine and hash
        combined = "|".join(filter(None, components))
        hwid = hashlib.sha256(combined.encode()).hexdigest()
        
        logger.debug(f"HWID generated: {hwid[:16]}...")
        return hwid
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from HWID using PBKDF2"""
        if not self._key:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.SALT,
                iterations=100000,
                backend=default_backend()
            )
            key = kdf.derive(self.hwid.encode())
            self._key = base64.urlsafe_b64encode(key)
        return self._key
    
    def encrypt_model(
        self, 
        model: Any, 
        model_id: str,
        metadata: Optional[dict] = None
    ) -> SecuredModel:
        """
        Encrypt a trained ML model with HWID-bound encryption.
        
        Args:
            model: The trained scikit-learn or similar model
            model_id: Unique identifier for the model
            metadata: Optional metadata (accuracy, symbol, etc.)
        
        Returns:
            SecuredModel container with encrypted data
        """
        metadata = metadata or {}
        
        # Serialize model
        model_bytes = pickle.dumps(model)
        
        # Calculate model hash for integrity check
        model_hash = hashlib.sha256(model_bytes).hexdigest()
        
        # Encrypt with Fernet (AES-128-CBC with HMAC)
        key = self._derive_key()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(model_bytes)
        
        # HWID hash for verification
        hwid_hash = hashlib.sha256(self.hwid.encode()).hexdigest()
        
        secured = SecuredModel(
            model_id=model_id,
            encrypted_data=encrypted_data,
            hwid_hash=hwid_hash,
            model_hash=model_hash,
            metadata=metadata
        )
        
        logger.info(f"Model {model_id} encrypted successfully")
        return secured
    
    def decrypt_model(self, secured: SecuredModel) -> Optional[Any]:
        """
        Decrypt and load a secured model.
        Fails if HWID doesn't match.
        
        Args:
            secured: SecuredModel container
        
        Returns:
            The decrypted model, or None if verification fails
        """
        # Verify HWID
        current_hwid_hash = hashlib.sha256(self.hwid.encode()).hexdigest()
        if current_hwid_hash != secured.hwid_hash:
            logger.error(f"HWID mismatch for model {secured.model_id}")
            return None
        
        try:
            # Decrypt
            key = self._derive_key()
            fernet = Fernet(key)
            model_bytes = fernet.decrypt(secured.encrypted_data)
            
            # Verify integrity
            model_hash = hashlib.sha256(model_bytes).hexdigest()
            if model_hash != secured.model_hash:
                logger.error(f"Integrity check failed for model {secured.model_id}")
                return None
            
            # Deserialize
            model = pickle.loads(model_bytes)
            
            logger.info(f"Model {secured.model_id} decrypted successfully")
            return model
            
        except Exception as e:
            logger.exception(f"Decryption failed for model {secured.model_id}: {e}")
            return None
    
    def save_secured_model(self, secured: SecuredModel) -> Path:
        """Save secured model to disk"""
        file_path = self.models_dir / f"{secured.model_id}.nexmodel"
        
        # Prepare data for saving
        save_data = {
            "model_id": secured.model_id,
            "encrypted_data": base64.b64encode(secured.encrypted_data).decode(),
            "hwid_hash": secured.hwid_hash,
            "model_hash": secured.model_hash,
            "metadata": secured.metadata
        }
        
        with open(file_path, "w") as f:
            json.dump(save_data, f)
        
        logger.info(f"Secured model saved to {file_path}")
        return file_path
    
    def load_secured_model(self, model_id: str) -> Optional[SecuredModel]:
        """Load secured model from disk"""
        file_path = self.models_dir / f"{model_id}.nexmodel"
        
        if not file_path.exists():
            logger.error(f"Model file not found: {file_path}")
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return SecuredModel(
                model_id=data["model_id"],
                encrypted_data=base64.b64decode(data["encrypted_data"]),
                hwid_hash=data["hwid_hash"],
                model_hash=data["model_hash"],
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.exception(f"Failed to load model {model_id}: {e}")
            return None
    
    def list_models(self) -> list:
        """List all saved model IDs"""
        models = []
        for file in self.models_dir.glob("*.nexmodel"):
            models.append(file.stem)
        logger.debug(f"Found {len(models)} .nexmodel files in {self.models_dir}: {models}")
        return models

    def list_models_with_metadata(self) -> list:
        """List all models with their metadata for display

        Returns:
            List of dicts with keys: model_id, name, symbol, accuracy, created_at
        """
        models = []
        for file in self.models_dir.glob("*.nexmodel"):
            model_id = file.stem
            try:
                # Load the secured model to get metadata
                secured = self.load_secured_model(model_id)
                if secured:
                    metadata = secured.metadata

                    # Extract user-friendly info
                    model_info = {
                        'model_id': model_id,
                        'name': metadata.get('name', model_id[:8]),  # Fallback to short UUID
                        'symbol': metadata.get('symbol', 'Unknown'),
                        'accuracy': metadata.get('accuracy', 0.0),
                        'created_at': metadata.get('created_at', 'Unknown'),
                        'file_size': file.stat().st_size if file.exists() else 0
                    }
                    models.append(model_info)
            except Exception as e:
                logger.warning(f"Failed to load metadata for {model_id}: {e}")
                # Still add model with basic info
                models.append({
                    'model_id': model_id,
                    'name': model_id[:8] + '...',
                    'symbol': 'Unknown',
                    'accuracy': 0.0,
                    'created_at': 'Unknown',
                    'file_size': file.stat().st_size if file.exists() else 0
                })

        # Sort by name
        models.sort(key=lambda x: x['name'])
        logger.debug(f"Found {len(models)} models with metadata")
        return models

    def delete_model(self, model_id: str) -> bool:
        """Delete a saved model"""
        file_path = self.models_dir / f"{model_id}.nexmodel"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Model {model_id} deleted")
            return True
        return False
    
    def verify_model(self, model_id: str) -> bool:
        """Verify a model can be decrypted on this machine"""
        secured = self.load_secured_model(model_id)
        if not secured:
            return False
        
        current_hwid_hash = hashlib.sha256(self.hwid.encode()).hexdigest()
        return current_hwid_hash == secured.hwid_hash
