#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoinSwitch Futures Multi-Strategy Bot (One-Cycle Live Scan) — DRY RUN
Author: ChatGPT for Bharathan M

What it does
------------
• Authenticates with CoinSwitch PRO v2 (ed25519 signature).
• Pulls full futures instrument list.
• For each symbol, fetches ~100 recent 4H candles.
• Computes indicators: EMA(9/50/200), MACD(12/26/9), RSI(14), Volume SMA(20).
• Scores each coin's strength and auto-selects top 10–20 symbols.
• Runs 4 strategies (trend_follow, breakout, mean_revert, scalp).
• Simulates orders with SL/TP and EMA9-based trailing + partial booking at +5%.
• Logs to SQLite + CSV, prints a concise summary, and exits (single run).

Safety
------
• dry_run ONLY (no order placement). No WebSocket, no live orders.
• API key and ed25519 private key hex are read from env: CS_API_KEY / CS_API_SECRET_HEX.
"""

import os
import time
import json
import math
import sys
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional

import requests
import numpy as np
import pandas as pd
import sqlite3

from cryptography.hazmat.primitives.asymmetric import ed25519
import urllib.parse
from urllib.parse import urlencode, urlparse
from pathlib import Path

# ----------------------------- Logging -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ----------------------------- Config ------------------------------
@dataclass
class LiveConfig:
    # API bases (per PDF)
    base_v2: str = "https://coinswitch.co"
    exchange_spot: str = "coinswitchx"   # used for /candles 'exchange' param
    futures_exchange: str = "EXCHANGE_2" # v2 futures namespace used in docs
    # Selection & Limits
    max_coins_to_scan: int = 100         # Limit symbols to scan (avoid rate limits)
    top_n_min: int = 5                   # Reduced from 10
    top_n_max: int = 10                  # Reduced from 20
    candles_interval_min: int = 240      # 4H
    candles_limit: int = 120             # fetch enough history
    # Wallet & Risk Management
    wallet_balance_usdt: float = 1000.0  # Default wallet balance (override via env)
    max_portfolio_allocation: float = 0.8 # Use max 80% of wallet
    risk_per_trade: float = 0.02         # Risk 2% per trade
    max_trades_per_run: int = 8          # Max simultaneous positions
    sl_pct: float = 0.13                 # 13% stop for long (or above for short)
    tp_pct: float = 0.06                 # 6% take-profit
    partial_tp_pct: float = 0.05         # 5% partial booking
    trail_under_ema9_pct: float = 0.01   # 1% under EMA9
    dry_run: bool = True                 # default safety; can be overridden via env CS_DRY_RUN
    default_leverage: int = 3            # conservative default leverage if not specified per symbol
    # Storage
    db_path: str = "futures_trades.db"
    csv_path: str = "futures_trades.csv"
    learning_db: str = "bot_learning.db" # Self-learning database

CFG = LiveConfig()

# Allow overriding dry-run and leverage via environment variables safely
def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    val_l = val.strip().lower()
    return val_l in ("1", "true", "yes", "y", "on")

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

# If CS_DRY_RUN is provided, use it directly: true => dry-run ON, false => dry-run OFF
if os.getenv("CS_DRY_RUN") is not None:
    CFG.dry_run = os.getenv("CS_DRY_RUN", "1").strip().lower() in ("1", "true", "yes", "y", "on")

CFG.default_leverage = _env_int("CS_DEFAULT_LEVERAGE", CFG.default_leverage)

# ----------------------------- Auth helpers ------------------------
API_KEY = os.getenv("CS_API_KEY", "")
SECRET_HEX = os.getenv("CS_API_SECRET_HEX", "")  # ed25519 private key hex

def epoch_ms() -> str:
    return str(int(time.time() * 1000))

def sign_v2(method: str, endpoint: str, params: Dict[str, Any], body: Optional[dict], epoch: str) -> Tuple[str, str]:
    unquote_endpoint = endpoint
    if method.upper() == "GET" and params:
        endpoint += ('&', '?')[urlparse(endpoint).query == ''] + urlencode(params)
        unquote_endpoint = urllib.parse.unquote_plus(endpoint)
    signature_msg = method.upper() + unquote_endpoint + epoch
    sk_bytes = bytes.fromhex(SECRET_HEX)
    sk = ed25519.Ed25519PrivateKey.from_private_bytes(sk_bytes)
    sig = sk.sign(signature_msg.encode()).hex()
    return sig, endpoint

def headers_v2(sig: str, epoch: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-AUTH-SIGNATURE": sig,
        "X-AUTH-APIKEY": API_KEY,
        "X-AUTH-EPOCH": epoch,
    }

# ----------------------------- REST client -------------------------
class CSClient:
    def __init__(self, base_v2: str = CFG.base_v2):
        self.base = base_v2

    def _req(self, method: str, path: str, params=None, body=None) -> dict:
        params = params or {}
        max_retries = 3
        retry_delay = 1
        last_error = None

        for attempt in range(max_retries):
            try:
                epoch = epoch_ms()
                sig, endpoint = sign_v2(method, path, params, body, epoch)
                url = self.base + endpoint
                res = requests.request(method, url, headers=headers_v2(sig, epoch), json=body, timeout=20)
                # If this raises, it will be requests.exceptions.HTTPError
                res.raise_for_status()
                return res.json()
            except requests.exceptions.HTTPError as he:
                # For client errors (4xx) except 429, don't retry — likely bad params/symbol
                resp = getattr(he, 'response', None)
                if resp is not None and 400 <= resp.status_code < 500 and resp.status_code != 429:
                    # Log detailed response body to aid debugging (422 reasons etc.)
                    try:
                        body = resp.json()
                    except Exception:
                        body = resp.text
                    logging.error("HTTP %s for %s %s -> %s", resp.status_code, method, url, body)
                    # surface the HTTPError up for caller to handle/log immediately
                    raise
                last_error = he
            except requests.exceptions.RequestException as e:
                last_error = e

            # backoff before next attempt (only reached for retryable errors)
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))

        raise RuntimeError(f"API request failed after {max_retries} attempts: {last_error}")

    # Futures instrument list
    def futures_instrument_info(self) -> dict:
        try:
            return self._req("GET", "/trade/api/v2/futures/instrument_info", params={"exchange": CFG.futures_exchange})
        except Exception:
            body = {"exchange": CFG.futures_exchange}
            return self._req("POST", "/trade/api/v2/futures/instrument_info", body=body)

    # Futures klines (candles)
    def candles(self, symbol: str, interval_min: int, start_ms: Optional[int] = None, end_ms: Optional[int] = None) -> dict:
        # For FUTURES, use the /futures/klines endpoint (not /candles)
        params = {"exchange": CFG.futures_exchange, "symbol": symbol, "interval": str(interval_min)}

        # If caller didn't provide a time window, request a default history window
        # equal to CFG.candles_limit * interval_min minutes (converted to ms).
        now_ms = int(time.time() * 1000)
        if start_ms is None:
            duration_ms = int(CFG.candles_limit) * int(interval_min) * 60 * 1000
            start_ms = now_ms - duration_ms
        if end_ms is None:
            end_ms = now_ms

        params["start_time"] = str(start_ms)
        params["end_time"] = str(end_ms)
        return self._req("GET", "/trade/api/v2/futures/klines", params=params)

    # ----- Futures trading endpoints -----
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                    price: Optional[float] = None, reduce_only: bool = False,
                    leverage: int = 1, time_in_force: Optional[str] = None,
                    client_order_id: Optional[str] = None, extra: Optional[dict] = None,
                    dry_run: Optional[bool] = None) -> dict:
        """Place a futures order. By default respects CFG.dry_run; set dry_run=False to actually send.

        order_type: MARKET | LIMIT | STOP_MARKET | TAKE_PROFIT etc. (based on API)
        side: BUY or SELL
        """
        if dry_run is None:
            dry_run = CFG.dry_run

        payload = {
            "exchange": CFG.futures_exchange,
            "symbol": symbol,
            "side": side.upper(),
            "order_type": order_type.upper(),
            "quantity": str(quantity),
            "reduce_only": reduce_only,
            "leverage": int(leverage),
        }
        if price is not None:
            payload["price"] = str(price)
        if time_in_force:
            payload["time_in_force"] = time_in_force
        if client_order_id:
            payload["client_order_id"] = client_order_id
        if extra:
            payload.update(extra)

        logging.info("place_order called (dry_run=%s): %s", dry_run, {k: payload.get(k) for k in ("symbol","side","type","quantity","price","leverage")})
        if dry_run:
            # Simulated order response
            return {
                "status": "SIMULATED",
                "order": payload,
                "message": "Dry-run mode: order not sent"
            }

        return self._req("POST", "/trade/api/v2/futures/order", body=payload)

    def update_leverage(self, symbol: str, leverage: int) -> dict:
        payload = {"exchange": CFG.futures_exchange, "symbol": symbol, "leverage": int(leverage)}
        return self._req("POST", "/trade/api/v2/futures/leverage", body=payload)

    def get_positions(self, symbol: Optional[str] = None) -> dict:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._req("GET", "/trade/api/v2/futures/positions", params=params)

    def get_ticker(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        return self._req("GET", "/trade/api/v2/futures/ticker", params=params)

    def get_all_tickers(self) -> dict:
        return self._req("GET", "/trade/api/v2/futures/all-pairs/ticker")
    
    def get_wallet_balance(self) -> dict:
        """Fetch wallet balance for futures trading."""
        try:
            return self._req("GET", "/trade/api/v2/futures/balance")
        except Exception as e:
            logging.warning("Could not fetch wallet balance: %s", e)
            return {"data": {"available_balance": str(CFG.wallet_balance_usdt)}}

# ----------------------------- Self-Learning System ----------------
class LearningEngine:
    """Self-evolving learning system that tracks strategy performance."""
    
    def __init__(self, db_path: str = "bot_learning.db"):
        self.db_path = os.path.abspath(db_path)
        dir_path = os.path.dirname(self.db_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_tables()
    
    def _init_tables(self):
        cur = self.conn.cursor()
        # Strategy performance tracking
        cur.execute("""CREATE TABLE IF NOT EXISTS strategy_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy TEXT,
            symbol TEXT,
            timestamp INTEGER,
            score REAL,
            entry_price REAL,
            exit_price REAL,
            pnl_pct REAL,
            success INTEGER
        )""")
        
        # Symbol performance tracking
        cur.execute("""CREATE TABLE IF NOT EXISTS symbol_performance (
            symbol TEXT PRIMARY KEY,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            avg_pnl REAL DEFAULT 0.0,
            last_updated INTEGER
        )""")
        
        # Strategy weights (evolving parameters)
        cur.execute("""CREATE TABLE IF NOT EXISTS strategy_weights (
            strategy TEXT PRIMARY KEY,
            weight REAL DEFAULT 1.0,
            success_rate REAL DEFAULT 0.5,
            last_updated INTEGER
        )""")
        self.conn.commit()
    
    def log_trade_outcome(self, strategy: str, symbol: str, score: float, 
                          entry: float, exit: float, success: bool):
        """Log trade outcome for learning."""
        pnl_pct = ((exit - entry) / entry) * 100 if entry > 0 else 0
        ts = int(time.time())
        
        cur = self.conn.cursor()
        cur.execute("""INSERT INTO strategy_performance 
                       (strategy, symbol, timestamp, score, entry_price, exit_price, pnl_pct, success)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (strategy, symbol, ts, score, entry, exit, pnl_pct, 1 if success else 0))
        
        # Update symbol performance
        cur.execute("""INSERT INTO symbol_performance (symbol, total_trades, winning_trades, avg_pnl, last_updated)
                       VALUES (?, 1, ?, ?, ?)
                       ON CONFLICT(symbol) DO UPDATE SET
                       total_trades = total_trades + 1,
                       winning_trades = winning_trades + ?,
                       avg_pnl = (avg_pnl * total_trades + ?) / (total_trades + 1),
                       last_updated = ?""",
                    (symbol, 1 if success else 0, pnl_pct, ts, 1 if success else 0, pnl_pct, ts))
        
        self.conn.commit()
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get current strategy weights based on historical performance."""
        cur = self.conn.cursor()
        cur.execute("SELECT strategy, weight FROM strategy_weights")
        weights = dict(cur.fetchall())
        
        # Default weights if not learned yet
        default = {"trend_follow": 1.0, "breakout": 0.8, "mean_revert": 0.6, "scalp": 1.0}
        return {**default, **weights}
    
    def update_strategy_weights(self):
        """Update strategy weights based on recent performance."""
        cur = self.conn.cursor()
        # Calculate success rates for each strategy from recent trades
        cur.execute("""SELECT strategy, 
                             AVG(success) as success_rate,
                             COUNT(*) as count
                      FROM strategy_performance 
                      WHERE timestamp > ? 
                      GROUP BY strategy""",
                    (int(time.time()) - 30*24*3600,))  # Last 30 days
        
        ts = int(time.time())
        for strategy, success_rate, count in cur.fetchall():
            if count >= 5:  # Need at least 5 trades to update
                # Weight = success_rate * 2 (range 0 to 2)
                weight = max(0.3, min(2.0, success_rate * 2))
                cur.execute("""INSERT INTO strategy_weights (strategy, weight, success_rate, last_updated)
                               VALUES (?, ?, ?, ?)
                               ON CONFLICT(strategy) DO UPDATE SET
                               weight = ?, success_rate = ?, last_updated = ?""",
                            (strategy, weight, success_rate, ts, weight, success_rate, ts))
        
        self.conn.commit()
    
    def get_top_symbols(self, limit: int = 50) -> List[str]:
        """Get historically best performing symbols."""
        cur = self.conn.cursor()
        cur.execute("""SELECT symbol FROM symbol_performance 
                       WHERE total_trades >= 3 
                       ORDER BY (winning_trades * 1.0 / total_trades) DESC, avg_pnl DESC 
                       LIMIT ?""", (limit,))
        return [row[0] for row in cur.fetchall()]

# ----------------------------- Indicators -------------------------
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))

def macd(series: pd.Series, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    fast_ = ema(series, fast); slow_ = ema(series, slow)
    line = fast_ - slow_; sig = ema(line, signal); hist = line - sig
    return line, sig, hist

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema9"] = ema(df["close"], 9)
    df["ema50"] = ema(df["close"], 50)
    df["ema200"] = ema(df["close"], 200)
    m, s, h = macd(df["close"], 12, 26, 9)
    df["macd_line"], df["macd_signal"], df["macd_hist"] = m, s, h
    df["rsi14"] = rsi(df["close"], 14)
    df["vol_sma20"] = sma(df["volume"], 20)
    return df

# ----------------------------- Strategy logic ---------------------
def decide_trend_follow(row) -> Dict[str, Any]:
    if row.ema9 > row.ema50 > row.ema200 and row.macd_line > row.macd_signal and row.rsi14 < 70:
        return {"signal": "LONG"}
    if row.ema9 < row.ema50 < row.ema200 and row.macd_line < row.macd_signal and row.rsi14 > 30:
        return {"signal": "SHORT"}
    return {"signal": "FLAT"}

def decide_breakout(df) -> Dict[str, Any]:
    row = df.iloc[-1]
    high = df["high"].rolling(20).max().iloc[-2]
    low = df["low"].rolling(20).min().iloc[-2]
    if row.close > high and row.macd_hist > 0:
        return {"signal": "LONG"}
    if row.close < low and row.macd_hist < 0:
        return {"signal": "SHORT"}
    return {"signal": "FLAT"}

def decide_mean_revert(row) -> Dict[str, Any]:
    if row.rsi14 > 75:
        return {"signal": "SHORT"}
    if row.rsi14 < 25:
        return {"signal": "LONG"}
    return {"signal": "FLAT"}

def decide_scalp(row) -> Dict[str, Any]:
    if row.macd_line > row.macd_signal and row.rsi14 < 70:
        return {"signal": "LONG"}
    if row.macd_line < row.macd_signal and row.rsi14 > 30:
        return {"signal": "SHORT"}
    return {"signal": "FLAT"}

def simulate_order(symbol: str, price: float, capital_inr: float, signal: str,
                   sl_pct: float, tp_pct: float, trail_under_ema9_pct: float, ema9: float) -> Dict[str, Any]:
    if signal == "FLAT":
        return {"symbol": symbol, "status": "NO_TRADE"}

    if signal == "LONG":
        sl = price * (1 - sl_pct)
        tp = price * (1 + tp_pct)
        trail = ema9 * (1 - trail_under_ema9_pct)
        stop_range = price - sl
    else:
        sl = price * (1 + sl_pct)
        tp = price * (1 - tp_pct)
        trail = ema9 * (1 + trail_under_ema9_pct)  # for short, above EMA9
        stop_range = sl - price

    # Dynamic position sizing based on risk
    risk_budget = capital_inr * CFG.risk_per_trade
    qty = max(0.0, risk_budget / max(1e-8, stop_range))

    return {
        "symbol": symbol,
        "price": price,
        "side": "BUY" if signal == "LONG" else "SELL",
        "sl": sl,
        "tp": tp,
        "trail": trail,
        "qty": qty,
        "status": "SIMULATED"
    }

# Selection score with learning enhancement
def score_coin(df: pd.DataFrame, learning: Optional['LearningEngine'] = None, symbol: str = "") -> float:
    row = df.iloc[-1]
    score = 0.0
    
    # Technical score
    if row.ema9 > row.ema50 > row.ema200: score += 2.0
    if row.ema9 < row.ema50 < row.ema200: score -= 2.0
    score += float(np.tanh(row.macd_hist)) * 1.5
    if 55 <= row.rsi14 <= 70: score += 1.0
    if row.rsi14 > 75: score -= 0.5
    if not math.isnan(row.vol_sma20) and row.volume > row.vol_sma20: score += 0.5
    
    # Learning bonus: boost score for historically successful symbols
    if learning and symbol:
        cur = learning.conn.cursor()
        cur.execute("""SELECT winning_trades * 1.0 / total_trades as win_rate 
                       FROM symbol_performance 
                       WHERE symbol = ? AND total_trades >= 3""", (symbol,))
        result = cur.fetchone()
        if result:
            win_rate = result[0]
            # Add bonus score based on historical win rate (0 to +2)
            score += (win_rate - 0.5) * 4  # 50% = 0, 75% = +1, 100% = +2
    
    return float(score)

def calculate_position_sizes(available_balance: float, num_positions: int) -> List[float]:
    """Calculate dynamic position sizes based on available balance."""
    if num_positions == 0:
        return []
    
    # Use portfolio allocation limit
    total_allocatable = available_balance * CFG.max_portfolio_allocation
    
    # Distribute with slight variation (not equal allocation)
    base_size = total_allocatable / num_positions
    sizes = []
    for i in range(num_positions):
        # Add 10% variation based on position index
        variation = 1.0 - 0.1 + (0.2 * (i / max(1, num_positions - 1)))
        size = base_size * variation
        sizes.append(round(size, 2))
    
    # Normalize to ensure total doesn't exceed limit
    total = sum(sizes)
    if total > total_allocatable:
        factor = total_allocatable / total
        sizes = [round(s * factor, 2) for s in sizes]
    
    return sizes

# ----------------------------- Storage ----------------------------
class Store:
    def __init__(self, db_path: str = "futures_trades.db", csv_path: str = "futures_trades.csv"):
        self.db_path = os.path.abspath(db_path)
        self.csv_path = os.path.abspath(csv_path)
        # Ensure directory exists for both files
        for path in [self.db_path, self.csv_path]:
            dir_path = os.path.dirname(path)
            if dir_path:  # Only create if there's a directory component
                os.makedirs(dir_path, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER,
            symbol TEXT,
            method TEXT,
            side TEXT,
            price REAL,
            qty REAL,
            sl REAL,
            tp REAL,
            trail REAL,
            capital REAL,
            status TEXT
        )""")
        self.conn.commit()

    def log(self, row: Dict[str, Any]):
        fields = ["ts","symbol","method","side","price","qty","sl","tp","trail","capital","status"]
        data = [row.get(k) for k in fields]
        cur = self.conn.cursor()
        cur.execute(f"INSERT INTO trades ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})", data)
        self.conn.commit()
        df = pd.DataFrame([row])
        append_header = not Path(self.csv_path).exists()
        df.to_csv(self.csv_path, mode="a", index=False, header=append_header)

