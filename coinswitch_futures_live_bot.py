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
    # Selection
    top_n_min: int = 10
    top_n_max: int = 20
    candles_interval_min: int = 240      # 4H
    candles_limit: int = 120             # fetch enough history
    # Risk & per-coin allocation (dry run)
    capital_per_coin_min: float = 200.0
    capital_per_coin_max: float = 300.0
    sl_pct: float = 0.13                 # 13% stop for long (or above for short)
    tp_pct: float = 0.06                 # 6% take-profit
    partial_tp_pct: float = 0.05         # 5% partial booking
    trail_under_ema9_pct: float = 0.01   # 1% under EMA9
    dry_run: bool = True                 # always True in this file
    # Storage
    db_path: str = "futures_trades.db"
    csv_path: str = "futures_trades.csv"

CFG = LiveConfig()

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

    # 4H candles
    def candles(self, symbol: str, interval_min: int, start_ms: Optional[int] = None, end_ms: Optional[int] = None) -> dict:
        # Candles for futures should use the futures_exchange namespace
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
        return self._req("GET", "/trade/api/v2/candles", params=params)

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
            "symbol": symbol,
            "side": side.upper(),
            "type": order_type.upper(),
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
        payload = {"symbol": symbol, "leverage": int(leverage)}
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

    risk_budget = capital_inr * 0.02
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

# Selection score
def score_coin(df: pd.DataFrame) -> float:
    row = df.iloc[-1]
    score = 0.0
    if row.ema9 > row.ema50 > row.ema200: score += 2.0
    if row.ema9 < row.ema50 < row.ema200: score -= 2.0
    score += float(np.tanh(row.macd_hist)) * 1.5
    if 55 <= row.rsi14 <= 70: score += 1.0
    if row.rsi14 > 75: score -= 0.5
    if not math.isnan(row.vol_sma20) and row.volume > row.vol_sma20: score += 0.5
    return float(score)

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
def normalize_ohlcv(json_payload: dict) -> pd.DataFrame:
    if not isinstance(json_payload, dict):
        raise ValueError(f"Invalid response format: expected dict, got {type(json_payload)}")
    
    data = json_payload.get("data") or json_payload.get("result") or []
    if not data or not isinstance(data, list) or not data[0]:
        raise ValueError("Empty or invalid candles response")
        
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
    """Try fetching candles for sym; if server reports invalid symbol, generate and try common variants
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
                return client._req("GET", "/trade/api/v2/candles", params=params)
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
        # Format: {"data": {"BTCUSDT": {...}, "ETHUSDT": {...}}}
        # Prefer the dict key (the authoritative pair) as the canonical symbol
        # because the candles endpoint appears to accept that form. Fall back
        # to details['symbol'] or base+quote if the key is missing or unusable.
        symbols = []
        for k, details in inst["data"].items():
            # Prefer the dict key first (likely the full pair like 'BTCUSDT' or '0GUSDT')
            try:
                if isinstance(k, str) and k:
                    symbols.append(str(k))
                    continue
            except Exception:
                pass

            # If no usable key, try instrument details
            if isinstance(details, dict):
                cand = details.get("symbol") or details.get("Symbol")
                if cand:
                    symbols.append(str(cand).upper())
                    continue
                base = details.get("base_asset") or details.get("base")
                quote = details.get("quote_asset") or details.get("quote")
                if base and quote:
                    symbols.append(f"{str(base).upper()}{str(quote).upper()}")
                    continue

            # Final fallback
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
    # Optional small-subset debug mode: set CS_MAX_SYMBOLS environment variable
    try:
        max_symbols = int(os.getenv("CS_MAX_SYMBOLS", "0") or 0)
    except Exception:
        max_symbols = 0
    if max_symbols and max_symbols > 0:
        logging.info("Debug mode: limiting symbols to first %d entries", max_symbols)
        symbols = symbols[:max_symbols]
    if not symbols:
        logging.error("Response format: %s", json.dumps(inst, indent=2))
        raise RuntimeError("No futures symbols found from instrument_info")
    logging.info("Found %d futures symbols", len(symbols))

    # Optional probe-only mode: quick-check which symbols the candles endpoint accepts.
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
                client._req("GET", "/trade/api/v2/candles", params=params)
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
    for sym in symbols:
        try:
            # Attempt to fetch candles; if symbol is rejected, try common variants derived from instrument_info
            candles = try_fetch_candles_with_candidates(client, inst, sym, CFG.candles_interval_min)
            df = normalize_ohlcv(candles)
            if len(df) < 60:
                continue
            df = compute_indicators(df).dropna()
            s = score_coin(df)
            scored.append((sym, s, df))
        except Exception as e:
            logging.warning("Skip %s: %s", sym, e)

    if not scored:
        logging.error("No symbols with valid candle data — exiting cleanly")
        return

    scored.sort(key=lambda x: x[1], reverse=True)

    top_k = max(CFG.top_n_min, min(CFG.top_n_max, len(scored)))
    selection = scored[:top_k]
    logging.info("Selected top %d symbols: %s", top_k, [s[0] for s in selection])

    results = []
    ts_now = int(time.time())
    methods = ["trend_follow", "breakout", "mean_revert", "scalp"]

    for i, (sym, s, df) in enumerate(selection):
        row = df.iloc[-1]
        price = float(row.close)
        ema9 = float(row.ema9)
        capital = pick_capital_range(i)

        sigs = {
            "trend_follow": decide_trend_follow(row)["signal"],
            "breakout":     decide_breakout(df)["signal"],
            "mean_revert":  decide_mean_revert(row)["signal"],
            "scalp":        decide_scalp(row)["signal"]
        }

        for method in methods:
            sig = sigs[method]
            sim = simulate_order(sym, price, capital, sig, CFG.sl_pct, CFG.tp_pct, CFG.trail_under_ema9_pct, ema9)
            if sim["status"] == "SIMULATED":
                sim_row = {
                    "ts": ts_now, "symbol": sym, "method": method,
                    "side": sim["side"], "price": sim["price"], "qty": sim["qty"],
                    "sl": sim["sl"], "tp": sim["tp"], "trail": sim["trail"],
                    "capital": capital, "status": sim["status"],
                }
                store.log(sim_row)
                results.append(sim_row)

    long_count = sum(1 for r in results if r["side"] == "BUY")
    short_count = sum(1 for r in results if r["side"] == "SELL")
    logging.info("=== RUN SUMMARY ===")
    logging.info("Symbols scanned: %d | Traded (sim): %d | Longs: %d | Shorts: %d",
                 len(scored), len(results), long_count, short_count)
    by_symbol = {}
    for r in results:
        by_symbol.setdefault(r["symbol"], []).append(r)
    for sym, rows in list(by_symbol.items())[:10]:
        sides = [r["side"][0] for r in rows]
        logging.info("%s => %s (methods=%s)", sym, "".join(sides), ",".join({r["method"] for r in rows}))

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
