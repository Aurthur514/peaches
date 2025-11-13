#!/usr/bin/env python3
"""
ultron_futures_v2.py
CoinSwitch PRO — Futures ML Trading Bot (inline training)

Features:
 - Uses base URL https://coinswitch.co and exchange "EXCHANGE_2"
 - Signs requests using Ed25519 with SECRET_KEY (base64 encoded)
 - Fetches 4-hour candles (interval=240). Trains on recent 4h bars (configurable).
 - Predicts LONG / SHORT / HOLD (RandomForest trained each run).
 - Places futures limit entry, then TP (limit reduce-only) and SL (stop reduce-only).
 - Auto-leverage computed from ATR and exchange max leverage.
 - Dry-run default, debug, retries, 423 handling.
 - Inline ML training (option A). Model uses recent 4h bars (default 100) to train,
   but the decision primarily evaluates the latest 4h bar to keep predictions aligned
   with your "include 4 hrs of data" request.

Environment:
  - API_KEY (string)
  - SECRET_KEY (base64-encoded ed25519 private key string)
Optional env:
  - BASE_URL (default https://coinswitch.co)
  - EXCHANGE (default EXCHANGE_2)
  - DRY_RUN (if set to "0" or "false", script may place orders - but CLI --dry-run overrides)
  - AUTH_SIG (hex or b64; default 'b64' because secret provided is base64 but signature output is hex/b64 option)
  - AUTH_SIGN_BODY (true/false to include body in signature; default false)
"""

import os
import sys
import time
import json
import math
import logging
import random
import requests
import urllib
from urllib.parse import urlencode
from datetime import datetime
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# ---------------- CLI flags ----------------
DEBUG = '--debug' in sys.argv
DRY_RUN_FLAG = '--dry-run' in sys.argv
AUTO_YES = '--yes' in sys.argv
TEST_ORDER = '--test-order' in sys.argv

# ---------------- Config & defaults ----------------
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO, format='[%(levelname)s] %(message)s')

API_KEY = os.environ.get("API_KEY")
SECRET_KEY_BASE64 = os.environ.get("SECRET_KEY")  # user specified base64 private key
BASE_URL = os.environ.get("BASE_URL", "https://coinswitch.co")
EXCHANGE = os.environ.get("EXCHANGE", "EXCHANGE_2")  # user-specified exchange slug from examples

# Signature options: default to base64 output (server accepts hex or base64; we'll default to 'b64' because SECRET provided base64)
AUTH_SIG = os.environ.get("AUTH_SIG", "b64").lower()  # 'hex' or 'b64'
AUTH_SIGN_BODY = os.environ.get("AUTH_SIGN_BODY", "false").lower() in ("1", "true", "yes")

# trading defaults (user earlier chose TP=10%, SL=5%, leverage=auto)
TAKE_PROFIT_PCT = float(os.environ.get("TP_PCT", "0.10"))
STOP_LOSS_PCT = float(os.environ.get("SL_PCT", "0.05"))
LEVERAGE_MODE = os.environ.get("LEV_MODE", "auto").lower()  # 'auto' or numeric later

# ML & market data
CANDLE_INTERVAL_MIN = 240  # 4-hour bars
LOOKBACK_BARS = int(os.environ.get("LOOKBACK_BARS", "100"))  # bars used for training (>=4 recommended)
MIN_HISTORICAL_ROWS = max(6, min(LOOKBACK_BARS, 6))  # require at least a few bars
TRAIN_TEST_SPLIT = 0.2

# position sizing
TARGET_RISK_PCT = float(os.environ.get("TARGET_RISK_PCT", "0.01"))  # risk per trade as fraction of equity

# runtime
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "15"))
DRY_RUN = True if DRY_RUN_FLAG or os.environ.get("DRY_RUN", "1") in ("1", "true", "yes") else False

