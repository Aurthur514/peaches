"""
Data Collection Orchestrator for Finance Anomaly Radar
Coordinates and manages all data collection modules.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

from .message_collector import MessageCollector
from .market_collector import MarketDataCollector
from .transaction_collector import TransactionCollector
from .social_collector import SocialMediaCollector
from ..core.config_manager import ConfigManager

class DataOrchestrator:
    """Orchestrates data collection from multiple sources."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.collectors = {}
        self.is_running = False
        self.collection_tasks = []
        self.data_buffer = []
        self.data_handlers = []
        
        self._initialize_collectors()
    
    def _initialize_collectors(self) -> None:
        """Initialize all data collectors based on configuration."""
        try:
            # Get data collection config
            data_config = self.config_manager.get('data_collection', {})
            
            # Initialize message collector
            if data_config.get('enable_message_collection', True):
                message_config = data_config.get('message_collector', {})
                self.collectors['message'] = MessageCollector(message_config)
                logger.info("Message collector initialized")
            
            # Initialize market data collector
            if data_config.get('enable_market_collection', True):
                market_config = data_config.get('market_collector', {})
                self.collectors['market'] = MarketDataCollector(market_config)
                logger.info("Market data collector initialized")
            
            # Initialize transaction collector
            if data_config.get('enable_transaction_collection', True):
                transaction_config = data_config.get('transaction_collector', {})
                self.collectors['transaction'] = TransactionCollector(transaction_config)
                logger.info("Transaction collector initialized")
            
            # Initialize social media collector
            if data_config.get('enable_social_collection', True):
                social_config = data_config.get('social_collector', {})
                self.collectors['social'] = SocialMediaCollector(social_config)
                logger.info("Social media collector initialized")
        
        except Exception as e:
            logger.error(f"Error initializing collectors: {e}")
    
    async def start_collection(self) -> None:
        """Start data collection from all configured sources."""
        if self.is_running:
            logger.warning("Data collection is already running")
            return
        
        self.is_running = True
        logger.info("Starting data collection orchestrator")
        
        try:
            # Start each collector as a separate task
            for name, collector in self.collectors.items():
                task = asyncio.create_task(
                    self._run_collector_with_error_handling(name, collector)
                )
                self.collection_tasks.append(task)
            
            # Start data processing task
            processing_task = asyncio.create_task(self._process_collected_data())
            self.collection_tasks.append(processing_task)
            
            # Wait for all tasks
            await asyncio.gather(*self.collection_tasks, return_exceptions=True)
        
        except Exception as e:
            logger.error(f"Error in data collection orchestrator: {e}")
        finally:
            self.is_running = False
    
    async def _run_collector_with_error_handling(self, name: str, collector) -> None:
        """Run a collector with error handling and retry logic."""
        retry_count = 0
        max_retries = 3
        
        while self.is_running and retry_count < max_retries:
            try:
                logger.info(f"Starting {name} collector")
                
                # Set up data storage callback
                original_store_data = collector.store_data
                collector.store_data = lambda data: self._handle_collected_data(name, data)
                
                await collector.start_collection()
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in {name} collector (retry {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    await asyncio.sleep(30 * retry_count)  # Exponential backoff
                else:
                    logger.error(f"Max retries exceeded for {name} collector")
                    break
    
    async def _handle_collected_data(self, collector_name: str, data: List[Dict[str, Any]]) -> None:
        """Handle data collected from a specific collector.
        
        Args:
            collector_name: Name of the collector that provided the data
            data: Collected data
        """
        try:
            # Add metadata to each data item
            for item in data:
                item['collector_source'] = collector_name
                item['orchestrator_timestamp'] = datetime.utcnow().isoformat()
            
            # Add to buffer
            self.data_buffer.extend(data)
            
            logger.debug(f"Received {len(data)} items from {collector_name} collector")
        
        except Exception as e:
            logger.error(f"Error handling data from {collector_name}: {e}")
    
    async def _process_collected_data(self) -> None:
        """Process collected data and forward to registered handlers."""
        while self.is_running:
            try:
                if self.data_buffer:
                    # Process data in batches
                    batch_size = 100
                    current_batch = self.data_buffer[:batch_size]
                    self.data_buffer = self.data_buffer[batch_size:]
                    
                    # Forward to all registered handlers
                    for handler in self.data_handlers:
                        try:
                            await handler(current_batch)
                        except Exception as e:
                            logger.error(f"Error in data handler: {e}")
                    
                    logger.debug(f"Processed batch of {len(current_batch)} items")
                
                # Wait before next processing cycle
                await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Error in data processing: {e}")
                await asyncio.sleep(30)
    
    def register_data_handler(self, handler_func) -> None:
        """Register a function to handle collected data.
        
        Args:
            handler_func: Async function that accepts List[Dict[str, Any]]
        """
        self.data_handlers.append(handler_func)
        logger.info(f"Registered data handler: {handler_func.__name__}")
    
    def stop_collection(self) -> None:
        """Stop data collection."""
        logger.info("Stopping data collection orchestrator")
        self.is_running = False
        
        # Stop individual collectors
        for collector in self.collectors.values():
            collector.stop_collection()
        
        # Cancel all tasks
        for task in self.collection_tasks:
            task.cancel()
        
        self.collection_tasks.clear()
    
    def get_collector_status(self) -> Dict[str, Any]:
        """Get status of all collectors.
        
        Returns:
            Status information for each collector
        """
        status = {
            'orchestrator_running': self.is_running,
            'buffer_size': len(self.data_buffer),
            'registered_handlers': len(self.data_handlers),
            'collectors': {}
        }
        
        for name, collector in self.collectors.items():
            status['collectors'][name] = collector.get_status()
        
        return status
    
    async def collect_once(self, collector_names: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Collect data once from specified collectors.
        
        Args:
            collector_names: List of collector names to run, or None for all
            
        Returns:
            Dictionary mapping collector names to collected data
        """
        if collector_names is None:
            collector_names = list(self.collectors.keys())
        
        results = {}
        
        for name in collector_names:
            if name in self.collectors:
                try:
                    collector = self.collectors[name]
                    data = await collector.collect()
                    processed_data = collector.preprocess_data(data)
                    results[name] = processed_data
                    
                    logger.info(f"One-time collection from {name}: {len(processed_data)} items")
                
                except Exception as e:
                    logger.error(f"Error in one-time collection from {name}: {e}")
                    results[name] = []
        
        return results
    
    def get_data_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of collected data.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Data summary
        """
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        summary = {
            'time_range_hours': hours,
            'collectors': {},
            'total_items': len(self.data_buffer),
            'buffer_items': len(self.data_buffer)
        }
        
        # This would be enhanced in production to query the actual data store
        for name in self.collectors.keys():
            summary['collectors'][name] = {
                'items_collected': 0,  # Would be actual count from database
                'last_collection': None,  # Would be actual timestamp
                'status': 'active' if self.is_running else 'stopped'
            }
        
        return summary