"""
CoinSwitch PRO - Automated ML Trading Bot v2.1
------------------------------------------------
Features:
✅ Handles HTTP 423 (Locked) gracefully — auto-retries or pauses.
✅ Compatible with CoinSwitch PRO API terms.
✅ Uses RandomForestClassifier to make BUY/SELL/HOLD predictions.
✅ Includes --debug, --dry-run, and test flags.

Usage:
    python coinswitch_ml_trading_bot_v2.1.py [--debug] [--dry-run] [--test-order]
Dependencies:
    pip install requests pandas numpy scikit-learn cryptography
"""

import os
import time
import json
import requests
import urllib
import pandas as pd
from urllib.parse import urlencode
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import sys
import logging

# --------------------------------------------------------------
# Flags and configuration
# --------------------------------------------------------------
DEBUG = '--debug' in sys.argv
DRY_RUN = '--dry-run' in sys.argv
AUTO_YES = '--yes' in sys.argv
TEST_ORDER = '--test-order' in sys.argv
LAST_SIGN, LAST_REQUEST = {}, {}

TEST_ORDER_AMOUNT = 10.0
for a in sys.argv:
    if a.startswith('--test-amount='):
        try: TEST_ORDER_AMOUNT = float(a.split('=', 1)[1])
        except Exception: pass

MIN_HISTORICAL_ROWS = 200
for a in sys.argv:
    if a.startswith('--min-rows='):
        try: MIN_HISTORICAL_ROWS = int(a.split('=', 1)[1])
        except Exception: pass

DUMP_SYMBOL = None
for a in sys.argv:
    if a.startswith('--dump-symbol='): DUMP_SYMBOL = a.split('=', 1)[1]

DUMP_POST = '--dump-post' in sys.argv
TRIAL_ORDER_ID = None
for a in sys.argv:
    if a.startswith('--trial-order-id='): TRIAL_ORDER_ID = a.split('=', 1)[1]

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='[%(levelname)s] %(message)s')

API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
BASE_URL = "https://coinswitch.co"
EXCHANGE = "coinswitchx"
SYMBOL_SUFFIX = "/INR"
TRADE_PERCENT_OF_BALANCE = 0.25
REQUEST_TIMEOUT = 10
MAX_COINS_TO_PROCESS = 15
HISTORICAL_DAYS = 365

# --------------------------------------------------------------
# Helper: Detect 423 Locked
# --------------------------------------------------------------
def is_locked_response(resp):
    """Detects if the response is a 423 Locked error and logs its meaning."""
    if not resp:
        return False
    if getattr(resp, "status_code", None) == 423:
        print("[ERROR] 423 Locked: The resource or account is temporarily unavailable.")
        print("🕒 Likely causes: rate limit, maintenance, or account lock.")
        print("✅ Action: waiting 30 s before retry...")
        time.sleep(30)
        return True
    return False


# --------------------------------------------------------------
# Safe GET with retries + 423 handling
# --------------------------------------------------------------
def safe_get(url, headers, params=None):
    retries = 3
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            if is_locked_response(res):
                continue
            res.raise_for_status()
            return res
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
            if DEBUG and hasattr(e, 'response') and e.response is not None:
                resp = e.response
                print('[DEBUG] Response status:', getattr(resp, 'status_code', None))
                try: print('[DEBUG] Response body:', resp.text)
                except Exception: pass
                print('[DEBUG] Last signed message:', LAST_SIGN.get('message'))
                print('[DEBUG] Last signature:', LAST_SIGN.get('signature'))
                print('[DEBUG] Last request headers:', LAST_REQUEST.get('headers'))
                print('[DEBUG] Last request url:', LAST_REQUEST.get('url'))
            time.sleep(2)
    print("[ERROR] All retry attempts failed for:", url)
    return None


def get_server_time():
    res = safe_get(f"{BASE_URL}/trade/api/v2/time", headers={})
    if res:
        return str(res.json().get("serverTime", str(int(time.time() * 1000))))
    return str(int(time.time() * 1000))


