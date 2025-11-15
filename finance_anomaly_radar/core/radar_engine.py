"""
Radar Engine - Core Intelligence Hub for Finance Anomaly Radar
Coordinates all AI detection engines and provides unified analysis.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from .config_manager import ConfigManager
from ..ai_engines.nlp_detector import NLPScamDetector
from ..ai_engines.market_detector import MarketManipulationDetector
from ..alert_system.alert_manager import AlertManager

class RadarEngine:
    """Core engine that coordinates all detection systems."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.nlp_detector = None
        self.market_detector = None
        self.alert_manager = None
        self.is_initialized = False
        
        # Analysis statistics
        self.stats = {
            'messages_analyzed': 0,
            'scams_detected': 0,
            'market_anomalies_detected': 0,
            'alerts_sent': 0,
            'last_analysis': None
        }
    
    async def initialize(self):
        """Initialize all detection engines."""
        try:
            logger.info("Initializing Radar Engine...")
            
            # Initialize NLP detector
            nlp_config = self.config_manager.get('ai_engines.nlp_detector', {})
            self.nlp_detector = NLPScamDetector(nlp_config)
            
            # Initialize market detector
            market_config = self.config_manager.get('ai_engines.market_detector', {})
            self.market_detector = MarketManipulationDetector(market_config)
            
            # Initialize alert manager
            alert_config = self.config_manager.get('alerts', {})
            self.alert_manager = AlertManager(alert_config)
            
            self.is_initialized = True
            logger.success("Radar Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Radar Engine: {e}")
            raise
    
    async def analyze_message(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze a message for scam indicators.
        
        Args:
            text: Message text to analyze
            context: Additional context (sender, platform, etc.)
            
        Returns:
            Analysis results with risk assessment
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Analyze with NLP detector
            nlp_result = await self.nlp_detector.analyze_text(text, context)
            
            # Create comprehensive result
            result = {
                'analysis_id': f"msg_{int(datetime.utcnow().timestamp())}",
                'timestamp': datetime.utcnow().isoformat(),
                'text_preview': text[:100] + "..." if len(text) > 100 else text,
                'risk_level': nlp_result.get('risk_level', 'LOW'),
                'scam_probability': nlp_result.get('scam_probability', 0.0),
                'confidence': nlp_result.get('confidence', 0.0),
                'indicators': nlp_result.get('indicators', {}),
                'model_predictions': nlp_result.get('model_predictions', {}),
                'alert_message': self._generate_alert_message(nlp_result)
            }
            
            # Send alert if high risk
            if result['risk_level'] == 'HIGH':
                await self._send_alert(result)
                self.stats['scams_detected'] += 1
            
            # Update statistics
            self.stats['messages_analyzed'] += 1
            self.stats['last_analysis'] = result['timestamp']
            
            logger.info(f"Message analyzed: Risk={result['risk_level']}, Probability={result['scam_probability']:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return {
                'error': str(e),
                'risk_level': 'UNKNOWN',
                'scam_probability': 0.5,
                'confidence': 0.0
            }
    
    async def analyze_market_data(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market data for manipulation patterns.
        
        Args:
            market_data: List of market data points
            
        Returns:
            Market analysis results
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Analyze with market detector
            market_result = await self.market_detector.analyze_market_data(market_data)
            
            # Create comprehensive result
            result = {
                'analysis_id': f"market_{int(datetime.utcnow().timestamp())}",
                'timestamp': datetime.utcnow().isoformat(),
                'data_points': len(market_data),
                'manipulation_probability': market_result.get('manipulation_probability', 0.0),
                'risk_level': market_result.get('risk_level', 'LOW'),
                'detected_patterns': market_result.get('detected_patterns', []),
                'recommendation': market_result.get('recommendation', 'NORMAL'),
                'statistical_indicators': market_result.get('statistical_indicators', {}),
                'alert_message': self._generate_market_alert_message(market_result)
            }
            
            # Send alert if high risk
            if result['risk_level'] == 'HIGH':
                await self._send_alert(result)
                self.stats['market_anomalies_detected'] += 1
            
            logger.info(f"Market analyzed: Risk={result['risk_level']}, Manipulation={result['manipulation_probability']:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing market data: {e}")
            return {
                'error': str(e),
                'risk_level': 'UNKNOWN',
                'manipulation_probability': 0.5,
                'recommendation': 'UNKNOWN'
            }
    
    async def process_data_batch(self, data_batch: List[Dict[str, Any]]):
        """Process a batch of collected data.
        
        Args:
            data_batch: Batch of data from various collectors
        """
        try:
            for data_item in data_batch:
                collector_source = data_item.get('collector_source')
                
                if collector_source == 'message':
                    # Process message data
                    text = data_item.get('text', '')
                    if text:
                        await self.analyze_message(text, data_item)
                
                elif collector_source == 'market':
                    # Collect market data for batch analysis
                    # In production, you'd batch these and analyze periodically
                    pass
                
                elif collector_source == 'transaction':
                    # Process transaction data
                    # Would implement transaction analysis here
                    pass
                
                elif collector_source == 'social':
                    # Process social media data
                    # Would implement social graph analysis here
                    pass
        
        except Exception as e:
            logger.error(f"Error processing data batch: {e}")
    
    def _generate_alert_message(self, analysis_result: Dict[str, Any]) -> str:
        """Generate alert message for scam detection."""
        risk_level = analysis_result.get('risk_level', 'LOW')
        probability = analysis_result.get('scam_probability', 0.0)
        
        if risk_level == 'HIGH':
            return f"🚨 HIGH RISK: Potential scam detected! ({probability:.0%} probability)"
        elif risk_level == 'MEDIUM':
            return f"⚠️ MEDIUM RISK: Suspicious content detected ({probability:.0%} probability)"
        else:
            return f"✅ LOW RISK: Content appears safe ({probability:.0%} probability)"
    
    def _generate_market_alert_message(self, analysis_result: Dict[str, Any]) -> str:
        """Generate alert message for market manipulation detection."""
        risk_level = analysis_result.get('risk_level', 'LOW')
        probability = analysis_result.get('manipulation_probability', 0.0)
        recommendation = analysis_result.get('recommendation', 'NORMAL')
        
        if risk_level == 'HIGH':
            return f"🚨 MARKET ALERT: Potential manipulation detected! ({probability:.0%} probability) - {recommendation}"
        elif risk_level == 'MEDIUM':
            return f"⚠️ MARKET CAUTION: Unusual activity detected ({probability:.0%} probability) - {recommendation}"
        else:
            return f"✅ MARKET NORMAL: No significant anomalies ({probability:.0%} probability)"
    
    async def _send_alert(self, analysis_result: Dict[str, Any]):
        """Send alert through alert manager."""
        try:
            if self.alert_manager:
                await self.alert_manager.send_alert(analysis_result)
                self.stats['alerts_sent'] += 1
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def shutdown(self):
        """Shutdown the radar engine."""
        logger.info("Shutting down Radar Engine...")
        self.is_initialized = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the radar engine."""
        return {
            'initialized': self.is_initialized,
            'statistics': self.stats.copy(),
            'components': {
                'nlp_detector': self.nlp_detector is not None,
                'market_detector': self.market_detector is not None,
                'alert_manager': self.alert_manager is not None
            }
        }