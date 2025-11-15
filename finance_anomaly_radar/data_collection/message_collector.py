"""
Message Collector for Finance Anomaly Radar
Collects and processes messages from various sources (WhatsApp, SMS, social media).
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import aiohttp
from loguru import logger

from .base_collector import BaseDataCollector

class MessageCollector(BaseDataCollector):
    """Collects messages from various communication platforms."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.supported_sources = ['whatsapp', 'telegram', 'sms', 'email']
        self.scam_keywords = self._load_scam_keywords()
        
    def _load_scam_keywords(self) -> List[str]:
        """Load known scam keywords and patterns."""
        return [
            'guaranteed returns', 'risk-free investment', 'exclusive opportunity',
            'limited time offer', 'double your money', 'get rich quick',
            'secret method', 'insider information', 'cryptocurrency mining',
            'binary options', 'forex trading signals', 'penny stocks',
            'investment group', 'telegram group', 'whatsapp group',
            'send money now', 'urgent transfer', 'verify account',
            'click this link', 'download app', 'install apk'
        ]
    
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect messages from configured sources.
        
        Returns:
            List of collected message data
        """
        collected_messages = []
        
        # Collect from each configured source
        for source in self.config.get('sources', []):
            try:
                if source == 'whatsapp':
                    messages = await self._collect_whatsapp_messages()
                elif source == 'telegram':
                    messages = await self._collect_telegram_messages()
                elif source == 'sms':
                    messages = await self._collect_sms_messages()
                elif source == 'email':
                    messages = await self._collect_email_messages()
                else:
                    logger.warning(f"Unsupported message source: {source}")
                    continue
                
                # Add source metadata
                for msg in messages:
                    msg['source'] = source
                    msg['risk_indicators'] = self._extract_risk_indicators(msg['text'])
                
                collected_messages.extend(messages)
                
            except Exception as e:
                logger.error(f"Error collecting from {source}: {e}")
        
        return collected_messages
    
    async def _collect_whatsapp_messages(self) -> List[Dict[str, Any]]:
        """Collect messages from WhatsApp (simulated for demo).
        
        In production, this would integrate with WhatsApp Business API
        or use phone monitoring with proper permissions.
        """
        # Simulated WhatsApp messages for demonstration
        sample_messages = [
            {
                'text': 'Join our exclusive investment group! Guaranteed 500% returns in 30 days!',
                'sender': '+1234567890',
                'timestamp': datetime.utcnow().isoformat(),
                'group_id': 'investment_group_123',
                'message_id': 'wa_msg_001'
            },
            {
                'text': 'Limited time crypto opportunity! Only 10 spots left. Send ₹50,000 now!',
                'sender': '+0987654321', 
                'timestamp': datetime.utcnow().isoformat(),
                'group_id': 'crypto_signals_456',
                'message_id': 'wa_msg_002'
            }
        ]
        
        return sample_messages
    
    async def _collect_telegram_messages(self) -> List[Dict[str, Any]]:
        """Collect messages from Telegram channels/groups."""
        messages = []
        
        try:
            telegram_token = self.config.get('telegram_bot_token')
            if not telegram_token:
                logger.warning("Telegram bot token not configured")
                return messages
            
            # Use Telegram Bot API to get messages
            # This is a simplified implementation
            url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for update in data.get('result', []):
                            if 'message' in update:
                                msg = update['message']
                                messages.append({
                                    'text': msg.get('text', ''),
                                    'sender': msg.get('from', {}).get('username', ''),
                                    'timestamp': datetime.fromtimestamp(msg.get('date', 0)).isoformat(),
                                    'chat_id': msg.get('chat', {}).get('id'),
                                    'message_id': f"tg_msg_{msg.get('message_id')}"
                                })
        
        except Exception as e:
            logger.error(f"Error collecting Telegram messages: {e}")
        
        return messages
    
    async def _collect_sms_messages(self) -> List[Dict[str, Any]]:
        """Collect SMS messages (requires phone integration)."""
        # In production, this would integrate with SMS APIs or phone monitoring
        sample_sms = [
            {
                'text': 'Your account will be blocked! Click here to verify: http://fake-bank.com',
                'sender': 'BANK-ALERT',
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': 'sms_msg_001'
            }
        ]
        
        return sample_sms
    
    async def _collect_email_messages(self) -> List[Dict[str, Any]]:
        """Collect emails from configured accounts."""
        # Would integrate with email APIs (Gmail, Outlook, etc.)
        return []
    
    def _extract_risk_indicators(self, text: str) -> Dict[str, Any]:
        """Extract risk indicators from message text.
        
        Args:
            text: Message text to analyze
            
        Returns:
            Dictionary of risk indicators
        """
        indicators = {
            'scam_keywords': [],
            'suspicious_urls': [],
            'phone_numbers': [],
            'financial_amounts': [],
            'urgency_words': [],
            'has_group_invite': False,
            'has_download_link': False
        }
        
        text_lower = text.lower()
        
        # Check for scam keywords
        for keyword in self.scam_keywords:
            if keyword in text_lower:
                indicators['scam_keywords'].append(keyword)
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        indicators['suspicious_urls'] = urls
        
        # Extract phone numbers
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        phones = re.findall(phone_pattern, text)
        indicators['phone_numbers'] = phones
        
        # Extract financial amounts
        amount_pattern = r'[₹$€£][\d,]+|[\d,]+\s*(?:rupees?|dollars?|euros?|pounds?)'
        amounts = re.findall(amount_pattern, text, re.IGNORECASE)
        indicators['financial_amounts'] = amounts
        
        # Check for urgency words
        urgency_words = ['urgent', 'immediately', 'act now', 'limited time', 'expires today', 'last chance']
        for word in urgency_words:
            if word in text_lower:
                indicators['urgency_words'].append(word)
        
        # Check for group invites
        group_patterns = ['join group', 'telegram group', 'whatsapp group', 'investment group']
        indicators['has_group_invite'] = any(pattern in text_lower for pattern in group_patterns)
        
        # Check for download links
        download_patterns = ['download app', 'install apk', 'download link', 'click to install']
        indicators['has_download_link'] = any(pattern in text_lower for pattern in download_patterns)
        
        return indicators
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate message data.
        
        Args:
            data: Message data to validate
            
        Returns:
            True if data is valid
        """
        required_fields = ['text', 'sender', 'timestamp', 'message_id']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # Check text length
        if len(data['text']) < 5 or len(data['text']) > 10000:
            return False
        
        return True
    
    def get_collection_interval(self) -> int:
        """Get message collection interval."""
        return self.config.get('collection_interval', 30)  # Check every 30 seconds
    
    def calculate_message_risk_score(self, message: Dict[str, Any]) -> float:
        """Calculate preliminary risk score for a message.
        
        Args:
            message: Message data with risk indicators
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        score = 0.0
        indicators = message.get('risk_indicators', {})
        
        # Scam keywords (0.4 max)
        scam_keywords = indicators.get('scam_keywords', [])
        score += min(len(scam_keywords) * 0.1, 0.4)
        
        # Suspicious URLs (0.2 max)
        urls = indicators.get('suspicious_urls', [])
        score += min(len(urls) * 0.1, 0.2)
        
        # Financial amounts (0.1)
        if indicators.get('financial_amounts'):
            score += 0.1
        
        # Urgency words (0.15)
        urgency_words = indicators.get('urgency_words', [])
        score += min(len(urgency_words) * 0.05, 0.15)
        
        # Group invite (0.1)
        if indicators.get('has_group_invite'):
            score += 0.1
        
        # Download links (0.05)
        if indicators.get('has_download_link'):
            score += 0.05
        
        return min(score, 1.0)