# endpoints (from your examples)
FUTURES_INSTRUMENT_INFO = "/trade/api/v2/futures/instrument_info"
FUTURES_ORDERS_CLOSED = "/trade/api/v2/futures/orders/closed"
FUTURES_ORDERS_OPEN = "/trade/api/v2/futures/orders/open"
FUTURES_ORDER = "/trade/api/v2/futures/order"
FUTURES_WALLET_BALANCE = "/trade/api/v2/futures/wallet_balance"
FUTURES_CANCEL_ALL = "/trade/api/v2/futures/cancel_all"
FUTURES_ADD_MARGIN = "/trade/api/v2/futures/add_margin"
FUTURES_TRANSACTIONS = "/trade/api/v2/futures/transactions"
FUTURES_POSITIONS = "/trade/api/v2/futures/positions"
FUTURES_LEVERAGE = "/trade/api/v2/futures/leverage"
FUTURES_TICKER = "/trade/api/v2/futures/ticker"
FUTURES_ORDERBOOK = "/trade/api/v2/futures/order_book"
CANDLES_ENDPOINT = "/trade/api/v2/candles"

LAST_SIGN = {}
LAST_REQUEST = {}

# ---------------- utilities ----------------
def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def jitter_sleep(s):
    time.sleep(s + random.random() * 0.2)

def _canonical_query(params):
    if not params: return ""
    return "?" + urlencode(sorted(params.items()))

def _canonical_body(body):
    if body is None: return ""
    return json.dumps(body, separators=(',', ':'), sort_keys=True)

# ---------------- key loading ----------------
def _load_private_key_from_base64(s):
    if not s:
        return None
    try:
        return base64.b64decode(s)
    except Exception as e:
        raise RuntimeError("SECRET_KEY must be base64-encoded ed25519 private key") from e

_PRIVATE_KEY_BYTES = None
try:
    _PRIVATE_KEY_BYTES = _load_private_key_from_base64(SECRET_KEY_BASE64)
except Exception as e:
    debug_print("[WARN] SECRET_KEY parse:", e)
    _PRIVATE_KEY_BYTES = None

# ---------------- server time & signing ----------------
def get_server_time():
    try:
        r = requests.get(f"{BASE_URL}/trade/api/v2/time", timeout=REQUEST_TIMEOUT)
        if r.ok:
            body = r.json() or {}
            st = body.get("serverTime") or body.get("time") or body.get("server_time")
            if st:
                return str(int(st))
    except Exception:
        pass
    return str(int(time.time() * 1000))

def generate_signature(method, endpoint, params, body, epoch_time):
    """Canonical string: METHOD + unquoted_path(+query) + epoch + (body if AUTH_SIGN_BODY)"""
    method_u = (method or "").upper()
    query = _canonical_query(params)
    unquoted = urllib.parse.unquote_plus(endpoint + query)
    body_str = _canonical_body(body) if AUTH_SIGN_BODY else ""
    signed = method_u + unquoted + epoch_time + body_str
    LAST_SIGN['message'] = signed
    LAST_SIGN['epoch'] = epoch_time
    if _PRIVATE_KEY_BYTES is None:
        raise RuntimeError("SECRET_KEY not loaded or invalid")
    key = ed25519.Ed25519PrivateKey.from_private_bytes(_PRIVATE_KEY_BYTES)
    sig_bytes = key.sign(signed.encode('utf-8'))
    if AUTH_SIG == 'hex':
        sig_out = sig_bytes.hex()
        LAST_SIGN['signature_hex'] = sig_out
        return sig_out
    else:
        sig_out = base64.b64encode(sig_bytes).decode()
        LAST_SIGN['signature_b64'] = sig_out
        return sig_out

def build_headers(method, endpoint, params=None, body=None):
    epoch = get_server_time()
    sig = generate_signature(method, endpoint, params, body, epoch)
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': sig,
        'X-AUTH-EPOCH': epoch
    }
    LAST_REQUEST.update({'method': method, 'endpoint': endpoint, 'params': params, 'body': body, 'headers': headers})
    debug_print("[DEBUG] built headers:", headers)
    return headers

def is_locked_response(resp):
    if not resp: return False
    if getattr(resp, 'status_code', None) == 423:
        logging.warning("[WARN] 423 Locked received => wait 30s")
        time.sleep(30)
        return True
    return False

