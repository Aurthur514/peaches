#!/usr/bin/env python3
"""
Trading Bot Health Check and Monitoring Module
Provides endpoints for cloud health checks and notifications
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import sqlite3

def setup_cloud_logging():
    """Configure logging for cloud environments"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configure structured logging for cloud
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add cloud-specific structured logging
    if os.getenv('ENABLE_CLOUD_LOGGING', '').lower() == 'true':
        try:
            import google.cloud.logging
            client = google.cloud.logging.Client()
            handler = client.get_default_handler()
            logging.getLogger().addHandler(handler)
        except ImportError:
            logging.warning("Google Cloud Logging not available")

def send_notification(message: str, webhook_url: Optional[str] = None) -> bool:
    """Send notification to webhook (Slack, Discord, etc.)"""
    webhook_url = webhook_url or os.getenv('WEBHOOK_URL')
    if not webhook_url:
        return False
    
    try:
        payload = {
            "text": f"🤖 Trading Bot Alert: {message}",
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")
        return False

def get_health_status() -> Dict[str, Any]:
    """Get comprehensive health status"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check database connectivity
    try:
        conn = sqlite3.connect('futures_trades.db', timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        conn.close()
        
        health["checks"]["database"] = {
            "status": "ok",
            "trade_count": trade_count
        }
    except Exception as e:
        health["checks"]["database"] = {
            "status": "error", 
            "error": str(e)
        }
        health["status"] = "unhealthy"
    
    # Check learning database
    try:
        conn = sqlite3.connect('bot_learning.db', timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM strategy_performance")
        learning_records = cursor.fetchone()[0]
        conn.close()
        
        health["checks"]["learning_db"] = {
            "status": "ok",
            "learning_records": learning_records
        }
    except Exception as e:
        health["checks"]["learning_db"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check API credentials
    api_key = os.getenv('CS_API_KEY')
    api_secret = os.getenv('CS_API_SECRET_HEX')
    
    health["checks"]["credentials"] = {
        "status": "ok" if (api_key and api_secret and len(api_secret) == 64) else "error",
        "api_key_present": bool(api_key),
        "secret_length": len(api_secret) if api_secret else 0
    }
    
    # Check recent activity
    try:
        conn = sqlite3.connect('futures_trades.db', timeout=5)
        cursor = conn.cursor()
        last_24h = int((datetime.now() - timedelta(hours=24)).timestamp())
        cursor.execute("SELECT COUNT(*) FROM trades WHERE ts > ?", (last_24h,))
        recent_trades = cursor.fetchone()[0]
        conn.close()
        
        health["checks"]["recent_activity"] = {
            "status": "ok" if recent_trades > 0 else "warning",
            "trades_last_24h": recent_trades
        }
    except Exception:
        health["checks"]["recent_activity"] = {
            "status": "unknown",
            "trades_last_24h": 0
        }
    
    return health

def monitor_and_alert():
    """Monitor bot health and send alerts if needed"""
    health = get_health_status()
    
    if health["status"] == "unhealthy":
        message = f"Bot is unhealthy. Failed checks: {[k for k, v in health['checks'].items() if v['status'] == 'error']}"
        send_notification(message)
        logging.error(message)
    
    # Alert on no recent activity
    recent_activity = health["checks"].get("recent_activity", {})
    if recent_activity.get("trades_last_24h", 0) == 0:
        message = "No trading activity in the last 24 hours"
        send_notification(message)
        logging.warning(message)
    
    return health

def main():
    """Main health check entry point"""
    setup_cloud_logging()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        # Full monitoring with alerts
        health = monitor_and_alert()
        print(json.dumps(health, indent=2))
    else:
        # Simple health check
        health = get_health_status()
        print(json.dumps(health))
        
        # Exit with error code if unhealthy
        if health["status"] == "unhealthy":
            sys.exit(1)

if __name__ == "__main__":
    main()