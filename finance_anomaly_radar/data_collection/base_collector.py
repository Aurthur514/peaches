"""
Base Data Collector Interface
Defines the common interface for all data collection modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
from loguru import logger

class BaseDataCollector(ABC):
    """Abstract base class for all data collectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_active = False
        self.last_collection_time = None
        
    @abstractmethod
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data from the source.
        
        Returns:
            List of collected data items
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate collected data.
        
        Args:
            data: Data item to validate
            
        Returns:
            True if data is valid
        """
        pass
    
    def preprocess_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocess collected data.
        
        Args:
            data: Raw collected data
            
        Returns:
            Preprocessed data
        """
        processed = []
        
        for item in data:
            if self.validate_data(item):
                # Add metadata
                item['collection_time'] = datetime.utcnow().isoformat()
                item['collector_type'] = self.__class__.__name__
                
                processed.append(item)
            else:
                logger.warning(f"Invalid data item discarded: {item}")
        
        return processed
    
    async def start_collection(self) -> None:
        """Start continuous data collection."""
        self.is_active = True
        logger.info(f"Started {self.__class__.__name__}")
        
        while self.is_active:
            try:
                data = await self.collect()
                processed_data = self.preprocess_data(data)
                
                if processed_data:
                    await self.store_data(processed_data)
                    self.last_collection_time = datetime.utcnow()
                
                # Wait before next collection
                await asyncio.sleep(self.get_collection_interval())
                
            except Exception as e:
                logger.error(f"Error in {self.__class__.__name__}: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def stop_collection(self) -> None:
        """Stop data collection."""
        self.is_active = False
        logger.info(f"Stopped {self.__class__.__name__}")
    
    async def store_data(self, data: List[Dict[str, Any]]) -> None:
        """Store collected data.
        
        Args:
            data: Processed data to store
        """
        # This should be implemented by subclasses or injected
        logger.debug(f"Storing {len(data)} items from {self.__class__.__name__}")
    
    def get_collection_interval(self) -> int:
        """Get collection interval in seconds.
        
        Returns:
            Collection interval
        """
        return self.config.get('collection_interval', 60)
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status.
        
        Returns:
            Status information
        """
        return {
            'collector_type': self.__class__.__name__,
            'is_active': self.is_active,
            'last_collection': self.last_collection_time.isoformat() if self.last_collection_time else None,
            'config': self.config
        }