def is_retryable_http(resp_or_exc):
    code = None
    if hasattr(resp_or_exc, 'status_code'):
        code = resp_or_exc.status_code
    elif getattr(resp_or_exc, 'response', None):
        code = getattr(resp_or_exc.response, 'status_code', None)
    return code in (423, 429) or (isinstance(code, int) and 500 <= code <= 599)

# ---------------- safe GET/POST with re-sign and backoff ----------------
def safe_get(endpoint, params=None, max_retries=4):
    backoff = 2
    for attempt in range(1, max_retries+1):
        try:
            headers = build_headers("GET", endpoint, params=params, body=None)
            url = BASE_URL + endpoint + _canonical_query(params)
            r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            debug_print(f"[DEBUG] GET {url} -> {getattr(r,'status_code',None)}")
            if is_locked_response(r):
                continue
            if r.status_code == 200:
                return r
            if is_retryable_http(r) and attempt < max_retries:
                logging.info("[INFO] GET attempt %d: %s -> retry in %ds", attempt, r.status_code, backoff)
                jitter_sleep(backoff)
                backoff = min(backoff*2, 60)
                continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            logging.error("[ERROR] GET attempt %d failed: %s", attempt, e)
            if DEBUG and getattr(e, 'response', None) is not None:
                debug_print("[DEBUG] resp body:", e.response.text[:800])
            if attempt < max_retries and is_retryable_http(e):
                jitter_sleep(backoff)
                backoff = min(backoff*2, 60)
            else:
                break
    return None

def safe_post(endpoint, params, payload, max_retries=4):
    backoff = 4
    for attempt in range(1, max_retries+1):
        try:
            headers = build_headers("POST", endpoint, params=params, body=payload)
            url = BASE_URL + endpoint + _canonical_query(params)
            r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            debug_print(f"[DEBUG] POST {url} -> {getattr(r,'status_code',None)}")
            if is_locked_response(r):
                if attempt < max_retries:
                    jitter_sleep(backoff); backoff = min(backoff*2, 60); continue
            if r.status_code in (200, 201) or (hasattr(r,'ok') and r.ok):
                return r
            if is_retryable_http(r) and attempt < max_retries:
                logging.info("[INFO] POST attempt %d: %s -> retry in %ds", attempt, r.status_code, backoff)
                jitter_sleep(backoff); backoff = min(backoff*2, 60); continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            logging.error("[ERROR] POST attempt %d failed: %s", attempt, e)
            if DEBUG and getattr(e, 'response', None) is not None:
                debug_print("[DEBUG] resp body:", e.response.text[:800])
            if attempt < max_retries and is_retryable_http(e):
                jitter_sleep(backoff); backoff = min(backoff*2, 60)
            else:
                break
    # final fallback: toggle signature encoding & force sign-body once (best-effort)
    try:
        logging.info("[INFO] final fallback: toggling signature encoding and sign-body")
        old_sig = globals().get('AUTH_SIG', AUTH_SIG)
        old_sb  = globals().get('AUTH_SIGN_BODY', AUTH_SIGN_BODY)
        globals()['AUTH_SIG'] = 'hex' if AUTH_SIG == 'b64' else 'b64'
        globals()['AUTH_SIGN_BODY'] = True
        headers = build_headers("POST", endpoint, params=params, body=payload)
        url = BASE_URL + endpoint + _canonical_query(params)
        r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if r and (r.status_code in (200,201) or getattr(r,'ok',False)):
            logging.info("[INFO] fallback POST succeeded")
            return r
    except Exception as e:
        logging.error("[ERROR] fallback POST exception: %s", e)
    finally:
        globals()['AUTH_SIG'] = old_sig
        globals()['AUTH_SIGN_BODY'] = old_sb
    return None

# ---------------- API helpers (instrument & market) ----------------
def normalize_market(symbol):
    s = (symbol or "").upper()
    if '/' in s:
        a,b = s.split('/')
        return (a + b).lower()
    return s.lower()

