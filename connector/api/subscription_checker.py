"""
Subscription Checker Module
Verifies user subscription status from Supabase
"""

import hashlib
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import httpx
from supabase import create_client, Client
from loguru import logger

from core.config import SupabaseConfig


@dataclass
class SubscriptionStatus:
    """Subscription status data"""
    is_active: bool
    tier: str
    expires_at: Optional[str]
    features: list


class SubscriptionChecker:
    """Verifies subscription status from Supabase"""
    
    # Feature mapping per tier
    TIER_FEATURES = {
        "free": ["basic_trading", "limited_history"],
        "basic": ["basic_trading", "full_history", "llm_access", "backtest_10"],
        "pro": ["basic_trading", "full_history", "llm_access", "backtest_50", "auto_trading_5", "priority_support"],
        "enterprise": ["basic_trading", "full_history", "llm_access", "backtest_unlimited", "auto_trading_unlimited", "dedicated_support", "custom_models"]
    }
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.supabase: Optional[Client] = None
        self._cache: dict = {}
        self._cache_ttl = 300  # 5 minutes
        
        if config.url and config.anon_key:
            try:
                self.supabase = create_client(config.url, config.anon_key)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
    
    def _hash_key(self, api_key: str) -> str:
        """Hash API key for lookup"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def verify(self, api_key: str) -> SubscriptionStatus:
        """Verify subscription status from API key"""
        
        # Check cache first
        cache_key = self._hash_key(api_key)[:16]
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now().timestamp() - cached["timestamp"] < self._cache_ttl:
                return cached["status"]
        
        # Default to free tier if Supabase not configured
        if not self.supabase:
            return SubscriptionStatus(
                is_active=True,
                tier="free",
                expires_at=None,
                features=self.TIER_FEATURES["free"]
            )
        
        try:
            # Hash the API key for lookup
            key_hash = self._hash_key(api_key)
            
            # Verify API key and get user
            result = self.supabase.rpc(
                "verify_api_key",
                {"p_key_hash": key_hash}
            ).execute()
            
            if not result.data or not result.data[0].get("is_valid"):
                return SubscriptionStatus(
                    is_active=False,
                    tier="none",
                    expires_at=None,
                    features=[]
                )
            
            user_id = result.data[0]["user_id"]
            
            # Get subscription status
            sub_result = self.supabase.rpc(
                "check_subscription_status",
                {"p_user_id": user_id}
            ).execute()
            
            if sub_result.data:
                sub_data = sub_result.data[0]
                tier = sub_data.get("tier", "free")
                is_active = sub_data.get("is_active", False)
                expires_at = sub_data.get("expires_at")
                
                status = SubscriptionStatus(
                    is_active=is_active or tier == "free",
                    tier=tier,
                    expires_at=expires_at,
                    features=self.TIER_FEATURES.get(tier, self.TIER_FEATURES["free"])
                )
            else:
                status = SubscriptionStatus(
                    is_active=True,
                    tier="free",
                    expires_at=None,
                    features=self.TIER_FEATURES["free"]
                )
            
            # Cache result
            self._cache[cache_key] = {
                "timestamp": datetime.now().timestamp(),
                "status": status
            }
            
            return status
            
        except Exception as e:
            logger.exception(f"Subscription verification failed: {e}")
            # Return free tier on error to allow basic functionality
            return SubscriptionStatus(
                is_active=True,
                tier="free",
                expires_at=None,
                features=self.TIER_FEATURES["free"]
            )
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
    
    def get_tier_features(self, tier: str) -> list:
        """Get features for a specific tier"""
        return self.TIER_FEATURES.get(tier, self.TIER_FEATURES["free"])
