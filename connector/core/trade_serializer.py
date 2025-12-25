"""
Trade Serializer Module
Handles trade data serialization/deserialization with numeric precision preservation.
"""

import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from dataclasses import asdict

from core.mt5_client import Trade


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal and datetime types."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class TradeSerializer:
    """
    Handles trade data serialization/deserialization.
    Preserves numeric precision for prices and volumes using Decimal.
    """
    
    # Fields that require Decimal precision
    DECIMAL_FIELDS = ['volume', 'open_price', 'close_price', 'profit', 'commission', 'swap']
    
    def serialize(self, trade: Trade) -> str:
        """
        Serialize a Trade object to JSON string.
        
        Args:
            trade: Trade object to serialize
            
        Returns:
            JSON string representation of the trade
        """
        data = asdict(trade)
        
        # Convert numeric fields to Decimal strings for precision
        for field in self.DECIMAL_FIELDS:
            if field in data and data[field] is not None:
                data[field] = str(Decimal(str(data[field])))
        
        # Convert datetime fields to ISO format
        if 'open_time' in data and data['open_time'] is not None:
            data['open_time'] = data['open_time'].isoformat()
        if 'close_time' in data and data['close_time'] is not None:
            data['close_time'] = data['close_time'].isoformat()
        
        return json.dumps(data, cls=DecimalEncoder)
    
    def deserialize(self, json_str: str) -> Trade:
        """
        Deserialize a JSON string to a Trade object.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            Trade object
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        data = json.loads(json_str)
        
        # Convert Decimal string fields back to float
        for field in self.DECIMAL_FIELDS:
            if field in data and data[field] is not None:
                data[field] = float(Decimal(data[field]))
        
        # Convert ISO datetime strings back to datetime objects
        if 'open_time' in data and data['open_time'] is not None:
            data['open_time'] = datetime.fromisoformat(data['open_time'])
        if 'close_time' in data and data['close_time'] is not None:
            data['close_time'] = datetime.fromisoformat(data['close_time'])
        
        return Trade(**data)
    
    def serialize_list(self, trades: List[Trade]) -> str:
        """
        Serialize a list of Trade objects to JSON string.
        
        Args:
            trades: List of Trade objects to serialize
            
        Returns:
            JSON string representation of the trade list
        """
        trade_dicts = []
        for trade in trades:
            data = asdict(trade)
            
            # Convert numeric fields to Decimal strings for precision
            for field in self.DECIMAL_FIELDS:
                if field in data and data[field] is not None:
                    data[field] = str(Decimal(str(data[field])))
            
            # Convert datetime fields to ISO format
            if 'open_time' in data and data['open_time'] is not None:
                data['open_time'] = data['open_time'].isoformat()
            if 'close_time' in data and data['close_time'] is not None:
                data['close_time'] = data['close_time'].isoformat()
            
            trade_dicts.append(data)
        
        return json.dumps(trade_dicts, cls=DecimalEncoder)
    
    def deserialize_list(self, json_str: str) -> List[Trade]:
        """
        Deserialize a JSON string to a list of Trade objects.
        
        Args:
            json_str: JSON string to deserialize
            
        Returns:
            List of Trade objects
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        data_list = json.loads(json_str)
        trades = []
        
        for data in data_list:
            # Convert Decimal string fields back to float
            for field in self.DECIMAL_FIELDS:
                if field in data and data[field] is not None:
                    data[field] = float(Decimal(data[field]))
            
            # Convert ISO datetime strings back to datetime objects
            if 'open_time' in data and data['open_time'] is not None:
                data['open_time'] = datetime.fromisoformat(data['open_time'])
            if 'close_time' in data and data['close_time'] is not None:
                data['close_time'] = datetime.fromisoformat(data['close_time'])
            
            trades.append(Trade(**data))
        
        return trades
    
    def pretty_print(self, trade: Trade) -> str:
        """
        Generate a pretty-printed JSON representation of a trade.
        
        Args:
            trade: Trade object to format
            
        Returns:
            Pretty-printed JSON string
        """
        data = asdict(trade)
        
        # Convert numeric fields to Decimal strings for precision
        for field in self.DECIMAL_FIELDS:
            if field in data and data[field] is not None:
                data[field] = str(Decimal(str(data[field])))
        
        # Convert datetime fields to ISO format
        if 'open_time' in data and data['open_time'] is not None:
            data['open_time'] = data['open_time'].isoformat()
        if 'close_time' in data and data['close_time'] is not None:
            data['close_time'] = data['close_time'].isoformat()
        
        return json.dumps(data, cls=DecimalEncoder, indent=2)