def generate_signature(method, endpoint, params, body, epoch_time):
    method_u = method.upper()
    endpoint_unquoted = urllib.parse.unquote_plus(endpoint)
    query = ('?' + urlencode(params) if params else "")
    message_to_sign = method + urllib.parse.unquote_plus(endpoint + query) + epoch_time
    body_string = json.dumps(body, separators=(',', ':'), sort_keys=True) if body is not None else ""
    request_string = message_to_sign.encode('utf-8')

    LAST_SIGN['message'] = message_to_sign
    LAST_SIGN['epoch'] = epoch_time

    secret_bytes = bytes.fromhex(SECRET_KEY)
    key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
    signature_bytes = key.sign(request_string)
    signature = signature_bytes.hex()
    signature_b64 = base64.b64encode(signature_bytes).decode()
    LAST_SIGN['signature'] = signature
    LAST_SIGN['signature_b64'] = signature_b64
    if DEBUG:
        print('[DEBUG] Message to sign:', LAST_SIGN['message'])
        print('[DEBUG] Signature (hex):', LAST_SIGN['signature'])
    return signature


def get_headers(method, endpoint, params=None, body=None):
    epoch_time = get_server_time()
    signature = generate_signature(method, endpoint, params, body, epoch_time)
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature,
        'X-AUTH-EPOCH': epoch_time
    }
    LAST_REQUEST.update({'method': method, 'endpoint': endpoint, 'params': params,
                         'body': body, 'headers': headers, 'url': BASE_URL + endpoint})
    return headers, BASE_URL + endpoint


# --------------------------------------------------------------
# Core API functions
# --------------------------------------------------------------
def get_inr_balance():
    endpoint = "/trade/api/v2/user/portfolio"
    headers, url = get_headers("GET", endpoint)
    res = safe_get(url, headers)
    if not res:
        return 0
    for item in res.json().get("data", []):
        if item.get("currency", "").lower() == "inr":
            return float(item.get("main_balance", 0))
    return 0


def get_top_symbols_by_volume():
    endpoint = "/trade/api/v2/24hr/all-pairs/ticker"
    params = {"exchange": EXCHANGE}
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params=params)
    if not res:
        return []
    all_pairs = res.json().get("data", {})
    inr_pairs = [v for k, v in all_pairs.items() if k.endswith(SYMBOL_SUFFIX) and float(v.get("quoteVolume", 0)) > 0]
    inr_pairs.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
    return [coin['symbol'] for coin in inr_pairs[:MAX_COINS_TO_PROCESS]]