def get_instrument_info(market):
    params = {"exchange": EXCHANGE, "symbol": market}
    r = safe_get(FUTURES_INSTRUMENT_INFO, params=params)
    if not r: return {}
    try:
        return r.json().get('data') or r.json().get('result') or r.json()
    except Exception:
        return {}

def get_futures_ticker(market):
    params = {"exchange": EXCHANGE, "symbol": market}
    r = safe_get(FUTURES_TICKER, params=params)
    if not r: return {}
    try:
        return r.json().get('data') or r.json().get('result') or r.json()
    except Exception:
        return {}

def get_max_leverage(market):
    params = {"exchange": EXCHANGE, "symbol": market}
    r = safe_get(FUTURES_LEVERAGE, params=params)
    if not r:
        return 1
    try:
        data = r.json().get('data') or r.json().get('result') or r.json()
        # common keys: leverage, max_leverage
        if isinstance(data, dict):
            val = data.get('max_leverage') or data.get('leverage') or data.get('maxLeverage') or (data.get('data') or {}).get('leverage')
            if val:
                return max(1, int(float(val)))
    except Exception:
        pass
    return 1

def get_wallet_balance():
    r = safe_get(FUTURES_WALLET_BALANCE, params=None)
    if not r:
        return None
    try:
        return r.json().get('data') or r.json().get('result') or r.json()
    except Exception:
        return None

# ---------------- Market data (4hr candles) ----------------
def get_historical_4h(symbol, bars=LOOKBACK_BARS):
    params = {
        "exchange": EXCHANGE,
        "symbol": normalize_market(symbol),
        "interval": str(CANDLE_INTERVAL_MIN),
        "start_time": int(time.time() * 1000) - bars * CANDLE_INTERVAL_MIN * 60 * 1000,
        "end_time": int(time.time() * 1000)
    }
    r = safe_get(CANDLES_ENDPOINT, params=params)
    if not r:
        return pd.DataFrame()
    try:
        body = r.json()
    except Exception:
        return pd.DataFrame()
    maybe = body.get('data') or body.get('result') or body
    rows = []
    # normalize various shapes
    if isinstance(maybe, dict):
        maybe = maybe.get(normalize_market(symbol), []) or maybe.get('candles') or []
    for it in maybe:
        if isinstance(it, dict):
            ts = it.get('timestamp') or it.get('start_time') or it.get('close_time') or it.get('t')
            o = it.get('o') or it.get('open') or it.get('openPrice')
            h = it.get('h') or it.get('high') or it.get('highPrice')
            l = it.get('l') or it.get('low') or it.get('lowPrice')
            c = it.get('c') or it.get('close') or it.get('closePrice')
            v = it.get('v') or it.get('volume') or it.get('baseVolume')
            rows.append([ts, o, h, l, c, v])
        elif isinstance(it, (list, tuple)) and len(it) >= 6:
            rows.append(it[:6])
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df = df.dropna()
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
    for col in ['open','high','low','close','volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna().sort_values('timestamp').reset_index(drop=True)
    return df

def compute_atr(df, window=14):
    if df.empty:
        return 0.0
    df = df.copy()
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['close'].shift(1)).abs()
    df['tr3'] = (df['low'] - df['close'].shift(1)).abs()
    df['tr'] = df[['tr1','tr2','tr3']].max(axis=1)
    return float(df['tr'].rolling(window=window, min_periods=1).mean().iloc[-1])

