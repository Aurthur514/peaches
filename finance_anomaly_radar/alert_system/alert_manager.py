"""
Alert Manager for Finance Anomaly Radar
Handles multi-modal alerts with visual, audio, and notification capabilities.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from enum import Enum
from loguru import logger

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AlertType(Enum):
    SCAM_MESSAGE = "scam_message"
    MARKET_MANIPULATION = "market_manipulation"
    TRANSACTION_FRAUD = "transaction_fraud"
    SOCIAL_NETWORK_ANOMALY = "social_network_anomaly"

class AlertManager:
    """Manages all types of alerts and notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_history = []
        self.notification_channels = []
        self.sound_enabled = config.get('sound_enabled', True)
        self.visual_enabled = config.get('visual_enabled', True)
        
        # Initialize notification channels
        self._initialize_notification_channels()
    
    def _initialize_notification_channels(self):
        """Initialize available notification channels."""
        channels = self.config.get('notification_methods', [])
        
        for channel in channels:
            if channel == 'email':
                self.notification_channels.append(EmailNotifier(self.config.get('email', {})))
            elif channel == 'sms':
                self.notification_channels.append(SMSNotifier(self.config.get('sms', {})))
            elif channel == 'audio':
                self.notification_channels.append(AudioNotifier(self.config.get('audio', {})))
            elif channel == 'visual':
                self.notification_channels.append(VisualNotifier(self.config.get('visual', {})))
    
    async def send_alert(self, analysis_result: Dict[str, Any]) -> None:
        """Send alert based on analysis result.
        
        Args:
            analysis_result: Result from analysis engine
        """
        try:
            alert = self._create_alert(analysis_result)
            
            # Store in history
            self.alert_history.append(alert)
            
            # Keep only last 1000 alerts
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]
            
            # Send through all enabled channels
            tasks = []
            for channel in self.notification_channels:
                task = channel.send_notification(alert)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Alert sent: {alert['alert_type']} - {alert['risk_level']}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _create_alert(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized alert from analysis result."""
        risk_level = analysis_result.get('risk_level', 'LOW')
        
        alert_type = AlertType.SCAM_MESSAGE
        if 'manipulation_probability' in analysis_result:
            alert_type = AlertType.MARKET_MANIPULATION
        elif 'transaction_id' in analysis_result:
            alert_type = AlertType.TRANSACTION_FRAUD
        
        return {
            'alert_id': f"alert_{int(datetime.utcnow().timestamp())}",
            'timestamp': datetime.utcnow().isoformat(),
            'alert_type': alert_type.value,
            'risk_level': risk_level,
            'title': self._get_alert_title(alert_type, risk_level),
            'message': analysis_result.get('alert_message', 'Alert triggered'),
            'details': analysis_result,
            'color_code': self._get_color_code(risk_level),
            'sound_file': self._get_sound_file(risk_level),
            'urgency': self._get_urgency_level(risk_level)
        }
    
    def _get_alert_title(self, alert_type: AlertType, risk_level: str) -> str:
        """Generate alert title."""
        titles = {
            AlertType.SCAM_MESSAGE: {
                'HIGH': '🚨 URGENT: Scam Detected!',
                'MEDIUM': '⚠️ WARNING: Suspicious Content',
                'LOW': 'ℹ️ INFO: Low Risk Content'
            },
            AlertType.MARKET_MANIPULATION: {
                'HIGH': '🚨 MARKET ALERT: Manipulation Detected!',
                'MEDIUM': '⚠️ MARKET WARNING: Unusual Activity',
                'LOW': 'ℹ️ MARKET INFO: Minor Anomaly'
            },
            AlertType.TRANSACTION_FRAUD: {
                'HIGH': '🚨 URGENT: Transaction Fraud Risk!',
                'MEDIUM': '⚠️ WARNING: Suspicious Transaction',
                'LOW': 'ℹ️ INFO: Transaction Flagged'
            }
        }
        
        return titles.get(alert_type, {}).get(risk_level, 'Alert')
    
    def _get_color_code(self, risk_level: str) -> str:
        """Get color code for risk level."""
        colors = self.config.get('risk_levels', {})
        return colors.get(risk_level.lower(), {}).get('color', '#FFFFFF')
    
    def _get_sound_file(self, risk_level: str) -> str:
        """Get sound file for risk level."""
        sounds = self.config.get('risk_levels', {})
        return sounds.get(risk_level.lower(), {}).get('sound', 'default.wav')
    
    def _get_urgency_level(self, risk_level: str) -> str:
        """Get urgency level for notifications."""
        urgency_map = {
            'HIGH': 'urgent',
            'MEDIUM': 'normal', 
            'LOW': 'low'
        }
        return urgency_map.get(risk_level, 'normal')
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:] if self.alert_history else []
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        if not self.alert_history:
            return {
                'total_alerts': 0,
                'high_risk_alerts': 0,
                'medium_risk_alerts': 0,
                'low_risk_alerts': 0
            }
        
        total = len(self.alert_history)
        high_risk = sum(1 for alert in self.alert_history if alert['risk_level'] == 'HIGH')
        medium_risk = sum(1 for alert in self.alert_history if alert['risk_level'] == 'MEDIUM')
        low_risk = sum(1 for alert in self.alert_history if alert['risk_level'] == 'LOW')
        
        return {
            'total_alerts': total,
            'high_risk_alerts': high_risk,
            'medium_risk_alerts': medium_risk,
            'low_risk_alerts': low_risk,
            'high_risk_percentage': (high_risk / total) * 100 if total > 0 else 0
        }

class BaseNotifier:
    """Base class for notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
    
    async def send_notification(self, alert: Dict[str, Any]) -> bool:
        """Send notification through this channel.
        
        Args:
            alert: Alert to send
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            return await self._send_impl(alert)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return False
    
    async def _send_impl(self, alert: Dict[str, Any]) -> bool:
        """Implementation specific sending logic."""
        raise NotImplementedError

class AudioNotifier(BaseNotifier):
    """Handles audio notifications."""
    
    async def _send_impl(self, alert: Dict[str, Any]) -> bool:
        """Play audio alert."""
        try:
            # Simulate audio notification
            sound_file = alert.get('sound_file', 'default.wav')
            logger.info(f"🔊 Playing audio alert: {sound_file}")
            
            # In production, you would use libraries like pygame or playsound
            # pygame.mixer.music.load(sound_file)
            # pygame.mixer.music.play()
            
            return True
        except Exception as e:
            logger.error(f"Audio notification failed: {e}")
            return False

class VisualNotifier(BaseNotifier):
    """Handles visual notifications."""
    
    async def _send_impl(self, alert: Dict[str, Any]) -> bool:
        """Show visual alert."""
        try:
            color = alert.get('color_code', '#FF0000')
            title = alert.get('title', 'Alert')
            message = alert.get('message', '')
            
            # Simulate visual notification
            logger.info(f"👁️ Visual Alert: {title}")
            logger.info(f"Color: {color}, Message: {message}")
            
            # In production, you would create actual visual notifications
            # using libraries like tkinter, PyQt, or web-based notifications
            
            return True
        except Exception as e:
            logger.error(f"Visual notification failed: {e}")
            return False

class EmailNotifier(BaseNotifier):
    """Handles email notifications."""
    
    async def _send_impl(self, alert: Dict[str, Any]) -> bool:
        """Send email alert."""
        try:
            to_email = self.config.get('recipient')
            if not to_email:
                return False
            
            subject = alert.get('title', 'Finance Anomaly Radar Alert')
            body = self._create_email_body(alert)
            
            # Simulate email sending
            logger.info(f"📧 Email sent to {to_email}: {subject}")
            
            # In production, you would use libraries like smtplib or sendgrid
            # send_email(to_email, subject, body)
            
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False
    
    def _create_email_body(self, alert: Dict[str, Any]) -> str:
        """Create email body from alert."""
        return f"""
        Finance Anomaly Radar Alert
        
        Alert Type: {alert.get('alert_type', 'Unknown')}
        Risk Level: {alert.get('risk_level', 'Unknown')}
        Timestamp: {alert.get('timestamp', 'Unknown')}
        
        Message: {alert.get('message', 'No message')}
        
        This is an automated alert from the Finance Anomaly Radar system.
        Please review the details and take appropriate action if necessary.
        """

class SMSNotifier(BaseNotifier):
    """Handles SMS notifications."""
    
    async def _send_impl(self, alert: Dict[str, Any]) -> bool:
        """Send SMS alert."""
        try:
            phone_number = self.config.get('phone_number')
            if not phone_number:
                return False
            
            message = f"FAR Alert: {alert.get('title', 'Alert')} - {alert.get('message', '')}"[:160]  # SMS limit
            
            # Simulate SMS sending
            logger.info(f"📱 SMS sent to {phone_number}: {message}")
            
            # In production, you would use services like Twilio
            # send_sms(phone_number, message)
            
            return True
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            return False