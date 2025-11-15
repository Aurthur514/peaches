"""
Transaction Collector for Finance Anomaly Radar
Collects and analyzes transaction data for UPI fraud and payment anomaly detection.
"""

import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from geopy.distance import geodesic
import json
from loguru import logger

from .base_collector import BaseDataCollector

class TransactionCollector(BaseDataCollector):
    """Collects transaction data for fraud detection analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.transaction_cache = {}
        self.user_profiles = {}
        self.merchant_profiles = {}
        self.fraud_patterns = self._load_fraud_patterns()
        
    def _load_fraud_patterns(self) -> Dict[str, Any]:
        """Load known fraud patterns and rules."""
        return {
            'velocity_rules': {
                'max_transactions_per_hour': 20,
                'max_amount_per_hour': 100000,
                'max_unique_merchants_per_hour': 10
            },
            'amount_rules': {
                'suspicious_amounts': [1, 11, 101, 501, 1001],  # Common test amounts
                'large_amount_threshold': 50000,
                'micro_transaction_threshold': 10
            },
            'location_rules': {
                'max_distance_km': 100,  # Max distance between consecutive transactions
                'velocity_threshold_kmph': 500  # Impossible travel speed
            },
            'time_rules': {
                'unusual_hours': list(range(0, 6)),  # 12 AM to 6 AM
                'min_transaction_gap_seconds': 5
            }
        }
    
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect transaction data from various sources.
        
        Returns:
            List of transaction data
        """
        collected_transactions = []
        
        # Collect UPI transactions
        upi_transactions = await self._collect_upi_transactions()
        collected_transactions.extend(upi_transactions)
        
        # Collect bank transactions
        bank_transactions = await self._collect_bank_transactions()
        collected_transactions.extend(bank_transactions)
        
        # Collect card transactions
        card_transactions = await self._collect_card_transactions()
        collected_transactions.extend(card_transactions)
        
        # Collect cryptocurrency transactions
        crypto_transactions = await self._collect_crypto_transactions()
        collected_transactions.extend(crypto_transactions)
        
        return collected_transactions
    
    async def _collect_upi_transactions(self) -> List[Dict[str, Any]]:
        """Collect UPI transaction data.
        
        In production, this would integrate with UPI APIs or bank webhooks.
        For demo purposes, we'll generate realistic sample data.
        """
        sample_transactions = [
            {
                'transaction_id': 'UPI123456789012',
                'type': 'UPI',
                'amount': 1.00,  # Suspicious test amount
                'currency': 'INR',
                'sender_vpa': 'sender@paytm',
                'receiver_vpa': 'receiver@phonepe',
                'sender_account': self._hash_account('1234567890'),
                'receiver_account': self._hash_account('0987654321'),
                'merchant_id': 'MERCHANT001',
                'transaction_note': 'Testing payment system',
                'timestamp': datetime.utcnow().isoformat(),
                'location': {'lat': 28.6139, 'lon': 77.2090},  # Delhi
                'device_info': {
                    'device_id': 'device_123',
                    'app_version': '1.2.3',
                    'os': 'Android 12'
                },
                'status': 'SUCCESS'
            },
            {
                'transaction_id': 'UPI123456789013',
                'type': 'UPI',
                'amount': 75000.00,  # Large amount
                'currency': 'INR',
                'sender_vpa': 'user@paytm',
                'receiver_vpa': 'unknown@gpay',
                'sender_account': self._hash_account('1111111111'),
                'receiver_account': self._hash_account('2222222222'),
                'merchant_id': None,
                'transaction_note': 'Urgent payment needed',
                'timestamp': (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                'location': {'lat': 19.0760, 'lon': 72.8777},  # Mumbai
                'device_info': {
                    'device_id': 'device_456',
                    'app_version': '1.0.1',
                    'os': 'iOS 15'
                },
                'status': 'SUCCESS'
            }
        ]
        
        # Add fraud indicators to each transaction
        for transaction in sample_transactions:
            transaction['fraud_indicators'] = self._analyze_transaction_fraud_indicators(transaction)
        
        return sample_transactions
    
    async def _collect_bank_transactions(self) -> List[Dict[str, Any]]:
        """Collect bank transaction data."""
        # Would integrate with bank APIs in production
        return []
    
    async def _collect_card_transactions(self) -> List[Dict[str, Any]]:
        """Collect credit/debit card transaction data."""
        # Would integrate with card processor APIs in production
        return []
    
    async def _collect_crypto_transactions(self) -> List[Dict[str, Any]]:
        """Collect cryptocurrency transaction data."""
        # Would integrate with blockchain APIs in production
        return []
    
    def _hash_account(self, account_number: str) -> str:
        """Hash account number for privacy."""
        return hashlib.sha256(account_number.encode()).hexdigest()[:16]
    
    def _analyze_transaction_fraud_indicators(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction for fraud indicators.
        
        Args:
            transaction: Transaction data to analyze
            
        Returns:
            Dictionary of fraud indicators
        """
        indicators = {
            'velocity_anomalies': [],
            'amount_anomalies': [],
            'location_anomalies': [],
            'time_anomalies': [],
            'pattern_anomalies': [],
            'risk_score': 0.0
        }
        
        # Analyze velocity (frequency) anomalies
        velocity_issues = self._check_velocity_anomalies(transaction)
        indicators['velocity_anomalies'] = velocity_issues
        
        # Analyze amount anomalies
        amount_issues = self._check_amount_anomalies(transaction)
        indicators['amount_anomalies'] = amount_issues
        
        # Analyze location anomalies
        location_issues = self._check_location_anomalies(transaction)
        indicators['location_anomalies'] = location_issues
        
        # Analyze time anomalies
        time_issues = self._check_time_anomalies(transaction)
        indicators['time_anomalies'] = time_issues
        
        # Analyze pattern anomalies
        pattern_issues = self._check_pattern_anomalies(transaction)
        indicators['pattern_anomalies'] = pattern_issues
        
        # Calculate overall risk score
        indicators['risk_score'] = self._calculate_transaction_risk_score(indicators)
        
        return indicators
    
    def _check_velocity_anomalies(self, transaction: Dict[str, Any]) -> List[str]:
        """Check for transaction velocity anomalies."""
        anomalies = []
        user_account = transaction.get('sender_account')
        
        if not user_account:
            return anomalies
        
        # Get user's recent transactions from cache
        user_transactions = self.transaction_cache.get(user_account, [])
        current_time = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00'))
        
        # Check transactions in the last hour
        hour_ago = current_time - timedelta(hours=1)
        recent_transactions = [
            tx for tx in user_transactions 
            if datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00')) > hour_ago
        ]
        
        rules = self.fraud_patterns['velocity_rules']
        
        # Check transaction count
        if len(recent_transactions) > rules['max_transactions_per_hour']:
            anomalies.append('high_transaction_frequency')
        
        # Check total amount
        total_amount = sum([tx['amount'] for tx in recent_transactions]) + transaction['amount']
        if total_amount > rules['max_amount_per_hour']:
            anomalies.append('high_amount_velocity')
        
        # Check unique merchants
        unique_merchants = set([tx.get('merchant_id') for tx in recent_transactions if tx.get('merchant_id')])
        if transaction.get('merchant_id'):
            unique_merchants.add(transaction['merchant_id'])
        
        if len(unique_merchants) > rules['max_unique_merchants_per_hour']:
            anomalies.append('multiple_merchants')
        
        return anomalies
    
    def _check_amount_anomalies(self, transaction: Dict[str, Any]) -> List[str]:
        """Check for suspicious transaction amounts."""
        anomalies = []
        amount = transaction['amount']
        rules = self.fraud_patterns['amount_rules']
        
        # Check for suspicious test amounts
        if amount in rules['suspicious_amounts']:
            anomalies.append('suspicious_test_amount')
        
        # Check for large amounts
        if amount > rules['large_amount_threshold']:
            anomalies.append('large_amount')
        
        # Check for micro transactions (possible carding)
        if amount <= rules['micro_transaction_threshold']:
            anomalies.append('micro_transaction')
        
        # Check for round amounts (possible structured transactions)
        if amount % 1000 == 0 and amount > 10000:
            anomalies.append('round_amount')
        
        return anomalies
    
    def _check_location_anomalies(self, transaction: Dict[str, Any]) -> List[str]:
        """Check for location-based anomalies."""
        anomalies = []
        user_account = transaction.get('sender_account')
        current_location = transaction.get('location')
        
        if not user_account or not current_location:
            return anomalies
        
        user_transactions = self.transaction_cache.get(user_account, [])
        current_time = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00'))
        
        # Find the most recent transaction with location
        last_transaction = None
        for tx in reversed(user_transactions):
            if tx.get('location'):
                last_transaction = tx
                break
        
        if last_transaction:
            last_location = last_transaction['location']
            last_time = datetime.fromisoformat(last_transaction['timestamp'].replace('Z', '+00:00'))
            
            # Calculate distance and time difference
            distance_km = geodesic(
                (last_location['lat'], last_location['lon']),
                (current_location['lat'], current_location['lon'])
            ).kilometers
            
            time_diff_hours = (current_time - last_time).total_seconds() / 3600
            
            rules = self.fraud_patterns['location_rules']
            
            # Check impossible travel
            if time_diff_hours > 0:
                speed_kmph = distance_km / time_diff_hours
                if speed_kmph > rules['velocity_threshold_kmph']:
                    anomalies.append('impossible_travel')
            
            # Check large distance
            if distance_km > rules['max_distance_km'] and time_diff_hours < 1:
                anomalies.append('large_distance_movement')
        
        return anomalies
    
    def _check_time_anomalies(self, transaction: Dict[str, Any]) -> List[str]:
        """Check for time-based anomalies."""
        anomalies = []
        timestamp = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00'))
        rules = self.fraud_patterns['time_rules']
        
        # Check unusual hours
        if timestamp.hour in rules['unusual_hours']:
            anomalies.append('unusual_hour')
        
        # Check rapid successive transactions
        user_account = transaction.get('sender_account')
        if user_account:
            user_transactions = self.transaction_cache.get(user_account, [])
            if user_transactions:
                last_tx_time = datetime.fromisoformat(user_transactions[-1]['timestamp'].replace('Z', '+00:00'))
                time_diff = (timestamp - last_tx_time).total_seconds()
                
                if time_diff < rules['min_transaction_gap_seconds']:
                    anomalies.append('rapid_successive_transactions')
        
        return anomalies
    
    def _check_pattern_anomalies(self, transaction: Dict[str, Any]) -> List[str]:
        """Check for suspicious transaction patterns."""
        anomalies = []
        
        # Check transaction note for suspicious content
        note = transaction.get('transaction_note', '').lower()
        suspicious_keywords = [
            'test', 'testing', 'check', 'urgent', 'emergency', 
            'loan', 'investment', 'refund', 'cashback'
        ]
        
        for keyword in suspicious_keywords:
            if keyword in note:
                anomalies.append(f'suspicious_note_{keyword}')
                break
        
        # Check for P2P transactions to unknown accounts
        if not transaction.get('merchant_id'):
            # This is a P2P transaction
            receiver_account = transaction.get('receiver_account')
            sender_account = transaction.get('sender_account')
            
            # Check if this is a new recipient
            user_transactions = self.transaction_cache.get(sender_account, [])
            known_recipients = set([tx.get('receiver_account') for tx in user_transactions])
            
            if receiver_account not in known_recipients:
                anomalies.append('new_recipient')
        
        # Check device consistency
        device_id = transaction.get('device_info', {}).get('device_id')
        if device_id:
            user_account = transaction.get('sender_account')
            user_transactions = self.transaction_cache.get(user_account, [])
            
            if user_transactions:
                # Check if device ID is consistent
                recent_devices = set([
                    tx.get('device_info', {}).get('device_id') 
                    for tx in user_transactions[-5:]  # Last 5 transactions
                    if tx.get('device_info', {}).get('device_id')
                ])
                
                if device_id not in recent_devices and recent_devices:
                    anomalies.append('new_device')
        
        return anomalies
    
    def _calculate_transaction_risk_score(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall risk score for transaction."""
        score = 0.0
        
        # Weight different types of anomalies
        weights = {
            'velocity_anomalies': 0.3,
            'amount_anomalies': 0.25, 
            'location_anomalies': 0.2,
            'time_anomalies': 0.1,
            'pattern_anomalies': 0.15
        }
        
        for category, anomaly_list in indicators.items():
            if category in weights and isinstance(anomaly_list, list):
                # Each anomaly contributes to the score
                category_score = len(anomaly_list) * 0.2  # 0.2 per anomaly
                weighted_score = min(category_score, 1.0) * weights[category]
                score += weighted_score
        
        return min(score, 1.0)  # Cap at 1.0
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate transaction data.
        
        Args:
            data: Transaction data to validate
            
        Returns:
            True if data is valid
        """
        required_fields = ['transaction_id', 'type', 'amount', 'timestamp', 'status']
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate amount
        if not isinstance(data['amount'], (int, float)) or data['amount'] < 0:
            return False
        
        # Validate timestamp
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            return False
        
        return True
    
    async def store_data(self, data: List[Dict[str, Any]]) -> None:
        """Store transaction data and update cache.
        
        Args:
            data: Transaction data to store
        """
        for transaction in data:
            sender_account = transaction.get('sender_account')
            if sender_account:
                if sender_account not in self.transaction_cache:
                    self.transaction_cache[sender_account] = []
                
                self.transaction_cache[sender_account].append(transaction)
                
                # Keep only last 100 transactions per user
                if len(self.transaction_cache[sender_account]) > 100:
                    self.transaction_cache[sender_account] = self.transaction_cache[sender_account][-100:]
        
        await super().store_data(data)
    
    def get_collection_interval(self) -> int:
        """Get transaction collection interval."""
        return self.config.get('collection_interval', 30)  # Every 30 seconds
    
    def get_user_transaction_summary(self, account_hash: str, hours: int = 24) -> Dict[str, Any]:
        """Get transaction summary for a user.
        
        Args:
            account_hash: Hashed account identifier
            hours: Number of hours to look back
            
        Returns:
            Transaction summary
        """
        user_transactions = self.transaction_cache.get(account_hash, [])
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_transactions = [
            tx for tx in user_transactions
            if datetime.fromisoformat(tx['timestamp'].replace('Z', '+00:00')) > cutoff_time
        ]
        
        return {
            'total_transactions': len(recent_transactions),
            'total_amount': sum([tx['amount'] for tx in recent_transactions]),
            'unique_merchants': len(set([tx.get('merchant_id') for tx in recent_transactions if tx.get('merchant_id')])),
            'avg_risk_score': sum([tx.get('fraud_indicators', {}).get('risk_score', 0) for tx in recent_transactions]) / len(recent_transactions) if recent_transactions else 0,
            'high_risk_transactions': len([tx for tx in recent_transactions if tx.get('fraud_indicators', {}).get('risk_score', 0) > 0.7])
        }