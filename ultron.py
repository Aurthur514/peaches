#!/usr/bin/env python3
"""
ultron.py — CoinSwitch PRO ML Trading Bot v2.10
----------------------------------------------
Features:
- CLI flags: --auth-mode, --sign-body/--no-sign-body, --dry-run, --dry-run-save, --summary-save, --max-coins, --window-days, --interval, --min-rows, --test-order, --test-amount, --yes, --debug, --include-stables, --no-skip-active, --help
- Re-signs each GET/POST attempt using server time (fallback to local time)
- GET/POST retry with exponential backoff; final POST fallback toggles auth-mode and enables sign-body for one final attempt
- Uses RandomForest to predict BUY/SELL/HOLD
- Uses market min ask (orderbook) for buy price when available
- Robust min_quote (min notional) enforcement with rounding checks and safe skipping
- DRY-RUN file saving and run summary JSON
"""

import os
import sys
import time
import json
import random
import logging
import requests
import urllib
import pandas as pd
from urllib.parse import urlencode
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# -------------------- Usage / help --------------------
USAGE = """
ultron.py — CoinSwitch PRO ML Trading Bot v2.10

Usage:
  python ultron.py [flags]

Flags:
  --help                          Show this help message and exit
  --debug                         Enable debug logs
  --dry-run                       Do not place real orders
  --dry-run-save=PATH             Save DRY-RUN order payloads (default ./dry_run_orders.jsonl)
  --summary-save=PATH             Save run summary JSON at the end
  --yes                           Auto-confirm orders (skip interactive prompt)
  --test-order                    Use a reduced test order amount
  --test-amount=10                Test order amount in INR
  --window-days=120               Lookback days for historical data
  --interval=1440                 Candle interval in minutes (1440=daily, 60=hourly)
  --min-rows=60                   Minimum historical rows required
  --include-stables               Include stablecoin pairs (USDT/USDC...)
  --no-skip-active                Do not skip symbols with active/open orders
  --symbols=BTC/INR,ETH/INR       Comma-separated symbol override
  --max-coins=20                  Max coins to analyze (default 20)
  --auth-mode=hex|b64             Signature format (overrides AUTH_SIG env)
  --sign-body                     Include JSON body when signing (overrides AUTH_SIGN_BODY env)
  --no-sign-body                  Do not include body when signing
"""

if '--help' in sys.argv or '-h' in sys.argv:
    print(USAGE)
    sys.exit(0)

# -------------------- CLI parsing helpers --------------------
def get_cli_arg(prefix, default=None):
    for a in sys.argv:
        if a.startswith(prefix):
            return a.split('=', 1)[1] if '=' in a else ''
    return default

def has_flag(flag):
    return any(a == flag for a in sys.argv)

# -------------------- Config / flags --------------------
DEBUG = has_flag('--debug')
DRY_RUN = has_flag('--dry-run')
AUTO_YES = has_flag('--yes')
TEST_ORDER = has_flag('--test-order')
INCLUDE_STABLES = has_flag('--include-stables')
SKIP_ACTIVE = not has_flag('--no-skip-active')  # default True unless --no-skip-active set

CLI_AUTH_MODE = get_cli_arg('--auth-mode', None)
CLI_SIGN_BODY = None
if has_flag('--sign-body'):
    CLI_SIGN_BODY = True
if has_flag('--no-sign-body'):
    CLI_SIGN_BODY = False

DRY_RUN_SAVE_CLI = get_cli_arg('--dry-run-save', None)
SUMMARY_SAVE = get_cli_arg('--summary-save', None)

TEST_ORDER_AMOUNT = float(get_cli_arg('--test-amount', '10.0'))
LOOKBACK_DAYS = int(get_cli_arg('--window-days', '120'))
CANDLE_INTERVAL_MIN = int(get_cli_arg('--interval', '1440'))
if CANDLE_INTERVAL_MIN not in (60, 1440):
    CANDLE_INTERVAL_MIN = 1440