# ----------------------------- Helpers ----------------------------
def _to_step(value: float, step: Optional[float]) -> float:
    try:
        s = float(step or 0)
        if s <= 0:
            return float(value)
        return math.floor(float(value) / s) * s
    except Exception:
        return float(value)

def _round_precision(value: float, precision: Optional[int]) -> float:
    try:
        p = int(precision) if precision is not None else None
        return round(float(value), max(0, p)) if p is not None else float(value)
    except Exception:
        return float(value)

def normalize_ohlcv(json_payload: dict) -> pd.DataFrame:
    """Parse klines/candles response into OHLCV DataFrame.
    
    Handles two formats:
    1. Futures klines: list of dicts with keys 'o','h','l','c','v','t'
    2. Spot candles: list of arrays [time, open, high, low, close, volume]
    """
    if not isinstance(json_payload, dict):
        raise ValueError(f"Invalid response format: expected dict, got {type(json_payload)}")
    
    data = json_payload.get("data") or json_payload.get("result") or []
    if not data or not isinstance(data, list):
        raise ValueError("Empty or invalid candles response")
    
    if not data[0]:
        raise ValueError("Empty first element in candles data")
    
    # Check if data is list of dicts (futures klines format) or list of arrays (spot candles)
    if isinstance(data[0], dict):
        # Futures klines format: [{"o": "1.23", "h": "1.25", "l": "1.20", "c": "1.24", "v": "1000", "t": 1234567890}, ...]
        rows = []
        for item in data:
            try:
                t = int(item.get('t') or item.get('timestamp') or item.get('start_time') or item.get('close_time') or 0)
                o = float(item.get('o') or item.get('open') or item.get('O') or 0)
                h = float(item.get('h') or item.get('high') or item.get('H') or 0)
                l = float(item.get('l') or item.get('low') or item.get('L') or 0)
                c = float(item.get('c') or item.get('close') or item.get('C') or 0)
                v = float(item.get('v') or item.get('volume') or item.get('q') or 0)
                if t and o and c:  # Must have at least timestamp and price data
                    rows.append([t, o, h, l, c, v])
            except (ValueError, TypeError):
                continue
        
        if not rows:
            raise ValueError("No valid klines data could be parsed")
        
        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    else:
        # Spot candles format: [[time, open, high, low, close, volume], ...]
        cols = ["time","open","high","low","close","volume"]
        try:
            df = pd.DataFrame(data, columns=cols[:len(data[0])])
        except Exception as e:
            raise ValueError(f"Failed to create DataFrame: {str(e)}")
        if "time" not in df.columns: df.rename(columns={df.columns[0]: "time"}, inplace=True)
        if "open" not in df.columns: df.rename(columns={df.columns[1]: "open"}, inplace=True)
        if "high" not in df.columns: df.rename(columns={df.columns[2]: "high"}, inplace=True)
        if "low" not in df.columns: df.rename(columns={df.columns[3]: "low"}, inplace=True)
        if "close" not in df.columns: df.rename(columns={df.columns[4]: "close"}, inplace=True)
        if "volume" not in df.columns: df.rename(columns={df.columns[5]: "volume"}, inplace=True)
        df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
    
    # Convert timestamp to datetime
    if len(df) > 0:
        t = float(df["time"].iloc[-1])
        if t > 10_000_000_000:  # ms
            df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        else:
            df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    
    return df