# ---------------- ML: train on 4h bars (inline) ----------------
def feature_engineer(df):
    df = df.copy()
    df['ret'] = df['close'].pct_change().fillna(0)
    df['SMA_3'] = df['close'].rolling(window=3, min_periods=1).mean()
    df['SMA_6'] = df['close'].rolling(window=6, min_periods=1).mean()
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(window=6, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(window=6, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI_6'] = 100 - (100 / (1 + rs.replace(np.nan, 0)))
    df = df.dropna()
    return df

def create_labels(df, look_ahead=1, thr=0.005):
    df = df.copy()
    df['future'] = df['close'].shift(-look_ahead)
    df['pct'] = (df['future'] - df['close']) / df['close']
    df['label'] = df['pct'].apply(lambda x: 'LONG' if x > thr else ('SHORT' if x < -thr else 'HOLD'))
    df = df.dropna()
    return df

def train_model(df):
    if df.empty or len(df) < 10:
        return None
    df_fe = feature_engineer(df)
    df_lab = create_labels(df_fe, look_ahead=1, thr=0.005)
    if df_lab.empty:
        return None
    features = ['SMA_3','SMA_6','RSI_6','ret']
    X = df_lab[features]
    y = df_lab['label']
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TRAIN_TEST_SPLIT, random_state=42, stratify=y)
    except Exception:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=TRAIN_TEST_SPLIT, random_state=42)
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    try:
        score = model.score(X_test, y_test)
        debug_print("[DEBUG] model score:", score)
    except Exception:
        pass
    return model

def predict_direction(model, df):
    # return LONG/SHORT/HOLD for last bar
    if model is None or df.empty:
        return "HOLD", float('nan')
    df_fe = feature_engineer(df)
    last = df_fe[ ['SMA_3','SMA_6','RSI_6','ret'] ].tail(1)
    if last.empty:
        return "HOLD", float('nan')
    pred = model.predict(last)[0]
    price = df['close'].iloc[-1]
    return pred, float(price)

# ---------------- order sizing & leverage ----------------
def compute_leverage_auto(symbol, price, atr):
    if price <= 0 or atr <= 0:
        return 1
    atr_pct = atr / price
    # heuristic: smaller ATR% => larger leverage, but cap
    desired = max(1, int(round(0.05 / max(atr_pct, 1e-6))))
    max_lev = get_max_leverage(symbol)
    lev = min(max_lev, desired)
    return max(1, int(lev))

def get_max_leverage(symbol):
    try:
        market = normalize_market(symbol)
        params = {"exchange": EXCHANGE, "symbol": market}
        r = safe_get(FUTURES_LEVERAGE, params=params)
        if not r:
            return 1
        j = r.json()
        data = j.get('data') or j.get('result') or j
        if isinstance(data, dict):
            val = data.get('max_leverage') or data.get('leverage') or data.get('maxLeverage') or (data.get('data') or {}).get('leverage')
            if val:
                return max(1, int(float(val)))
    except Exception:
        pass
    return 1

def get_equity_estimate():
    # try futures wallet balance, else portfolio
    w = get_wallet_balance()
    if not w:
        # fallback to user portfolio
        r = safe_get("/trade/api/v2/user/portfolio", params=None)
        if not r:
            return None
        try:
            j = r.json()
            data = j.get('data') or j.get('result') or j
            if isinstance(data, list):
                for item in data:
                    cur = (item.get('currency') or "").upper()
                    if cur in ("USDT", "USD", "INR"):
                        try:
                            val = float(item.get('main_balance') or item.get('current_value') or 0)
                            return val
                        except Exception:
                            continue
            if isinstance(data, dict):
                val = data.get('equity') or data.get('total_equity')
                if val:
                    return float(val)
        except Exception:
            return None
    else:
        # common shapes: {'data': {'wallet_balance': 123}} or {'balance': ...}
        try:
            v = w.get('data') or w.get('result') or w
            if isinstance(v, dict):
                for k in ('wallet_balance','balance','equity','total_equity'):
                    if k in v:
                        try:
                            return float(v.get(k))
                        except Exception:
                            continue
        except Exception:
            return None
    return None