MIN_HISTORICAL_ROWS = int(get_cli_arg('--min-rows', str(max(60, LOOKBACK_DAYS // 2))))
SYMBOLS_OVERRIDE = None
s = get_cli_arg('--symbols', None)
if s:
    SYMBOLS_OVERRIDE = [x.strip() for x in s.split(',') if x.strip()]
MAX_COINS_TO_PROCESS = int(get_cli_arg('--max-coins', '20'))

# Logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='[%(levelname)s] %(message)s')

# Environment / defaults
ENV_AUTH_SIG = os.environ.get("AUTH_SIG", "hex").lower()  # 'hex' or 'b64'
ENV_SIGN_BODY = os.environ.get("AUTH_SIGN_BODY", "false").lower() in ("1", "true", "yes")

AUTH_SIG = CLI_AUTH_MODE.lower() if CLI_AUTH_MODE else ENV_AUTH_SIG
AUTH_SIGN_BODY = CLI_SIGN_BODY if CLI_SIGN_BODY is not None else ENV_SIGN_BODY

API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")  # hex or base64 ed25519 private key
BASE_URL = os.environ.get("BASE_URL", "https://coinswitch.co")
EXCHANGE = os.environ.get("EXCHANGE", "coinswitchx")
SYMBOL_SUFFIX = "/INR"
TRADE_PERCENT_OF_BALANCE = float(os.environ.get("TRADE_PERCENT_OF_BALANCE", 0.25))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 15))

LAST_SIGN = {}
LAST_REQUEST = {}

# Set default dry-run-save path if not provided and dry-run is enabled
if DRY_RUN and not DRY_RUN_SAVE_CLI:
    DRY_RUN_SAVE = os.path.abspath("./dry_run_orders.jsonl")
else:
    DRY_RUN_SAVE = os.path.abspath(DRY_RUN_SAVE_CLI) if DRY_RUN_SAVE_CLI else None

# -------------------- Utilities --------------------
def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def jitter_sleep(seconds):
    time.sleep(seconds + random.random() * 0.4)

def is_locked_response(resp):
    if not resp:
        return False
    if getattr(resp, "status_code", None) == 423:
        print("[ERROR] 423 Locked: temporary resource/account lock. Waiting 30s...")
        time.sleep(30)
        return True
    return False

def is_retryable_http(e_or_resp):
    code = None
    if hasattr(e_or_resp, 'response') and e_or_resp.response is not None:
        code = getattr(e_or_resp.response, 'status_code', None)
    elif hasattr(e_or_resp, 'status_code'):
        code = e_or_resp.status_code
    return code in (423, 429) or (isinstance(code, int) and 500 <= code <= 599)

# -------------------- Time & signing --------------------
def get_server_time():
    try:
        r = requests.get(f"{BASE_URL}/trade/api/v2/time", timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            j = r.json() or {}
            st = j.get("serverTime")
            if st:
                return str(st)
    except Exception:
        pass
    return str(int(time.time() * 1000))

def _canonical_body(body):
    if body is None:
        return ""
    return json.dumps(body, separators=(',', ':'), sort_keys=True)

def _canonical_query(params):
    if not params:
        return ""
    return '?' + urlencode(sorted((params or {}).items()))

def _load_private_key_bytes(secret):
    if not secret:
        raise RuntimeError("SECRET_KEY not provided.")
    s = secret.strip()
    try:
        if all(c in "0123456789abcdefABCDEF" for c in s) and len(s) % 2 == 0:
            return bytes.fromhex(s)
    except Exception:
        pass
    try:
        return base64.b64decode(s)
    except Exception as e:
        raise RuntimeError("Could not parse SECRET_KEY: provide hex or base64 ed25519 private key.") from e

# load private key bytes once (error handled later)
_PRIVATE_KEY_BYTES = None
try:
    _PRIVATE_KEY_BYTES = _load_private_key_bytes(SECRET_KEY)
except Exception as e:
    debug_print("[WARN] SECRET_KEY parse:", str(e))
    _PRIVATE_KEY_BYTES = None

def generate_signature(method, endpoint, params, body, epoch_time):
    method_u = (method or "").upper()
    query = _canonical_query(params)
    unquoted_path_query = urllib.parse.unquote_plus(endpoint + query)
    body_str = _canonical_body(body) if AUTH_SIGN_BODY else ""
    signed_str = method_u + unquoted_path_query + epoch_time + body_str

    LAST_SIGN['message'] = signed_str
    LAST_SIGN['epoch'] = epoch_time

    if _PRIVATE_KEY_BYTES is None:
        raise RuntimeError("SECRET_KEY not loaded or invalid. Set SECRET_KEY env with ed25519 private key (hex or base64).")

    key = ed25519.Ed25519PrivateKey.from_private_bytes(_PRIVATE_KEY_BYTES)
    sig_bytes = key.sign(signed_str.encode('utf-8'))

    if AUTH_SIG == 'b64':
        sig_out = base64.b64encode(sig_bytes).decode()
        LAST_SIGN['signature_b64'] = sig_out
        debug_print("[DEBUG] signature (b64):", sig_out)
        return sig_out
    else:
        sig_out = sig_bytes.hex()
        LAST_SIGN['signature_hex'] = sig_out
        debug_print("[DEBUG] signature (hex):", sig_out)
        return sig_out

def build_headers(method, endpoint, params=None, body=None):
    epoch_time = get_server_time() or str(int(time.time() * 1000))
    signature = generate_signature(method, endpoint, params, body, epoch_time)
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature,
        'X-AUTH-EPOCH': epoch_time
    }
    LAST_REQUEST.update({'method': method, 'endpoint': endpoint, 'params': params,
                         'body': body, 'headers': headers, 'url': BASE_URL + endpoint + _canonical_query(params)})
    debug_print("[DEBUG] Built headers:", headers)
    return headers

# -------------------- Safe GET/POST with re-signs --------------------
def safe_get_resign(endpoint, params=None):
    max_retries = 6
    backoff = 2
    url = BASE_URL + endpoint
    for attempt in range(1, max_retries + 1):
        try:
            headers = build_headers("GET", endpoint, params=params, body=None)
            url_full = BASE_URL + endpoint + _canonical_query(params)
            r = requests.get(url_full, headers=headers, timeout=REQUEST_TIMEOUT)
            if is_locked_response(r):
                continue
            if is_retryable_http(r) and r.status_code != 200:
                logging.error("[ERROR] GET attempt %d got %s", attempt, r.status_code)
                if attempt < max_retries:
                    jitter_sleep(backoff)
                    backoff = min(backoff * 2, 30)
                    continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            logging.error("[ERROR] GET attempt %d failed: %s", attempt, e)
            if DEBUG and getattr(e, 'response', None) is not None:
                resp = e.response
                debug_print('[DEBUG] Response status:', getattr(resp, 'status_code', None))
                try: debug_print('[DEBUG] Response body:', resp.text)
                except Exception: pass
                debug_print('[DEBUG] Last message:', LAST_SIGN.get('message'))
                debug_print('[DEBUG] Last signature:', LAST_SIGN.get('signature_hex') or LAST_SIGN.get('signature_b64'))
                debug_print('[DEBUG] Last request url:', LAST_REQUEST.get('url'))
            if attempt < max_retries and is_retryable_http(e):
                jitter_sleep(backoff)
                backoff = min(backoff * 2, 30)
            else:
                break
    return None

def safe_post_resign(endpoint, params, payload):
    """
    Re-signs each POST attempt with fresh epoch/signature.
    If repeated attempts fail, tries one final fallback:
      toggles auth-mode (hex<->b64) and enables sign-body for final attempt.
    """
    max_retries = 5
    backoff = 5
    url = BASE_URL + endpoint
    for attempt in range(1, max_retries + 1):
        try:
            headers = build_headers("POST", endpoint, params=params, body=payload)
            url_full = BASE_URL + endpoint + _canonical_query(params)
            r = requests.post(url_full, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            if DEBUG:
                try: debug_print("[DEBUG] POST response:", r.status_code, r.text[:1000])
                except Exception: pass
            if is_locked_response(r):
                # re-check active orders locally
                try:
                    active = get_open_order_symbols()
                    if active:
                        logging.info("[INFO] Symbols with open orders (skipping further POSTs): %s", sorted(active))
                except Exception:
                    pass
                if attempt < max_retries:
                    jitter_sleep(backoff)
                    backoff = min(backoff * 2, 45)
                    continue
            if is_retryable_http(r) and getattr(r, 'status_code', None) != 200:
                logging.error("[ERROR] POST attempt %d got %s", attempt, r.status_code)
                if attempt < max_retries:
                    jitter_sleep(backoff)
                    backoff = min(backoff * 2, 45)
                    continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            logging.error("[ERROR] POST attempt %d failed: %s", attempt, e)
            if DEBUG and getattr(e, 'response', None) is not None:
                resp = e.response
                debug_print('[DEBUG] Response status:', getattr(resp, 'status_code', None))
                try: debug_print('[DEBUG] Response body:', resp.text[:1000])
                except Exception: pass
                debug_print('[DEBUG] Last message:', LAST_SIGN.get('message'))
                debug_print('[DEBUG] Last signature:', LAST_SIGN.get('signature_hex') or LAST_SIGN.get('signature_b64'))
                debug_print('[DEBUG] Last request url:', LAST_REQUEST.get('url'))
            if attempt < max_retries and is_retryable_http(e):
                jitter_sleep(backoff)
                backoff = min(backoff * 2, 45)
            else:
                break

    # Final fallback attempt: toggle auth settings temporarily
    try:
        logging.info("[INFO] Performing final fallback POST attempt with alternate auth settings...")
        old_auth = AUTH_SIG
        old_sign_body = AUTH_SIGN_BODY
        alt_auth = 'b64' if (AUTH_SIG == 'hex') else 'hex'
        globals()['AUTH_SIG'] = alt_auth
        globals()['AUTH_SIGN_BODY'] = True
        headers = build_headers("POST", endpoint, params=params, body=payload)
        url_full = BASE_URL + endpoint + _canonical_query(params)
        r = requests.post(url_full, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if DEBUG:
            try: debug_print("[DEBUG] Fallback POST response:", r.status_code, r.text[:1000])
            except Exception: pass
        if r is not None and r.ok:
            logging.info("[INFO] Fallback POST succeeded with auth=%s sign_body=%s", alt_auth, True)
            return r
        else:
            logging.error("[ERROR] Fallback POST failed: %s", getattr(r, 'status_code', None))
    except Exception as e:
        logging.error("[ERROR] Fallback POST raised exception: %s", e)
    finally:
        globals()['AUTH_SIG'] = old_auth
        globals()['AUTH_SIGN_BODY'] = old_sign_body

    return None

# -------------------- Core API helpers --------------------
def get_inr_balance():
    res = safe_get_resign("/trade/api/v2/user/portfolio", params=None)
    if not res:
        return 0.0
    for item in res.json().get("data", []):
        if item.get("currency", "").lower() == "inr":
            try:
                return float(item.get("main_balance", 0))
            except Exception:
                return 0.0
    return 0.0

def get_top_symbols_by_volume():
    res = safe_get_resign("/trade/api/v2/24hr/all-pairs/ticker", params={"exchange": EXCHANGE})
    if not res:
        return []
    all_pairs = res.json().get("data", {})
    inr_pairs = [v for k, v in all_pairs.items() if k.endswith(SYMBOL_SUFFIX) and float(v.get("quoteVolume", 0)) > 0]
    inr_pairs.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
    return [coin['symbol'] for coin in inr_pairs[:MAX_COINS_TO_PROCESS]]

def get_open_order_symbols():
    res = safe_get_resign("/trade/api/v2/orders", params={"open": True, "exchanges": EXCHANGE, "count": 500})
    if not res:
        return set()
    data = res.json() or {}
    orders = (data.get("data", {}) or {}).get("orders", []) if isinstance(data, dict) else []
    symbols = set()
    for o in orders:
        status = str(o.get("status", "")).upper()
        symbol = o.get("symbol") or o.get("pair") or o.get("market")
        if not symbol:
            continue
        if '/' not in symbol and symbol.endswith('INR') and len(symbol) > 3:
            symbol = symbol[:-3] + '/INR'
        if status in ("OPEN", "PARTIALLY_EXECUTED", "CANCELLATION_RAISED", "EXPIRATION_RAISED"):
            symbols.add(symbol)
    return symbols

def get_trade_info(symbol):
    res = safe_get_resign("/trade/api/v2/tradeInfo", params={"exchange": EXCHANGE, "symbol": symbol})
    if not res:
        return {}
    return res.json().get("data", {}).get(EXCHANGE, {}).get(symbol, {}) or {}

def clamp_to_precision(price, qty, precision):
    base_p = int((precision or {}).get("base", 6) or 6)
    quote_p = int((precision or {}).get("quote", 2) or 2)
    # Ensure rounding behavior uses round() which may be fine; could use Decimal if needed more strict
    return round(float(price), quote_p), round(float(qty), base_p)

# -------------------- Orderbook: get min ask --------------------
def get_min_rate(symbol):
    endpoint = "/trade/api/v2/orderbook"
    params = {"symbol": symbol, "exchange": EXCHANGE, "limit": 50}
    res = safe_get_resign(endpoint, params=params)
    if not res:
        debug_print("[DEBUG] orderbook failed for", symbol)
        return None
    try:
        body = res.json()
    except Exception:
        return None

    data = None
    if isinstance(body, dict):
        data = body.get('data', body)
    else:
        data = body

    asks = None
    if isinstance(data, dict):
        if symbol in data and isinstance(data[symbol], dict):
            dd = data[symbol]
            asks = dd.get('asks') or dd.get('sell') or dd.get('s')
        else:
            asks = data.get('asks') or data.get('sell') or data.get('s') or data.get('ask')
    elif isinstance(data, list):
        if len(data) and isinstance(data[0], dict) and 'asks' in data[0]:
            asks = data[0].get('asks')

    if not asks:
        return None

    min_price = None
    try:
        for a in asks:
            if isinstance(a, (list, tuple)) and len(a) >= 1:
                p = float(a[0])
            elif isinstance(a, dict):
                p = float(a.get('price') or a.get('p') or a.get('rate') or a.get('r') or 0)
            else:
                continue
            if min_price is None or p < min_price:
                min_price = p
    except Exception as e:
        debug_print("[DEBUG] error parsing asks:", e)
        return None

    debug_print(f"[DEBUG] get_min_rate({symbol}) -> {min_price}")
    return min_price

# -------------------- ML: historical, features, model --------------------
def get_historical_data(symbol):
    logging.info("Fetching %d days of historical data for %s (interval=%d min)...", LOOKBACK_DAYS, symbol, CANDLE_INTERVAL_MIN)
    endpoint = "/trade/api/v2/candles"
    end_time = int(time.time() * 1000)
    start_time = end_time - (LOOKBACK_DAYS * 24 * 60 * 60 * 1000)

    def _fetch(interval_minutes):
        params = {"symbol": symbol, "exchange": EXCHANGE, "interval": str(interval_minutes),
                  "start_time": start_time, "end_time": end_time}
        res = safe_get_resign(endpoint, params=params)
        if not res:
            return []
        try:
            body = res.json()
        except Exception:
            return []
        maybe = body.get('data', body) if isinstance(body, dict) else body
        if isinstance(maybe, dict):
            data = maybe.get(symbol) or []
        else:
            data = maybe if isinstance(maybe, list) else []
        out = []
        for item in data:
            try:
                ts = item.get('timestamp') or item.get('start_time') or item.get('close_time') or item.get('t')
                o = item.get('o') or item.get('open')
                h = item.get('h') or item.get('high')
                l = item.get('l') or item.get('low')
                c = item.get('c') or item.get('close')
                v = item.get('volume') or item.get('v')
                out.append([ts, o, h, l, c, v])
            except Exception:
                continue
        return out

    data = _fetch(CANDLE_INTERVAL_MIN)
    if not data:
        logging.warning("No candles returned for %s.", symbol)
        return pd.DataFrame()
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna().sort_values('timestamp')
    median_gap_sec = df['timestamp'].diff().dt.total_seconds().median()
    if median_gap_sec and median_gap_sec < 20 * 60:
        dfr = (df.set_index('timestamp')
                 .resample('D')
                 .agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
                 .dropna()
                 .reset_index())
        if not dfr.empty:
            df = dfr
    return df

def calculate_features(df):
    df = df.copy()
    df['SMA_10'] = df['close'].rolling(window=10, min_periods=10).mean()
    df['SMA_30'] = df['close'].rolling(window=30, min_periods=30).mean()
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(window=14, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14, min_periods=14).mean()
    rs = gain / loss.replace(0, pd.NA)
    df['RSI'] = (100 - (100 / (1 + rs))).fillna(50)
    df = df.dropna(subset=['SMA_10', 'SMA_30', 'RSI'])
    return df

def create_labels(df, look_ahead=7, threshold=0.03):
    df = df.copy()
    df['future_price'] = df['close'].shift(-look_ahead)
    df['price_change'] = (df['future_price'] - df['close']) / df['close']
    df['label'] = df['price_change'].apply(lambda x: 'BUY' if x > threshold else ('SELL' if x < -threshold else 'HOLD'))
    df.dropna(inplace=True)
    return df

def train_and_predict(symbol):
    df = get_historical_data(symbol)
    if df.empty or len(df) < MIN_HISTORICAL_ROWS:
        logging.warning("Not enough data for %s (rows=%s < %s)", symbol, len(df), MIN_HISTORICAL_ROWS)
        return "HOLD", float('nan')
    df_features = calculate_features(df)
    df_labeled = create_labels(df_features.copy())
    if df_labeled.empty:
        return "HOLD", df_features['close'].iloc[-1]
    features = ['SMA_10', 'SMA_30', 'RSI']
    X = df_labeled[features]
    y = df_labeled['label']
    classes = y.unique().tolist()
    if len(classes) == 1:
        logging.info("[INFO] Only one class (%s) present for %s; returning that.", classes[0], symbol)
        return classes[0], df_features['close'].iloc[-1]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    try:
        print(f"[INFO] {symbol} model trained. Accuracy: {model.score(X_test, y_test):.2f}")
    except Exception:
        pass
    latest_features = df_features[features].tail(1)
    prediction = model.predict(latest_features)[0]
    price = df_features['close'].iloc[-1]
    return prediction, price

# -------------------- Min quote extraction & robust placing --------------------
def extract_min_quote(trade_info: dict) -> float:
    if not trade_info or not isinstance(trade_info, dict):
        return 0.0
    candidates = []
    q = trade_info.get('quote')
    if isinstance(q, dict):
        candidates.extend([q.get('min'), q.get('min_quote'), q.get('minNotional')])
    for k in ('min_quote', 'minNotional', 'minOrderValue', 'min_order_value', 'min_notional', 'min'):
        candidates.append(trade_info.get(k))
    for k in ('quoteMin', 'minQuote'):
        candidates.append(trade_info.get(k))
    if 'filters' in trade_info and isinstance(trade_info['filters'], dict):
        f = trade_info['filters']
        candidates.append(f.get('min_quote') or f.get('minNotional'))
    for c in candidates:
        try:
            if c is None:
                continue
            val = float(c)
            if val > 0:
                return val
        except Exception:
            continue
    return 0.0

def place_buy_order(symbol: str, model_price: float, invest_amt: float, available_balance: float, run_summary: dict):
    info = get_trade_info(symbol) or {}
    precision = (info.get("precision") or {"base": 6, "quote": 2})
    min_quote = extract_min_quote(info)

    # Ensure invest_amt meets min_quote or skip
    if min_quote and invest_amt < min_quote:
        if available_balance >= min_quote:
            logging.info("[INFO] Invest amount ₹%.2f < min_quote ₹%.2f. Increasing to min_quote.", invest_amt, min_quote)
            invest_amt = float(min_quote)
        else:
            logging.info("[SKIP] Invest ₹%.2f < required min_quote ₹%.2f and insufficient balance. Skipping %s", invest_amt, min_quote, symbol)
            run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_MIN_QUOTE", "required_min_quote": min_quote, "invest_amt": invest_amt})
            return False, 0.0

    # Determine chosen price using orderbook min ask if available
    min_rate = get_min_rate(symbol)
    chosen_price = model_price
    if min_rate and min_rate > 0:
        chosen_price = min(model_price, min_rate)
    debug_print(f"[DEBUG] chosen_price for {symbol}: {chosen_price} (model {model_price}, min_rate {min_rate})")

    # compute qty and clamp
    try:
        qty = float(invest_amt) / max(chosen_price, 1e-12)
    except Exception:
        logging.error("[ERROR] Invalid chosen_price or invest_amt for %s: price=%s invest=%s", symbol, chosen_price, invest_amt)
        return False, 0.0

    chosen_price, qty = clamp_to_precision(chosen_price, qty, precision)
    notional = chosen_price * qty

    # If rounding dropped notional below min_quote, attempt to bump qty minimally if funds allow
    if min_quote and notional < float(min_quote):
        needed_qty = float(min_quote) / max(chosen_price, 1e-12)
        base_p = int((precision or {}).get("base", 6) or 6)
        increment = 10 ** (-base_p)
        candidate_qty = round(((needed_qty // increment) + 1) * increment, base_p)
        candidate_notional = chosen_price * candidate_qty
        if candidate_notional <= available_balance + 1e-9:
            logging.info("[INFO] Rounding caused notional ₹%.6f < min_quote ₹%.6f; bumping qty to %s", notional, min_quote, candidate_qty)
            qty = candidate_qty
            notional = candidate_notional
        else:
            logging.info("[SKIP] Cannot bump qty to meet min_quote for %s: need ₹%.2f but only ₹%.2f available. Skipping.", symbol, candidate_notional, available_balance)
            run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_MIN_QUOTE_AFTER_ROUNDING", "required_notional": candidate_notional, "available_balance": available_balance})
            return False, 0.0

    # final check: ensure notional <= available_balance
    if notional > available_balance + 1e-9:
        logging.info("[SKIP] Notional ₹%.2f exceeds available balance ₹%.2f for %s. Skipping.", notional, available_balance, symbol)
        run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_INSUFFICIENT_FUNDS", "notional": notional, "available_balance": available_balance})
        return False, 0.0

    payload = {"side": "buy", "symbol": symbol, "type": "limit", "price": float(chosen_price), "quantity": float(qty), "exchange": EXCHANGE}

    logging.info("[ACTION] Placing BUY for %s units of %s at ₹%.8f (notional ₹%.2f)", qty, symbol, chosen_price, notional)

    if DRY_RUN:
        logging.info("[DRY-RUN] Would submit order: %s", json.dumps(payload))
        if DRY_RUN_SAVE:
            try:
                with open(DRY_RUN_SAVE, 'a', encoding='utf-8') as f:
                    json.dump({"timestamp": int(time.time()*1000), "payload": payload, "symbol": symbol, "price": chosen_price, "qty": qty, "notional": notional}, f)
                    f.write("\n")
            except Exception as e:
                logging.error("[ERROR] Could not write dry-run save file: %s", e)
        run_summary['actions'].append({"symbol": symbol, "action": "DRY_RUN", "price": chosen_price, "qty": qty, "notional": notional})
        return True, float(notional)

    if TEST_ORDER:
        logging.info("[TEST] Reducing quantity using TEST_ORDER_AMOUNT")
        try:
            base_p = int(precision.get("base", 6))
            qty = max(0.000001, TEST_ORDER_AMOUNT / max(chosen_price, 1e-9))
            payload['quantity'] = float(round(qty, base_p))
            notional = payload['quantity'] * chosen_price
        except Exception:
            pass

    if not AUTO_YES:
        resp = input(f"Confirm placing BUY order for {payload['quantity']} {symbol} at ₹{payload['price']:.2f}? (y/N): ").strip().lower()
        if resp != 'y':
            logging.info("[SKIP] Order cancelled by user.")
            run_summary['actions'].append({"symbol": symbol, "action": "USER_CANCELLED", "price": chosen_price, "qty": qty, "notional": notional})
            return False, 0.0

    res = safe_post_resign("/trade/api/v2/order", params=None, payload=payload)
    if res is None:
        logging.error("[ERROR] Order placement ultimately failed after retries for %s", symbol)
        run_summary['actions'].append({"symbol": symbol, "action": "FAILED", "price": chosen_price, "qty": qty, "notional": notional})
        return False, 0.0

    logging.info("[TRADE] Order submitted successfully: %s", res.text)
    run_summary['actions'].append({"symbol": symbol, "action": "ORDERED", "price": chosen_price, "qty": qty, "notional": notional, "response": (res.json() if res is not None else None)})
    return True, float(notional)

def is_stablecoin_symbol(symbol: str) -> bool:
    sym = symbol.upper()
    return sym.startswith("USDT/") or sym.startswith("USDC/") or sym.startswith("BUSD/") or sym.startswith("FDUSD/")

# -------------------- Main bot logic --------------------
def run_ml_trading_bot():
    if not API_KEY or not SECRET_KEY:
        print("[ERROR] API_KEY and SECRET_KEY must be set.")
        return

    start_balance = get_inr_balance()
    run_summary = {
        "start_balance": start_balance,
        "end_balance": None,
        "timestamp": int(time.time()*1000),
        "predictions": [],
        "actions": [],
        "config": {
            "auth_sig": AUTH_SIG,
            "sign_body": AUTH_SIGN_BODY,
            "dry_run": DRY_RUN,
            "dry_run_save": DRY_RUN_SAVE,
            "summary_save": SUMMARY_SAVE,
            "max_coins": MAX_COINS_TO_PROCESS
        }
    }

    print("[START] ML Trading Bot v2.10 Initialized.")
    print(f"[INFO] Lookback window: {LOOKBACK_DAYS} days | Interval: {CANDLE_INTERVAL_MIN} minutes")
    print(f"[INFO] Auth mode: {AUTH_SIG} | Sign body: {AUTH_SIGN_BODY} | Dry-run-save: {DRY_RUN_SAVE}")
    print(f"[INFO] INR Balance: ₹{start_balance:.2f}")
    if start_balance < 100:
        print("[STOP] Balance too low.")
        return

    candidates = SYMBOLS_OVERRIDE if SYMBOLS_OVERRIDE else get_top_symbols_by_volume()
    if not candidates:
        print("[STOP] Could not fetch top symbols.")
        return

    active_symbols = get_open_order_symbols() if SKIP_ACTIVE else set()
    if SKIP_ACTIVE and active_symbols:
        logging.info("[INFO] Symbols with open orders (skipping): %s", sorted(active_symbols))

    print(f"[INFO] Top symbols: {candidates}")
    available_balance = start_balance

    for symbol in candidates:
        if not INCLUDE_STABLES and is_stablecoin_symbol(symbol):
            logging.info("[SKIP] Skipping stablecoin pair %s", symbol)
            run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_STABLE"})
            continue
        if SKIP_ACTIVE and symbol in active_symbols:
            logging.info("[SKIP] %s has an active/open order; skipping this run.", symbol)
            run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_ACTIVE_ORDER"})
            continue

        print(f"\n--- Analyzing {symbol} ---")
        prediction, price = train_and_predict(symbol)
        run_summary['predictions'].append({"symbol": symbol, "prediction": prediction, "price": None if pd.isna(price) else float(price)})
        if pd.isna(price):
            print(f"[PREDICTION] {symbol}: {prediction} (price unavailable)")
            run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_NO_PRICE"})
            continue
        print(f"[PREDICTION] {symbol}: {prediction} at ₹{price:.2f}")

        if prediction == 'BUY' and available_balance > 100 and not pd.isna(price):
            invest_amt = available_balance * TRADE_PERCENT_OF_BALANCE

            # fetch tradeInfo early to check min_quote quickly
            info_for_symbol = get_trade_info(symbol) or {}
            min_quote = extract_min_quote(info_for_symbol)
            if min_quote and invest_amt < min_quote:
                if available_balance >= min_quote:
                    logging.info("[INFO] Increasing invest amount to min_quote ₹%.2f for %s", min_quote, symbol)
                    invest_amt = float(min_quote)
                else:
                    logging.info("[SKIP] Invest amount ₹%.2f < required min_quote ₹%.2f and insufficient balance. Skipping %s", invest_amt, min_quote, symbol)
                    run_summary['actions'].append({"symbol": symbol, "action": "SKIPPED_MIN_QUOTE", "required_min_quote": min_quote, "available_balance": available_balance})
                    continue

            ok, spent = place_buy_order(symbol, price, invest_amt, available_balance, run_summary)
            if ok and not DRY_RUN:
                available_balance -= spent
        else:
            run_summary['actions'].append({"symbol": symbol, "action": "NO_BUY_DECISION", "prediction": prediction, "price": price})

        time.sleep(2)

    end_balance = get_inr_balance()
    run_summary['end_balance'] = end_balance
    run_summary['finished_at'] = int(time.time()*1000)

    print(f"\n[INFO] Start balance: ₹{start_balance:.2f} | End balance: ₹{end_balance:.2f}")
    print("\n[DONE] Bot completed its run.")

    if SUMMARY_SAVE:
        try:
            with open(SUMMARY_SAVE, 'w', encoding='utf-8') as f:
                json.dump(run_summary, f, indent=2)
            logging.info("[INFO] Summary saved to %s", SUMMARY_SAVE)
        except Exception as e:
            logging.error("[ERROR] Could not write summary file: %s", e)

if __name__ == "__main__":
    run_ml_trading_bot()