def pick_capital_range(i: int) -> float:
    span = CFG.capital_per_coin_max - CFG.capital_per_coin_min
    return CFG.capital_per_coin_min + (i % 10) / 10.0 * span


def try_fetch_candles_with_candidates(client: CSClient, inst_raw: dict, sym: str, interval_min: int) -> dict:
    """Try fetching klines for sym; if server reports invalid symbol, generate and try common variants
    using instrument_info details (base/quote) when available."""
    candidates = [sym, sym.lower(), sym.upper()]
    # If we have instrument details, build candidates from base/quote
    try:
        if isinstance(inst_raw, dict) and "data" in inst_raw and isinstance(inst_raw["data"], dict):
            details = inst_raw["data"].get(sym) or inst_raw["data"].get(sym.upper()) or inst_raw["data"].get(sym.lower())
            if isinstance(details, dict):
                base = details.get("base_asset") or details.get("symbol") or ""
                quote = details.get("quote_asset") or ""
                if base and quote:
                    candidates.extend([
                        f"{base}{quote}", f"{base.upper()}{quote.upper()}", f"{base}-{quote}", f"{base.upper()}-{quote.upper()}",
                        f"{base}_{quote}", f"{base.upper()}_{quote.upper()}"
                    ])
                # also try base alone and simple variations
                if base:
                    candidates.extend([base, base.upper()])
                # try removing common suffixes from original sym (e.g., strip 'USDT')
                if sym.lower().endswith('usdt'):
                    stripped = sym[:-4]
                    candidates.extend([stripped, stripped.lower(), stripped.upper()])
    except Exception:
        logging.debug("Could not derive candidates from instrument_info for %s", sym)

    seen = set()
    exchanges = [CFG.futures_exchange, CFG.exchange_spot]
    for c in candidates:
        if not c or c in seen:
            continue
        seen.add(c)
        for exch in exchanges:
            params = {"exchange": exch, "symbol": c, "interval": str(interval_min)}
            now_ms = int(time.time() * 1000)
            duration_ms = int(CFG.candles_limit) * int(interval_min) * 60 * 1000
            params["start_time"] = str(now_ms - duration_ms)
            params["end_time"] = str(now_ms)
            try:
                # Use the futures klines endpoint for futures data
                endpoint = "/trade/api/v2/futures/klines" if exch == CFG.futures_exchange else "/trade/api/v2/candles"
                return client._req("GET", endpoint, params=params)
            except requests.exceptions.HTTPError as he:
                resp = getattr(he, 'response', None)
                if resp is not None and resp.status_code == 422:
                    logging.info("Candidate %s with exchange %s rejected (422)", c, exch)
                    continue
                raise
            except Exception:
                raise

    # If none succeeded, raise a RuntimeError to be caught by caller
    raise RuntimeError(f"Could not fetch candles for {sym} with any candidate variants")