# ---------------- placing orders ----------------
def place_futures_limit_with_tp_sl(symbol, side, entry_price, qty, leverage, tp_pct, sl_pct):
    market = normalize_market(symbol)
    entry_payload = {
        "symbol": market,
        "exchange": EXCHANGE,
        "price": float(entry_price),
        "side": side.upper(),
        "order_type": "LIMIT",
        "quantity": float(qty),
        "reduce_only": False
    }
    debug_print("[DEBUG] entry payload:", entry_payload)
    if DRY_RUN:
        # build TP/SL dry payloads for user inspection
        tp_price = entry_price * (1 + tp_pct) if side.upper()=="BUY" else entry_price * (1 - tp_pct)
        sl_price = entry_price * (1 - sl_pct) if side.upper()=="BUY" else entry_price * (1 + sl_pct)
        tp_payload = {
            "symbol": market, "exchange": EXCHANGE, "price": float(tp_price),
            "side": ("SELL" if side.upper()=="BUY" else "BUY"), "order_type": "LIMIT",
            "quantity": float(qty), "reduce_only": True
        }
        sl_payload = {
            "symbol": market, "exchange": EXCHANGE, "trigger_price": float(sl_price),
            "side": ("SELL" if side.upper()=="BUY" else "BUY"), "order_type": "STOP_MARKET",
            "quantity": float(qty), "reduce_only": True
        }
        return {"ok": True, "dry_run": True, "entry": entry_payload, "tp": tp_payload, "sl": sl_payload}

    # set leverage (POST)
    try:
        lev_payload = {"symbol": market, "exchange": EXCHANGE, "leverage": int(leverage)}
        rlev = safe_post(FUTURES_LEVERAGE, params=None, payload=lev_payload)
        if not rlev:
            logging.warning("Warning: couldn't set leverage before entry")
    except Exception as e:
        debug_print("set leverage error:", e)

    # place entry
    r_entry = safe_post(FUTURES_ORDER, params=None, payload=entry_payload)
    if not r_entry:
        return {"ok": False, "error": "entry_failed"}
    try:
        resp = r_entry.json()
    except Exception:
        resp = {"raw": r_entry.text}
    # best-effort extract order id
    order_id = None
    if isinstance(resp, dict):
        d = resp.get('data') or resp.get('result') or resp
        if isinstance(d, dict):
            order_id = d.get('order_id') or d.get('orderId') or d.get('id') or d.get('order_id')
    # place TP and SL
    tp_price = entry_price * (1 + tp_pct) if side.upper()=="BUY" else entry_price * (1 - tp_pct)
    sl_price = entry_price * (1 - sl_pct) if side.upper()=="BUY" else entry_price * (1 + sl_pct)
    tp_payload = {"symbol": market, "exchange": EXCHANGE, "price": float(tp_price),
                  "side": ("SELL" if side.upper()=="BUY" else "BUY"), "order_type": "LIMIT",
                  "quantity": float(qty), "reduce_only": True, "order_link_id": f"tp-{order_id}"}
    sl_payload = {"symbol": market, "exchange": EXCHANGE, "trigger_price": float(sl_price),
                  "side": ("SELL" if side.upper()=="BUY" else "BUY"), "order_type": "STOP_MARKET",
                  "quantity": float(qty), "reduce_only": True, "order_link_id": f"sl-{order_id}"}
    rtp = safe_post(FUTURES_ORDER, params=None, payload=tp_payload)
    rsl = safe_post(FUTURES_ORDER, params=None, payload=sl_payload)
    return {"ok": True, "entry_resp": resp, "tp_resp": (rtp.json() if rtp is not None else None), "sl_resp": (rsl.json() if rsl is not None else None)}

