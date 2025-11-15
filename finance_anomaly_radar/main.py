"""
Finance Anomaly Radar (FAR) - Main Application
A Real-Time Early-Warning Radar for Detecting Financial Fraud, Scams & Market Manipulation
"""

import asyncio
import sys
import signal
from pathlib import Path
from loguru import logger
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config_manager import ConfigManager
from core.radar_engine import RadarEngine
from data_collection.data_orchestrator import DataOrchestrator
from api.main import create_app
from dashboard.app import create_dashboard
import uvicorn
import streamlit.web.cli as stcli

class FinanceAnomalyRadar:
    """Main application class for Finance Anomaly Radar."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.radar_engine = None
        self.data_orchestrator = None
        self.api_server = None
        self.dashboard_server = None
        self.is_running = False
        
        # Set up logging
        self._setup_logging()
        
        logger.info("Finance Anomaly Radar initialized")
        logger.info("🛡️ Protecting finances with AI-powered detection")
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = self.config_manager.get('app.log_level', 'INFO')
        
        logger.remove()  # Remove default handler
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )
        
        # Add file logging
        logger.add(
            "logs/far_{time:YYYY-MM-DD}.log",
            level=log_level,
            rotation="1 day",
            retention="30 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
        )
    
    async def initialize(self):
        """Initialize all system components."""
        try:
            logger.info("Initializing Finance Anomaly Radar components...")
            
            # Initialize radar engine
            self.radar_engine = RadarEngine(self.config_manager)
            await self.radar_engine.initialize()
            
            # Initialize data orchestrator
            self.data_orchestrator = DataOrchestrator(self.config_manager)
            
            # Register data handler with radar engine
            self.data_orchestrator.register_data_handler(
                self.radar_engine.process_data_batch
            )
            
            logger.success("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            raise
    
    async def start(self):
        """Start the Finance Anomaly Radar system."""
        if self.is_running:
            logger.warning("System is already running")
            return
        
        try:
            await self.initialize()
            
            self.is_running = True
            logger.info("🚀 Starting Finance Anomaly Radar System")
            
            # Start data collection
            data_collection_task = asyncio.create_task(
                self.data_orchestrator.start_collection()
            )
            
            # Start API server
            api_task = asyncio.create_task(self._start_api_server())
            
            # Start dashboard (in a separate process)
            dashboard_task = asyncio.create_task(self._start_dashboard())
            
            logger.success("🛡️ Finance Anomaly Radar is now active!")
            logger.info("🌐 API Server: http://localhost:8000")
            logger.info("📊 Dashboard: http://localhost:8501")
            logger.info("📚 API Documentation: http://localhost:8000/docs")
            
            # Wait for tasks
            await asyncio.gather(
                data_collection_task,
                api_task,
                dashboard_task,
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            await self.stop()
            raise
    
    async def _start_api_server(self):
        """Start the FastAPI server."""
        try:
            app = create_app(self.radar_engine)
            api_config = self.config_manager.get_api_config()
            
            config = uvicorn.Config(
                app,
                host=api_config.get('host', '0.0.0.0'),
                port=api_config.get('port', 8000),
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Error starting API server: {e}")
    
    async def _start_dashboard(self):
        """Start the Streamlit dashboard."""
        try:
            # This would typically be run in a separate process
            # For now, we'll just log that it should be started manually
            logger.info("To start the dashboard, run: streamlit run dashboard/app.py")
            
            # Keep this task alive
            while self.is_running:
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error(f"Error with dashboard: {e}")
    
    async def stop(self):
        """Stop the Finance Anomaly Radar system."""
        logger.info("🛑 Stopping Finance Anomaly Radar System...")
        
        self.is_running = False
        
        try:
            if self.data_orchestrator:
                self.data_orchestrator.stop_collection()
            
            if self.radar_engine:
                await self.radar_engine.shutdown()
            
            logger.success("System stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    async def demo_analysis(self):
        """Run a demonstration analysis."""
        logger.info("🎯 Running Finance Anomaly Radar Demo Analysis")
        
        try:
            # Sample suspicious message
            sample_message = """
            🚀 URGENT: New crypto signal! 
            
            Guaranteed 1000% profits in 24 hours! 
            
            Join our exclusive WhatsApp group NOW! 
            Limited spots available - only for first 50 people!
            
            Send ₹5000 to activate your VIP membership.
            
            Don't miss this life-changing opportunity!
            """
            
            logger.info("Analyzing suspicious message...")
            result = await self.radar_engine.analyze_message(sample_message)
            
            print("\n" + "="*60)
            print("🛡️  FINANCE ANOMALY RADAR - ANALYSIS RESULT")
            print("="*60)
            print(f"📝 Message: {sample_message.strip()[:100]}...")
            print(f"⚠️  Risk Level: {result['risk_level']}")
            print(f"📊 Scam Probability: {result['scam_probability']:.2%}")
            print(f"🎯 Confidence: {result['confidence']:.2%}")
            print(f"🚨 Alert: {result.get('alert_message', 'N/A')}")
            
            if result.get('indicators', {}).get('pattern_matches'):
                print("\n🔍 Detected Patterns:")
                for pattern in result['indicators']['pattern_matches'][:3]:
                    print(f"  • {pattern['category']}: {pattern['pattern']}")
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error in demo analysis: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        status = {
            'system_running': self.is_running,
            'timestamp': asyncio.get_event_loop().time(),
            'components': {}
        }
        
        if self.radar_engine:
            status['components']['radar_engine'] = self.radar_engine.get_status()
        
        if self.data_orchestrator:
            status['components']['data_orchestrator'] = self.data_orchestrator.get_collector_status()
        
        return status

def setup_signal_handlers(app):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(app.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point."""
    try:
        app = FinanceAnomalyRadar()
        setup_signal_handlers(app)
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == 'demo':
                await app.initialize()
                await app.demo_analysis()
                return
            
            elif command == 'status':
                # Quick status check
                status = app.get_system_status()
                print(f"System Status: {'Running' if status['system_running'] else 'Stopped'}")
                return
            
            elif command == 'dashboard':
                # Start only dashboard
                logger.info("Starting dashboard only...")
                import subprocess
                subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])
                return
        
        # Default: start full system
        await app.start()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Run the application
    asyncio.run(main())