# ----------------------------- Main run ---------------------------
def run_once():
    if not API_KEY or not SECRET_HEX:
        raise RuntimeError("Set env vars CS_API_KEY and CS_API_SECRET_HEX before running.")
    
    # Validate API key format
    if not API_KEY.strip() or len(SECRET_HEX) != 64 or not all(c in '0123456789abcdefABCDEF' for c in SECRET_HEX):
        raise ValueError("Invalid API key or secret format")

    client = CSClient()
    store = Store(CFG.db_path, CFG.csv_path)
    learning = LearningEngine(CFG.learning_db)
    
    # Fetch wallet balance
    logging.info("Fetching wallet balance...")
    try:
        wallet_data = client.get_wallet_balance()
        available_balance = float(wallet_data.get("data", {}).get("available_balance", CFG.wallet_balance_usdt))
        # Allow override via environment variable
        available_balance = float(os.getenv("CS_WALLET_BALANCE", available_balance))
        logging.info("Available wallet balance: $%.2f USDT", available_balance)
    except Exception as e:
        available_balance = CFG.wallet_balance_usdt
        logging.warning("Using default balance $%.2f: %s", available_balance, e)
    
    # Update learning weights based on past performance
    learning.update_strategy_weights()
    strategy_weights = learning.get_strategy_weights()
    logging.info("Strategy weights: %s", strategy_weights)

    logging.info("Fetching futures instruments ...")
    inst = client.futures_instrument_info()
    # Probe: log a concise view of the raw instrument_info response to help map symbols
    try:
        if isinstance(inst, dict):
            if "data" in inst:
                data_obj = inst["data"]
                if isinstance(data_obj, dict):
                    first_key = next(iter(data_obj.keys()), None)
                    logging.info("instrument_info: data is dict, first key=%s", first_key)
                    if first_key:
                        logging.info("instrument_info first value snippet: %s", json.dumps(data_obj[first_key], indent=2)[:1000])
                elif isinstance(data_obj, list):
                    logging.info("instrument_info: data is list, first item snippet: %s", json.dumps(data_obj[0], indent=2)[:1000])
            elif "result" in inst:
                logging.info("instrument_info: result length=%d", len(inst.get("result") or []))
            else:
                logging.info("instrument_info: keys=%s", list(inst.keys()))
    except Exception:
        logging.exception("Failed to probe instrument_info response")
    if not isinstance(inst, dict):
        raise ValueError(f"Invalid instrument_info response type: {type(inst)}")
        
    symbols = []
    
    # Handle different response formats
    if "data" in inst and isinstance(inst["data"], dict):
        # Format: {"data": {"0GUSDT": {...}, "BTCUSDT": {...}}}
        # The dict keys ARE the authoritative full symbols for futures pairs.
        # Always use these keys directly - they include both base and quote (e.g., '0GUSDT').
        symbols = []
        for k, details in inst["data"].items():
            # Use the dict key directly - it's the complete trading pair symbol
            if isinstance(k, str) and k:
                symbols.append(str(k))
                continue
            
            # Fallback only if key is not a string (rare edge case)
            if isinstance(details, dict):
                base = details.get("base_asset") or details.get("base")
                quote = details.get("quote_asset") or details.get("quote")
                if base and quote:
                    symbols.append(f"{str(base).upper()}{str(quote).upper()}")
                    continue
            
            # Last resort
            symbols.append(str(k))
    elif "data" in inst and isinstance(inst["data"], list):
        # Format: {"data": [{"symbol": "BTC-USDT"}, ...]}
        for item in inst["data"]:
            if isinstance(item, dict):
                sym = item.get("symbol") or item.get("pair") or item.get("Symbol") or ""
                if sym:
                    symbols.append(sym)
    elif "result" in inst and isinstance(inst["result"], list):
        # Format: {"result": ["BTC-USDT", "ETH-USDT", ...]}
        symbols = [s for s in inst["result"] if isinstance(s, str)]
                
    symbols = list(dict.fromkeys(symbols))
    
    # Debug: log first few symbols to verify correct format
    if symbols:
        logging.info("First 5 symbols collected: %s", symbols[:5])
    
    # Build a quick symbol->details map when available for live order precision
    symbol_details = inst.get("data", {}) if isinstance(inst.get("data", {}), dict) else {}

    # Apply intelligent symbol limit
    max_to_scan = int(os.getenv("CS_MAX_SYMBOLS", CFG.max_coins_to_scan))
    
    # Prefer historically good symbols if we have learning data
    top_historical = learning.get_top_symbols(max_to_scan // 2) if max_to_scan < len(symbols) else []
    if top_historical:
        # Mix top historical with new symbols for exploration
        historical_set = set(top_historical)
        new_symbols = [s for s in symbols if s not in historical_set][:max_to_scan // 2]
        symbols = top_historical + new_symbols
        logging.info("Using %d historical winners + %d new symbols", len(top_historical), len(new_symbols))
    else:
        symbols = symbols[:max_to_scan]
    
    logging.info("Scanning %d futures symbols (limited from %d total)", len(symbols), len(inst.get("data", {})))
    
    # Optional small-subset debug mode: set CS_MAX_SYMBOLS environment variable
    if not symbols:
        logging.error("Response format: %s", json.dumps(inst, indent=2))
        raise RuntimeError("No futures symbols found from instrument_info")
    logging.info("Found %d futures symbols", len(symbols))

    # Optional probe-only mode: quick-check which symbols the futures klines endpoint accepts.
    if os.getenv("CS_PROBE_ONLY", ""):
        probe_count = int(os.getenv("CS_PROBE_COUNT", "20") or 20)
        probe_list = symbols[:probe_count]
        ok = []
        bad = []
        now_ms = int(time.time() * 1000)
        duration_ms = int(CFG.candles_limit) * int(CFG.candles_interval_min) * 60 * 1000
        for s in probe_list:
            params = {"exchange": CFG.futures_exchange, "symbol": s, "interval": str(CFG.candles_interval_min),
                      "start_time": str(now_ms - duration_ms), "end_time": str(now_ms)}
            try:
                client._req("GET", "/trade/api/v2/futures/klines", params=params)
                ok.append(s)
            except Exception as e:
                bad.append((s, str(e)))
        logging.info("Probe finished: %d ok, %d bad", len(ok), len(bad))
        if ok:
            logging.info("Working symbols (sample up to 20): %s", ok[:20])
        if bad:
            logging.info("Sample failures: %s", bad[:10])
        return

    scored: List[Tuple[str, float, pd.DataFrame]] = []
    for i, sym in enumerate(symbols):
        try:
            # Small delay to avoid rate limiting (every 10 symbols)
            if i > 0 and i % 10 == 0:
                time.sleep(1)
            
            # Attempt to fetch candles; if symbol is rejected, try common variants derived from instrument_info
            candles = try_fetch_candles_with_candidates(client, inst, sym, CFG.candles_interval_min)
            df = normalize_ohlcv(candles)
            if len(df) < 60:
                continue
            df = compute_indicators(df).dropna()
            # Use learning-enhanced scoring
            s = score_coin(df, learning, sym)
            scored.append((sym, s, df))
        except Exception as e:
            logging.warning("Skip %s: %s", sym, e)

    if not scored:
        logging.error("No symbols with valid candle data — exiting cleanly")
        return

    scored.sort(key=lambda x: x[1], reverse=True)

    # Limit to max trades per run and ensure we have budget
    max_positions = min(CFG.max_trades_per_run, len(scored))
    top_k = max(CFG.top_n_min, min(CFG.top_n_max, max_positions))
    selection = scored[:top_k]
    logging.info("Selected top %d symbols: %s", top_k, [s[0] for s in selection])
    
    # Calculate dynamic position sizes based on available balance
    position_sizes = calculate_position_sizes(available_balance, len(selection))
    logging.info("Position sizes: %s", position_sizes)

    results = []
    ts_now = int(time.time())
    methods = ["trend_follow", "breakout", "mean_revert", "scalp"]

    for i, (sym, s, df) in enumerate(selection):
        if i >= len(position_sizes):
            break  # Safety check
            
        row = df.iloc[-1]
        price = float(row.close)
        ema9 = float(row.ema9)
        capital = position_sizes[i]

        sigs = {
            "trend_follow": decide_trend_follow(row)["signal"],
            "breakout":     decide_breakout(df)["signal"],
            "mean_revert":  decide_mean_revert(row)["signal"],
            "scalp":        decide_scalp(row)["signal"]
        }

        # Apply learning weights - skip low-weight strategies
        for method in methods:
            weight = strategy_weights.get(method, 1.0)
            if weight < 0.4:  # Skip strategies that perform poorly
                logging.debug("Skipping %s for %s (low weight %.2f)", method, sym, weight)
                continue
                
            sig = sigs[method]
            if sig == "FLAT":
                continue

            if CFG.dry_run:
                sim = simulate_order(sym, price, capital, sig, CFG.sl_pct, CFG.tp_pct, CFG.trail_under_ema9_pct, ema9)
                if sim.get("status") == "SIMULATED":
                    sim_row = {
                        "ts": ts_now, "symbol": sym, "method": method,
                        "side": sim["side"], "price": sim["price"], "qty": sim["qty"],
                        "sl": sim["sl"], "tp": sim["tp"], "trail": sim["trail"],
                        "capital": capital, "status": sim["status"],
                    }
                    store.log(sim_row)
                    results.append(sim_row)
            else:
                try:
                    # Risk-based sizing consistent with simulation
                    if sig == "LONG":
                        sl = price * (1 - CFG.sl_pct)
                        stop_range = price - sl
                        side = "BUY"
                    else:
                        sl = price * (1 + CFG.sl_pct)
                        stop_range = sl - price
                        side = "SELL"

                    risk_budget = capital * CFG.risk_per_trade
                    qty_raw = max(0.0, risk_budget / max(1e-8, stop_range))

                    details = symbol_details.get(sym, {}) if isinstance(symbol_details, dict) else {}
                    step = details.get("base_quantity_step_size") or details.get("lot_size")
                    min_qty = details.get("min_base_quantity")
                    qty_prec = details.get("quantity_precision")

                    qty = _to_step(qty_raw, float(step) if step is not None else None)
                    if min_qty is not None:
                        qty = max(qty, float(min_qty))
                    qty = _round_precision(qty, int(qty_prec) if qty_prec is not None else None)

                    # Fallback protection
                    if qty <= 0:
                        logging.debug("Computed non-positive qty for %s; skipping.", sym)
                        continue

                    # Respect per-symbol max leverage if present
                    lev_cap = int(details.get("max_leverage") or CFG.default_leverage)
                    leverage = max(1, min(CFG.default_leverage, lev_cap))

                    try:
                        client.update_leverage(sym, leverage)
                    except Exception as le:
                        logging.warning("update_leverage failed for %s: %s", sym, le)

                    logging.info("Placing LIVE %s %s qty=%.8f @ MARKET (lev=%d)", method, sym, qty, leverage)
                    resp = client.place_order(symbol=sym, side=side, order_type="MARKET", quantity=qty, leverage=leverage, dry_run=False)
                    status = (resp.get("status") if isinstance(resp, dict) else None) or "PLACED"

                    # Calculate TP/SL prices
                    tp_price = price * (1 + CFG.tp_pct) if side == "BUY" else price * (1 - CFG.tp_pct)
                    sl_price = sl
                    
                    # Place Take Profit order (reduce-only)
                    try:
                        tp_side = "SELL" if side == "BUY" else "BUY"
                        tp_payload = {
                            "symbol": sym,
                            "side": tp_side,
                            "order_type": "TAKE_PROFIT_MARKET",
                            "quantity": qty,
                            "trigger_price": tp_price,
                            "reduce_only": True,
                            "leverage": leverage
                        }
                        tp_resp = client.place_order(symbol=sym, side=tp_side, order_type="TAKE_PROFIT_MARKET",
                                                     quantity=qty, price=None, reduce_only=True, leverage=leverage,
                                                     extra={"trigger_price": str(tp_price)}, dry_run=False)
                        logging.info("TP order placed for %s at trigger %.8f (side=%s)", sym, tp_price, tp_side)
                    except Exception as tp_err:
                        logging.warning("Failed to place TP order for %s: %s", sym, tp_err)
                    
                    # Place Stop Loss order (reduce-only)
                    try:
                        sl_side = "SELL" if side == "BUY" else "BUY"
                        sl_resp = client.place_order(symbol=sym, side=sl_side, order_type="STOP_MARKET",
                                                     quantity=qty, price=None, reduce_only=True, leverage=leverage,
                                                     extra={"trigger_price": str(sl_price)}, dry_run=False)
                        logging.info("SL order placed for %s at trigger %.8f (side=%s)", sym, sl_price, sl_side)
                    except Exception as sl_err:
                        logging.warning("Failed to place SL order for %s: %s", sym, sl_err)

                    live_row = {
                        "ts": ts_now, "symbol": sym, "method": method,
                        "side": side, "price": price, "qty": qty,
                        "sl": sl_price, "tp": tp_price,
                        "trail": ema9 * (1 - CFG.trail_under_ema9_pct) if side == "BUY" else ema9 * (1 + CFG.trail_under_ema9_pct),
                        "capital": capital, "status": status,
                    }
                    store.log(live_row)
                    results.append(live_row)
                    # After placing a live order for this symbol, avoid stacking multiple entries
                    break
                except Exception as oe:
                    logging.error("Live order failed for %s (%s): %s", sym, method, oe)

    long_count = sum(1 for r in results if r["side"] == "BUY")
    short_count = sum(1 for r in results if r["side"] == "SELL")
    total_capital_used = sum(r["capital"] for r in results)
    
    logging.info("=== RUN SUMMARY ===")
    logging.info("Wallet Balance: $%.2f | Max Allocation: $%.2f (%.0f%%)",
                 available_balance, available_balance * CFG.max_portfolio_allocation, 
                 CFG.max_portfolio_allocation * 100)
    logging.info("Capital Used: $%.2f | Symbols scanned: %d | Positions: %d",
                 total_capital_used, len(scored), len(results))
    logging.info("Longs: %d | Shorts: %d", long_count, short_count)
    logging.info("Strategy weights (learned): %s", 
                 {k: f"{v:.2f}" for k, v in strategy_weights.items()})
    
    by_symbol = {}
    for r in results:
        by_symbol.setdefault(r["symbol"], []).append(r)
    for sym, rows in list(by_symbol.items())[:10]:
        sides = [r["side"][0] for r in rows]
        capital_sym = sum(r["capital"] for r in rows)
        logging.info("%s => %s $%.0f (methods=%s)", 
                    sym, "".join(sides), capital_sym, ",".join({r["method"] for r in rows}))

def main():
    try:
        run_once()
    except requests.exceptions.RequestException as e:
        logging.error("Network error: %s", str(e))
        sys.exit(1)
    except ValueError as e:
        logging.error("Data validation error: %s", str(e))
        sys.exit(1)
    except RuntimeError as e:
        logging.error("Runtime error: %s", str(e))
        sys.exit(1)
    except Exception as e:
        logging.error("Unexpected error: %s", str(e), exc_info=True)
        sys.exit(1)

# Note: main() will be invoked at the end of this file after helper definitions


def probe_endpoints(client: CSClient) -> dict:
    """Quick probe that calls read-only endpoints and returns a small summary.

    Controlled via env: CS_RUN_PROBE=1
    """
    out = {}
    logging.info("Running probe: get_all_tickers()")
    try:
        all_t = client.get_all_tickers()
        # try to be flexible with response shape
        if isinstance(all_t, dict) and "data" in all_t:
            tickers = all_t.get("data")
        elif isinstance(all_t, dict) and "result" in all_t:
            tickers = all_t.get("result")
        else:
            tickers = all_t
        out["tickers_count"] = len(tickers) if hasattr(tickers, "__len__") else 0
    except Exception as e:
        out["tickers_error"] = str(e)
        tickers = []

    logging.info("Calling get_positions()")
    try:
        pos = client.get_positions()
        out["positions"] = pos
    except Exception as e:
        out["positions_error"] = str(e)

    # sample a ticker if available
    sample_sym = None
    try:
        if tickers:
            if isinstance(tickers, list):
                # items may be dicts or strings
                first = tickers[0]
                if isinstance(first, dict):
                    sample_sym = first.get("symbol") or first.get("pair")
                elif isinstance(first, str):
                    sample_sym = first
            elif isinstance(tickers, dict):
                # dict of symbol->details
                sample_sym = next(iter(tickers.keys()), None)
    except Exception:
        sample_sym = None

    if sample_sym:
        logging.info("Calling get_ticker(%s)", sample_sym)
        try:
            t = client.get_ticker(sample_sym)
            out["sample_ticker"] = t
        except Exception as e:
            out["sample_ticker_error"] = str(e)

    # dry-run place order example (safe)
    try:
        logging.info("Simulating place_order (dry-run)")
        sim = client.place_order(symbol=sample_sym or "BTCUSDT", side="BUY", order_type="MARKET", quantity=1.0, dry_run=True)
        out["place_order_sim"] = sim
    except Exception as e:
        out["place_order_error"] = str(e)

    return out


# Run probe after probe_endpoints is defined to avoid NameError
if os.getenv("CS_RUN_PROBE", "") == "1":
    try:
        client = CSClient()
        probe_results = probe_endpoints(client)
        logging.info("Probe results: %s", json.dumps(probe_results, indent=2)[:2000])
    except Exception as e:
        logging.error("Probe failed: %s", e)


if __name__ == "__main__":
    main()