# ---------------- main run ----------------
def run_ultron(symbols=None, max_symbols=5):
    if not API_KEY or not SECRET_KEY_BASE64:
        print("[ERROR] API_KEY and SECRET_KEY (base64) must be set in environment.")
        return

    print("[START] ultron_futures_v2")
    # get candidate list
    if symbols is None:
        # try futures ticker
        try:
            r = safe_get(FUTURES_TICKER, params={"exchange": EXCHANGE})
            if r:
                j = r.json()
                data = j.get('data') or j.get('result') or j
                if isinstance(data, dict):
                    candidates = list(data.keys())
                elif isinstance(data, list):
                    candidates = [it.get('symbol') or it.get('market') for it in data if it.get('symbol')][:max_symbols]
                else:
                    candidates = []
            else:
                candidates = []
        except Exception:
            candidates = []
        if not candidates:
            candidates = ["BTC/USDT","ETH/USDT"][:max_symbols]
    else:
        candidates = symbols

    # normalize and cap
    normalized = []
    for s in candidates:
        ss = s.upper()
        if '/' in ss:
            normalized.append(ss)
        else:
            if ss.endswith('USDT'):
                normalized.append(ss[:-4] + '/USDT')
            else:
                normalized.append(ss)

    summary = {"started_at": int(time.time()*1000), "trades": []}
    for sym in normalized[:max_symbols]:
        print("\n--- analyzing", sym)
        # fetch history (4h)
        df = get_historical_4h(sym, bars=max(LOOKBACK_BARS, 20))
        if df.empty or len(df) < 2:
            logging.warning("Not enough 4h bars for %s (have %s) - skipping", sym, len(df))
            summary['trades'].append({"symbol": sym, "action": "SKIPPED_NO_DATA"})
            continue

        # train model on recent 4h bars (inline)
        model = train_model(df)
        pred, price = predict_direction(model, df)
        # also compute simple rule based on latest single bar (user wanted 4-hr focus)
        latest_bar = df.tail(1).iloc[0]
        open_p = float(latest_bar['open'])
        close_p = float(latest_bar['close'])
        change = (close_p - open_p) / open_p
        # combine ML and simple rule: if ML gives LONG/SHORT and last bar supports it, act; else HOLD
        if pred == "LONG" and change > 0:
            direction = "LONG"
        elif pred == "SHORT" and change < 0:
            direction = "SHORT"
        else:
            direction = "HOLD"

        print(f"[PRED] {sym} ML={pred} lastbar_change={change:.5f} => decision={direction} price={price}")

        if direction == "HOLD":
            summary['trades'].append({"symbol": sym, "action": "HOLD"})
            continue

        # compute atr and leverage
        atr = compute_atr(df, window=6)
        lev = compute_leverage_auto(sym, price, atr) if LEVERAGE_MODE == "auto" else int(os.environ.get("FIXED_LEV", "1"))
        # position sizing
        equity = get_equity_estimate() or 1000.0
        desired_notional = (equity * TARGET_RISK_PCT) / max(STOP_LOSS_PCT, 1e-9)
        position_notional = desired_notional * lev
        qty = position_notional / max(price, 1e-12)
        # sanity clamps
        if qty <= 0:
            logging.warning("Qty computed zero for %s; skipping", sym)
            summary['trades'].append({"symbol": sym, "action": "SKIPPED_QTY_ZERO"})
            continue

        side = "BUY" if direction == "LONG" else "SELL"
        if DRY_RUN:
            print("[DRY-RUN] Would place", side, sym, "qty=", qty, "price=", price, "lev=", lev)
        else:
            if not AUTO_YES:
                resp = input(f"Confirm place {side} {sym} qty={qty:.6f} @ {price:.6f} lev={lev}? (y/N): ").strip().lower()
                if resp != 'y':
                    logging.info("User skipped")
                    summary['trades'].append({"symbol": sym, "action": "USER_SKIPPED"})
                    continue

        res = place_futures_limit_with_tp_sl(sym, side, price, qty, lev, TAKE_PROFIT_PCT, STOP_LOSS_PCT)
        summary['trades'].append({"symbol": sym, "action": "ORDERED" if res.get('ok') else "FAILED", "result": res})
        jitter_sleep(1.2)

    summary['finished_at'] = int(time.time() * 1000)
    print("\nRun summary:")
    print(json.dumps(summary, indent=2))
    return summary

# ---------------- entrypoint ----------------
if __name__ == "__main__":
    # parse optional CLI --symbols=BTC/USDT,ETH/USDT
    symbols = None
    for a in sys.argv:
        if a.startswith('--symbols='):
            symbols = [x.strip() for x in a.split('=',1)[1].split(',') if x.strip()]
    run_ultron(symbols=symbols, max_symbols=int(os.environ.get("MAX_SYMBOLS", "5")))