# --------------------------------------------------------------
# Historical data fetch
# --------------------------------------------------------------
def get_historical_data(symbol):
    logging.info("Fetching %d days of historical data for %s...", HISTORICAL_DAYS, symbol)
    endpoint = "/trade/api/v2/candles"
    end_time = int(time.time() * 1000)
    start_time = end_time - (HISTORICAL_DAYS * 24 * 60 * 60 * 1000)

    def _fetch(interval_minutes):
        params = {"symbol": symbol, "exchange": EXCHANGE, "interval": str(interval_minutes),
                  "start_time": start_time, "end_time": end_time}
        headers, url = get_headers("GET", endpoint, params=params)
        res = safe_get(url, headers, params=params)
        if not res:
            return []
        if is_locked_response(res):  # handles any mid-loop locks
            return []
        try:
            body = res.json()
        except Exception:
            return []
        maybe = body.get('data', body) if isinstance(body, dict) else body
        data = []
        if isinstance(maybe, dict):
            data = maybe.get(symbol) or []
        elif isinstance(maybe, list):
            data = maybe
        if data and isinstance(data[0], dict):
            converted = []
            for item in data:
                try:
                    ts = item.get('timestamp') or item.get('start_time') or item.get('close_time') or item.get('t')
                    o = item.get('o') or item.get('open')
                    h = item.get('h') or item.get('high')
                    l = item.get('l') or item.get('low')
                    c = item.get('c') or item.get('close')
                    v = item.get('volume') or item.get('v')
                    converted.append([ts, o, h, l, c, v])
                except Exception:
                    continue
            data = converted
        return data

    data = _fetch(1440)
    if not data or len(data) < 10:
        logging.info("Falling back to hourly candles for %s", symbol)
        hourly = _fetch(60)
        if not hourly:
            return pd.DataFrame()
        hdf = pd.DataFrame(hourly, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        hdf['timestamp'] = pd.to_datetime(hdf['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            hdf[col] = pd.to_numeric(hdf[col], errors='coerce')
        hdf.set_index('timestamp', inplace=True)
        ddf = hdf.resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min',
                                     'close': 'last', 'volume': 'sum'}).dropna()
        if ddf.empty:
            return pd.DataFrame()
        ddf = ddf.reset_index()
        df = ddf[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    else:
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


# --------------------------------------------------------------
# ML feature engineering & prediction
# --------------------------------------------------------------
def calculate_features(df):
    df['SMA_10'] = df['close'].rolling(window=10).mean()
    df['SMA_30'] = df['close'].rolling(window=30).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df.dropna(inplace=True)
    return df


def create_labels(df, look_ahead=7, threshold=0.03):
    df['future_price'] = df['close'].shift(-look_ahead)
    df['price_change'] = (df['future_price'] - df['close']) / df['close']
    df['label'] = df['price_change'].apply(lambda x: 'BUY' if x > threshold else ('SELL' if x < -threshold else 'HOLD'))
    df.dropna(inplace=True)
    return df


def train_and_predict(symbol):
    df = get_historical_data(symbol)
    if df.empty or len(df) < MIN_HISTORICAL_ROWS:
        logging.warning("Not enough data for %s", symbol)
        return "HOLD", float('nan')
    df_features = calculate_features(df.copy())
    df_labeled = create_labels(df_features.copy())
    if df_labeled.empty:
        return "HOLD", df['close'].iloc[-1]
    features = ['SMA_10', 'SMA_30', 'RSI']
    X = df_labeled[features]
    y = df_labeled['label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print(f"[INFO] {symbol} model trained. Accuracy: {model.score(X_test, y_test):.2f}")
    latest_features = df_features[features].iloc[-1:].values
    prediction = model.predict(latest_features)[0]
    price = df_features['close'].iloc[-1]
    return prediction, price


# --------------------------------------------------------------
# Trading actions
# --------------------------------------------------------------
def place_buy_order(symbol, price, qty):
    logging.info("[ACTION] Placing BUY order for %s of %s at ~₹%.2f", qty, symbol, price)
    endpoint = "/trade/api/v2/order"
    payload = {"side": "buy", "symbol": symbol, "type": "limit",
               "price": price, "quantity": qty, "exchange": EXCHANGE}
    headers, url = get_headers("POST", endpoint, body=payload)

    if DRY_RUN:
        logging.info("[DRY-RUN] Would submit order: %s", json.dumps(payload))
        return

    if not AUTO_YES:
        resp = input(f"Confirm placing BUY order for {qty} {symbol} at ₹{price:.2f}? (y/N): ").strip().lower()
        if resp != 'y':
            logging.info("[SKIP] Order cancelled by user.")
            return
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        if is_locked_response(res):
            return
        res.raise_for_status()
        logging.info("[TRADE] Order submitted successfully: %s", res.text)
    except requests.exceptions.RequestException as e:
        logging.error("[ERROR] Order placement failed for %s: %s", symbol, e)
        if getattr(e, 'response', None):
            logging.debug("Response body: %s", e.response.text)


# --------------------------------------------------------------
# Main bot logic
# --------------------------------------------------------------
def run_ml_trading_bot():
    if not API_KEY or not SECRET_KEY:
        print("[ERROR] API_KEY and SECRET_KEY must be set.")
        return

    print("[START] ML Trading Bot v2.1 Initialized.")
    available_balance = get_inr_balance()
    print(f"[INFO] INR Balance: ₹{available_balance:.2f}")
    if available_balance < 100:
        print("[STOP] Balance too low.")
        return

    top_symbols = get_top_symbols_by_volume()
    if not top_symbols:
        print("[STOP] Could not fetch top symbols.")
        return

    print(f"[INFO] Top symbols: {top_symbols}")
    for symbol in top_symbols:
        print(f"\n--- Analyzing {symbol} ---")
        prediction, price = train_and_predict(symbol)
        print(f"[PREDICTION] {symbol}: {prediction} at ₹{price:.2f}")
        if prediction == 'BUY' and available_balance > 100:
            invest_amt = available_balance * TRADE_PERCENT_OF_BALANCE
            qty = round(invest_amt / price, 6)
            place_buy_order(symbol, price, qty)
            available_balance -= invest_amt
        time.sleep(2)

    print("\n[DONE] Bot completed its run.")


if __name__ == "__main__":
    run_ml_trading_bot()
