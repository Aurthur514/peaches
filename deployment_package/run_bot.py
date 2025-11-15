#!/usr/bin/env python3
"""Simple entry point for cloud deployment"""
import os
import sys

# Set up environment
if not os.getenv('CS_API_KEY'):
    print("ERROR: Missing CS_API_KEY environment variable")
    sys.exit(1)

# Import and run the trading bot
try:
    from coinswitch_futures_live_bot import main
    print("Starting CoinSwitch Futures Trading Bot...")
    main()
except Exception as e:
    print(f"ERROR: Error running bot: {e}")
    sys.exit(1)
