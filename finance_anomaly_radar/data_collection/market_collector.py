"""
Market Data Collector for Finance Anomaly Radar
Collects real-time market data for stocks, cryptocurrencies, and other financial instruments.
"""

import yfinance as yf
import ccxt
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
import aiohttp
from loguru import logger

from .base_collector import BaseDataCollector

class MarketDataCollector(BaseDataCollector):
    """Collects market data from various exchanges and data providers."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.exchanges = self._initialize_exchanges()
        self.watched_symbols = config.get('watched_symbols', [])
        self.data_cache = {}
        
    def _initialize_exchanges(self) -> Dict[str, Any]:
        """Initialize cryptocurrency exchanges and other data sources."""
        exchanges = {}
        
        try:
            # Initialize Binance for crypto data
            exchanges['binance'] = ccxt.binance({
                'apiKey': self.config.get('binance_api_key', ''),
                'secret': self.config.get('binance_secret', ''),
                'sandbox': self.config.get('sandbox_mode', True),
                'enableRateLimit': True
            })
            
            # Add other exchanges as needed
            exchanges['kraken'] = ccxt.kraken({
                'enableRateLimit': True
            })
            
        except Exception as e:
            logger.error(f"Error initializing exchanges: {e}")
        
        return exchanges
    
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect market data from all configured sources.
        
        Returns:
            List of market data points
        """
        collected_data = []
        
        # Collect stock data
        stock_data = await self._collect_stock_data()
        collected_data.extend(stock_data)
        
        # Collect cryptocurrency data
        crypto_data = await self._collect_crypto_data()
        collected_data.extend(crypto_data)
        
        # Collect options data
        options_data = await self._collect_options_data()
        collected_data.extend(options_data)
        
        return collected_data
    
    async def _collect_stock_data(self) -> List[Dict[str, Any]]:
        """Collect stock market data using Yahoo Finance."""
        stock_data = []
        
        try:
            stock_symbols = self.config.get('stock_symbols', [
                'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NFLX',  # US stocks
                'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS'  # Indian stocks
            ])
            
            for symbol in stock_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Get real-time data
                    hist = ticker.history(period='1d', interval='1m')
                    
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        
                        # Calculate basic indicators
                        volume_avg = hist['Volume'].rolling(window=20).mean().iloc[-1]
                        price_change = ((latest['Close'] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                        
                        stock_data.append({
                            'symbol': symbol,
                            'asset_type': 'stock',
                            'timestamp': datetime.utcnow().isoformat(),
                            'price': float(latest['Close']),
                            'volume': int(latest['Volume']),
                            'high': float(latest['High']),
                            'low': float(latest['Low']),
                            'open': float(latest['Open']),
                            'price_change_percent': float(price_change),
                            'volume_ratio': float(latest['Volume'] / volume_avg) if volume_avg > 0 else 1.0,
                            'market_cap': self._get_market_cap(ticker),
                            'anomaly_flags': self._detect_price_anomalies(hist)
                        })
                
                except Exception as e:
                    logger.warning(f"Error collecting data for {symbol}: {e}")
        
        except Exception as e:
            logger.error(f"Error in stock data collection: {e}")
        
        return stock_data
    
    async def _collect_crypto_data(self) -> List[Dict[str, Any]]:
        """Collect cryptocurrency data from exchanges."""
        crypto_data = []
        
        try:
            crypto_symbols = self.config.get('crypto_symbols', [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'
            ])
            
            for exchange_name, exchange in self.exchanges.items():
                for symbol in crypto_symbols:
                    try:
                        # Get ticker data
                        ticker = await self._get_crypto_ticker(exchange, symbol)
                        
                        if ticker:
                            # Get recent trades for volume analysis
                            trades = await self._get_recent_trades(exchange, symbol)
                            
                            # Get order book for market depth analysis
                            order_book = await self._get_order_book(exchange, symbol)
                            
                            crypto_data.append({
                                'symbol': symbol,
                                'exchange': exchange_name,
                                'asset_type': 'cryptocurrency',
                                'timestamp': datetime.utcnow().isoformat(),
                                'price': ticker['last'],
                                'volume': ticker['baseVolume'],
                                'high': ticker['high'],
                                'low': ticker['low'],
                                'bid': ticker['bid'],
                                'ask': ticker['ask'],
                                'spread': ticker['ask'] - ticker['bid'] if ticker['ask'] and ticker['bid'] else 0,
                                'price_change_percent': ticker['percentage'],
                                'order_book_imbalance': self._calculate_order_book_imbalance(order_book),
                                'trade_velocity': self._calculate_trade_velocity(trades),
                                'anomaly_flags': self._detect_crypto_anomalies(ticker, order_book)
                            })
                    
                    except Exception as e:
                        logger.warning(f"Error collecting {symbol} from {exchange_name}: {e}")
        
        except Exception as e:
            logger.error(f"Error in crypto data collection: {e}")
        
        return crypto_data
    
    async def _collect_options_data(self) -> List[Dict[str, Any]]:
        """Collect options data for volatility analysis."""
        options_data = []
        
        try:
            # Get options data for major stocks
            major_stocks = ['AAPL', 'TSLA', 'SPY']
            
            for symbol in major_stocks:
                ticker = yf.Ticker(symbol)
                options_dates = ticker.options
                
                if options_dates:
                    # Get nearest expiry options
                    nearest_expiry = options_dates[0]
                    options_chain = ticker.option_chain(nearest_expiry)
                    
                    # Analyze calls and puts
                    calls = options_chain.calls
                    puts = options_chain.puts
                    
                    if not calls.empty and not puts.empty:
                        options_data.append({
                            'symbol': symbol,
                            'asset_type': 'options',
                            'expiry_date': nearest_expiry,
                            'timestamp': datetime.utcnow().isoformat(),
                            'call_volume': int(calls['volume'].sum()),
                            'put_volume': int(puts['volume'].sum()),
                            'put_call_ratio': float(puts['volume'].sum() / calls['volume'].sum()) if calls['volume'].sum() > 0 else 0,
                            'implied_volatility_calls': float(calls['impliedVolatility'].mean()),
                            'implied_volatility_puts': float(puts['impliedVolatility'].mean()),
                            'max_pain': self._calculate_max_pain(calls, puts),
                            'unusual_activity': self._detect_unusual_options_activity(calls, puts)
                        })
        
        except Exception as e:
            logger.error(f"Error collecting options data: {e}")
        
        return options_data
    
    async def _get_crypto_ticker(self, exchange, symbol: str) -> Optional[Dict]:
        """Get ticker data from crypto exchange."""
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(None, exchange.fetch_ticker, symbol)
            return ticker
        except Exception as e:
            logger.warning(f"Error fetching ticker {symbol}: {e}")
            return None
    
    async def _get_recent_trades(self, exchange, symbol: str) -> List[Dict]:
        """Get recent trades for trade velocity calculation."""
        try:
            trades = await asyncio.get_event_loop().run_in_executor(None, exchange.fetch_trades, symbol)
            return trades[-50:]  # Last 50 trades
        except Exception:
            return []
    
    async def _get_order_book(self, exchange, symbol: str) -> Optional[Dict]:
        """Get order book for market depth analysis."""
        try:
            order_book = await asyncio.get_event_loop().run_in_executor(None, exchange.fetch_order_book, symbol)
            return order_book
        except Exception:
            return None
    
    def _get_market_cap(self, ticker) -> Optional[float]:
        """Get market capitalization for stock."""
        try:
            info = ticker.info
            return info.get('marketCap')
        except Exception:
            return None
    
    def _detect_price_anomalies(self, hist_data: pd.DataFrame) -> List[str]:
        """Detect price anomalies in historical data."""
        anomalies = []
        
        try:
            if len(hist_data) < 20:
                return anomalies
            
            # Calculate returns
            returns = hist_data['Close'].pct_change()
            
            # Detect abnormal returns (> 3 standard deviations)
            std_dev = returns.std()
            mean_return = returns.mean()
            
            latest_return = returns.iloc[-1]
            if abs(latest_return - mean_return) > 3 * std_dev:
                anomalies.append('abnormal_return')
            
            # Detect volume spikes
            volume_avg = hist_data['Volume'].rolling(window=20).mean()
            latest_volume = hist_data['Volume'].iloc[-1]
            avg_volume = volume_avg.iloc[-1]
            
            if latest_volume > 3 * avg_volume:
                anomalies.append('volume_spike')
            
            # Detect gap up/down
            prev_close = hist_data['Close'].iloc[-2]
            current_open = hist_data['Open'].iloc[-1]
            gap_percent = abs((current_open - prev_close) / prev_close) * 100
            
            if gap_percent > 5:
                anomalies.append('price_gap')
        
        except Exception as e:
            logger.warning(f"Error detecting price anomalies: {e}")
        
        return anomalies
    
    def _detect_crypto_anomalies(self, ticker: Dict, order_book: Optional[Dict]) -> List[str]:
        """Detect cryptocurrency-specific anomalies."""
        anomalies = []
        
        try:
            # Large price movements
            if abs(ticker.get('percentage', 0)) > 20:
                anomalies.append('large_price_movement')
            
            # Wide spread
            if ticker.get('ask') and ticker.get('bid'):
                spread_percent = ((ticker['ask'] - ticker['bid']) / ticker['bid']) * 100
                if spread_percent > 1:  # 1% spread is high
                    anomalies.append('wide_spread')
            
            # Order book imbalance
            if order_book:
                imbalance = self._calculate_order_book_imbalance(order_book)
                if abs(imbalance) > 0.8:  # 80% imbalance
                    anomalies.append('order_book_imbalance')
        
        except Exception as e:
            logger.warning(f"Error detecting crypto anomalies: {e}")
        
        return anomalies
    
    def _calculate_order_book_imbalance(self, order_book: Optional[Dict]) -> float:
        """Calculate order book imbalance (bid vs ask volume)."""
        if not order_book:
            return 0.0
        
        try:
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            bid_volume = sum([bid[1] for bid in bids[:10]])  # Top 10 bids
            ask_volume = sum([ask[1] for ask in asks[:10]])  # Top 10 asks
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.0
            
            # Return value between -1 and 1
            # Positive = more bids (buying pressure)
            # Negative = more asks (selling pressure)
            return (bid_volume - ask_volume) / total_volume
        
        except Exception:
            return 0.0
    
    def _calculate_trade_velocity(self, trades: List[Dict]) -> float:
        """Calculate trade velocity (trades per minute)."""
        if not trades or len(trades) < 2:
            return 0.0
        
        try:
            # Get time range of trades
            first_trade_time = trades[0]['timestamp']
            last_trade_time = trades[-1]['timestamp']
            
            time_diff_minutes = (last_trade_time - first_trade_time) / (1000 * 60)  # Convert to minutes
            
            if time_diff_minutes == 0:
                return float(len(trades))
            
            return len(trades) / time_diff_minutes
        
        except Exception:
            return 0.0
    
    def _calculate_max_pain(self, calls: pd.DataFrame, puts: pd.DataFrame) -> Optional[float]:
        """Calculate options max pain point."""
        try:
            # Combine all strike prices
            strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
            
            max_pain = None
            min_loss = float('inf')
            
            for strike in strikes:
                total_loss = 0
                
                # Calculate call option losses
                call_losses = calls[calls['strike'] < strike]['openInterest'] * (strike - calls[calls['strike'] < strike]['strike'])
                total_loss += call_losses.sum()
                
                # Calculate put option losses
                put_losses = puts[puts['strike'] > strike]['openInterest'] * (puts[puts['strike'] > strike]['strike'] - strike)
                total_loss += put_losses.sum()
                
                if total_loss < min_loss:
                    min_loss = total_loss
                    max_pain = strike
            
            return float(max_pain) if max_pain is not None else None
        
        except Exception:
            return None
    
    def _detect_unusual_options_activity(self, calls: pd.DataFrame, puts: pd.DataFrame) -> List[str]:
        """Detect unusual options activity."""
        unusual_activity = []
        
        try:
            # High volume to open interest ratio
            calls['vol_oi_ratio'] = calls['volume'] / calls['openInterest'].replace(0, 1)
            puts['vol_oi_ratio'] = puts['volume'] / puts['openInterest'].replace(0, 1)
            
            if calls['vol_oi_ratio'].max() > 5:  # Volume > 5x open interest
                unusual_activity.append('high_call_volume')
            
            if puts['vol_oi_ratio'].max() > 5:
                unusual_activity.append('high_put_volume')
            
            # Unusual bid-ask spreads
            calls['spread_percent'] = (calls['ask'] - calls['bid']) / calls['bid'] * 100
            puts['spread_percent'] = (puts['ask'] - puts['bid']) / puts['bid'] * 100
            
            if calls['spread_percent'].mean() > 50:  # Average spread > 50%
                unusual_activity.append('wide_call_spreads')
            
            if puts['spread_percent'].mean() > 50:
                unusual_activity.append('wide_put_spreads')
        
        except Exception as e:
            logger.warning(f"Error detecting unusual options activity: {e}")
        
        return unusual_activity
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate market data.
        
        Args:
            data: Market data to validate
            
        Returns:
            True if data is valid
        """
        required_fields = ['symbol', 'asset_type', 'timestamp', 'price']
        
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate price is positive
        if data['price'] <= 0:
            return False
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            return False
        
        return True
    
    def get_collection_interval(self) -> int:
        """Get market data collection interval."""
        return self.config.get('collection_interval', 60)  # Every minute