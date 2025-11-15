#!/usr/bin/env python3
"""
Web service wrapper for the trading bot
Runs the bot when accessed via HTTP and also provides a health endpoint
"""
from flask import Flask, jsonify
import threading
import time
import os
import sys
from datetime import datetime

app = Flask(__name__)

# Global variable to track last run
last_run_time = None
last_run_status = "Not started"
last_run_output = ""

def run_trading_bot():
    """Run the trading bot in a separate thread"""
    global last_run_time, last_run_status, last_run_output
    
    try:
        last_run_time = datetime.now()
        last_run_status = "Running"
        
        # Import and run the trading bot
        from coinswitch_futures_live_bot import main
        
        # Capture the output
        import io
        from contextlib import redirect_stdout
        
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            main()
        
        last_run_output = output_buffer.getvalue()
        last_run_status = "Completed successfully"
        
    except Exception as e:
        last_run_status = f"Error: {str(e)}"
        last_run_output = f"Error running bot: {str(e)}"
        print(f"Bot error: {e}")

@app.route('/')
def home():
    """Home endpoint that triggers the trading bot"""
    global last_run_time, last_run_status
    
    # Run the trading bot in background
    threading.Thread(target=run_trading_bot, daemon=True).start()
    
    return jsonify({
        "message": "Trading bot started",
        "timestamp": datetime.now().isoformat(),
        "status": "Bot execution initiated"
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "CoinSwitch Futures Trading Bot",
        "timestamp": datetime.now().isoformat(),
        "last_run": last_run_time.isoformat() if last_run_time else "Never",
        "last_status": last_run_status
    })

@app.route('/status')
def status():
    """Status endpoint showing bot execution details"""
    return jsonify({
        "last_run_time": last_run_time.isoformat() if last_run_time else "Never",
        "status": last_run_status,
        "output_preview": last_run_output[:500] if last_run_output else "No output yet",
        "environment": {
            "dry_run": os.getenv('CS_DRY_RUN', 'true'),
            "wallet_balance": os.getenv('CS_WALLET_BALANCE', '1000'),
            "max_symbols": os.getenv('CS_MAX_SYMBOLS', '50')
        }
    })

@app.route('/run')
def manual_run():
    """Manual trigger endpoint"""
    threading.Thread(target=run_trading_bot, daemon=True).start()
    return jsonify({
        "message": "Manual trading bot execution triggered",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Check environment variables
    required_vars = ['CS_API_KEY', 'CS_API_SECRET_HEX']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    print("🚀 Starting CoinSwitch Trading Bot Web Service...")
    print(f"🔧 Dry Run: {os.getenv('CS_DRY_RUN', 'true')}")
    print(f"💰 Wallet: ${os.getenv('CS_WALLET_BALANCE', '1000')}")
    print(f"📊 Max Symbols: {os.getenv('CS_MAX_SYMBOLS', '50')}")
    
    # Get port from environment (Render uses PORT env var)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)