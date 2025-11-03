# CoinSwitch PRO - Automated ML Trading Bot Project v2.0

# [
#   source: 2128
# ] CoinSwitch Crypto Aggregator  Platform
# CoinSwitch PRO API Trading - Terms & Conditions  1. These Application Programming Interface (API) License Terms and Conditions (“API Terms”)
# shall govern the use of the API of CoinSwitch for the users of CoinSwitch PRO to undertake various trades (“Services”) by Users who fulfill the Eligibility
# Criteria stated in the Terms of Use  (the “Terms”) and these API Terms.

import os
import time
import json
import requests
import urllib
import pandas as pd
from urllib.parse import urlencode, urlparse
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

import sys
import logging

# Flags
DEBUG = '--debug' in sys.argv
DRY_RUN = '--dry-run' in sys.argv
AUTO_YES = '--yes' in sys.argv
LAST_SIGN = {}
LAST_REQUEST = {}

# Test / tuning flags (simple parsing to avoid moving to argparse)
TEST_ORDER = '--test-order' in sys.argv
# default test amount in INR
TEST_ORDER_AMOUNT = 10.0
for a in sys.argv:
    if a.startswith('--test-amount='):
        try:
            TEST_ORDER_AMOUNT = float(a.split('=', 1)[1])
        except Exception:
            pass

# Minimum historical rows required to train the model (can be overridden with --min-rows=N)
MIN_HISTORICAL_ROWS = 200
for a in sys.argv:
    if a.startswith('--min-rows='):
        try:
            MIN_HISTORICAL_ROWS = int(a.split('=', 1)[1])
        except Exception:
            pass

# Diagnostic dump flag: --dump-symbol=SYMBOL
DUMP_SYMBOL = None
for a in sys.argv:
    if a.startswith('--dump-symbol='):
        DUMP_SYMBOL = a.split('=', 1)[1]

# Dump the POST request headers/body instead of sending (safe diagnostic)
DUMP_POST = '--dump-post' in sys.argv

# Optional trial order_id for diagnostics: --trial-order-id=<id>
TRIAL_ORDER_ID = None
for a in sys.argv:
    if a.startswith('--trial-order-id='):
        TRIAL_ORDER_ID = a.split('=', 1)[1]

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='[%(levelname)s] %(message)s'
)

# --- CONFIGURATION ---
# I'm using environment variables for security.
# export API_KEY="your_api_key_here"
# export SECRET_KEY="your_secret_key_here"
API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
BASE_URL = "https://coinswitch.co"
EXCHANGE = "coinswitchx"
SYMBOL_SUFFIX = "/INR"
TRADE_PERCENT_OF_BALANCE = 0.25 # Use 25% of balance per trade to diversify
REQUEST_TIMEOUT = 10
MAX_COINS_TO_PROCESS = 5 # Focus on the top 5 coins by volume for speed
HISTORICAL_DAYS = 365 # Days of data to train the model on

# --- API & AUTHENTICATION UTILS (UNCHANGED) ---
def safe_get(url, headers, params=None):
    """A wrapper for requests to handle retries on network errors."""
    retries = 3
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            res.raise_for_status()
            return res
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {e}")
            # On debug, print server response and last sign/request info
            if DEBUG and hasattr(e, 'response') and e.response is not None:
                resp = e.response
                print('[DEBUG] Response status:', getattr(resp, 'status_code', None))
                try:
                    print('[DEBUG] Response body:', resp.text)
                except Exception:
                    pass
                print('[DEBUG] Last signed message:', LAST_SIGN.get('message'))
                print('[DEBUG] Last signature:', LAST_SIGN.get('signature'))
                print('[DEBUG] Last request headers:', LAST_REQUEST.get('headers'))
                print('[DEBUG] Last request url:', LAST_REQUEST.get('url'))
            time.sleep(2)
    print("[ERROR] All retry attempts failed for:", url)
    return None

def get_server_time():
    """Gets the official server time to sync our requests."""
    # [cite: 13, 127] This endpoint provides the server time.
    res = safe_get(f"{BASE_URL}/trade/api/v2/time", headers={})
    if res:
        return str(res.json().get("serverTime", str(int(time.time() * 1000))))
    return str(int(time.time() * 1000))


# Removed debug helper functions to reduce noise. Use --debug to print the canonical message/signature in generate_signature.


def generate_signature(method, endpoint, params, body, epoch_time):
    """Creates the unique signature required for authenticated API calls."""
    method_u = method.upper()
    # Normalize/unquote the endpoint path consistently for all methods
    endpoint_unquoted = urllib.parse.unquote_plus(endpoint)
    # For all methods, canonicalize the path using unquote_plus and sign: METHOD + UNQUOTED_PATH + EPOCH
    # The server expects signatures that do NOT include the request body even for POST/DELETE.
    query = ('?' + urlencode(params) if params else "")
    message_to_sign = method + urllib.parse.unquote_plus(endpoint + query) + epoch_time
    # Keep body handling separate; body is sent with the request but not part of the signed string
    body_string = json.dumps(body, separators=(',', ':'), sort_keys=True) if body is not None else ""
    request_string = message_to_sign.encode('utf-8')

    # Save non-secret debug info
    LAST_SIGN['message'] = message_to_sign
    # Keep epoch separately for headers/debug; it may not be part of the signed string for POSTs
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
        print('[DEBUG] Signature (base64):', LAST_SIGN.get('signature_b64'))

    return signature

def get_headers(method, endpoint, params=None, body=None):
    """Prepares the required headers for an authenticated API call."""
    epoch_time = get_server_time()
    signature = generate_signature(method, endpoint, params, body, epoch_time)
    # The API expects the signature as a hex string (documentation examples use .hex())
    signature_value = signature
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature_value,
        'X-AUTH-EPOCH': epoch_time
    }
    # store request metadata for debugging
    LAST_REQUEST['method'] = method
    LAST_REQUEST['endpoint'] = endpoint
    LAST_REQUEST['params'] = params
    LAST_REQUEST['body'] = body
    LAST_REQUEST['headers'] = {k: v for k, v in headers.items()}
    LAST_REQUEST['url'] = BASE_URL + endpoint

    return headers, BASE_URL + endpoint

# --- CORE TRADING LOGIC ---
def get_inr_balance():
    """Fetches the available INR balance from my portfolio."""
    # [cite: 30, 1001] This endpoint provides portfolio and balance information.
    endpoint = "/trade/api/v2/user/portfolio"
    headers, url = get_headers("GET", endpoint)
    res = safe_get(url, headers)
    if not res: return 0
    for item in res.json().get("data", []):
        if item.get("currency", "").lower() == "inr":
            return float(item.get("main_balance", 0))
    return 0

def get_top_symbols_by_volume():
    """Gets a list of the most actively traded coins."""
    #  This endpoint gets 24hr data for all pairs.
    endpoint = "/trade/api/v2/24hr/all-pairs/ticker"
    params = {"exchange": EXCHANGE}
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params=params)
    if not res: return []
    all_pairs = res.json().get("data", {})
    inr_pairs = [v for k, v in all_pairs.items() if k.endswith(SYMBOL_SUFFIX) and float(v.get("quoteVolume", 0)) > 0]
    # [cite: 1266] Sorting by quoteVolume to find the most active markets.
    inr_pairs.sort(key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
    return [coin['symbol'] for coin in inr_pairs[:MAX_COINS_TO_PROCESS]]

def get_historical_data(symbol):
    """Fetches daily candle data for the last year.

    Strategy:
    - Try daily candles first (interval=1440).
    - If daily data is missing or very sparse, fetch hourly candles (interval=60)
      and resample to daily OHLCV.
    - Normalize several response shapes returned by the API.
    """
    logging.info("Fetching %d days of historical data for %s...", HISTORICAL_DAYS, symbol)
    endpoint = "/trade/api/v2/candles"
    end_time = int(time.time() * 1000)
    start_time = end_time - (HISTORICAL_DAYS * 24 * 60 * 60 * 1000)

    def _fetch(interval_minutes):
        params = {
            "symbol": symbol,
            "exchange": EXCHANGE,
            "interval": str(interval_minutes),
            "start_time": start_time,
            "end_time": end_time,
        }
        headers, url = get_headers("GET", endpoint, params=params)
        res = safe_get(url, headers, params=params)
        if not res:
            return []
        try:
            body = res.json()
        except Exception:
            logging.debug("Failed to parse JSON from candles response for %s (interval=%s)", symbol, interval_minutes)
            return []

        # body may be {'data': {...}} or {'data': [...]} or a list
        maybe = body.get('data', body) if isinstance(body, dict) else body
        data = []
        if isinstance(maybe, dict):
            # maybe is a mapping of symbol -> list
            data = maybe.get(symbol) or []
        elif isinstance(maybe, list):
            data = maybe
        else:
            logging.debug("Unexpected candles structure for %s: %s", symbol, type(maybe))
            data = []

        # Convert list-of-dicts to list-of-lists, mapping common key names
        if data and isinstance(data[0], dict):
            converted = []
            for item in data:
                try:
                    # timestamp may be 'timestamp', 'start_time', or 'close_time'
                    ts = item.get('timestamp') or item.get('start_time') or item.get('close_time') or item.get('t')
                    # open/high/low/close may be abbreviated 'o','h','l','c' or full names
                    o = item.get('o') or item.get('open') or item.get('openPrice') or item.get('open_price')
                    h = item.get('h') or item.get('high') or item.get('highPrice') or item.get('high_price')
                    l = item.get('l') or item.get('low') or item.get('lowPrice') or item.get('low_price')
                    c = item.get('c') or item.get('close') or item.get('closePrice') or item.get('close_price')
                    v = item.get('volume') or item.get('v') or item.get('baseVolume') or item.get('quoteVolume')
                    converted.append([ts, o, h, l, c, v])
                except Exception:
                    continue
            data = converted

        return data

    # Try daily candles first
    data = _fetch(1440)
    logging.debug("Daily candles returned for %s: %d rows", symbol, len(data))
    # Diagnostic: show first/last few rows if present
    if data:
        try:
            logging.debug("Sample candle (first): %s", data[0])
            logging.debug("Sample candle (last): %s", data[-1])
        except Exception:
            pass

    # If we don't have enough daily rows, try hourly and resample
    if not data or len(data) < 10:
        logging.info("Falling back to hourly candles for %s to resample to daily", symbol)
        hourly = _fetch(60)
        logging.debug("Hourly candles returned for %s: %d rows", symbol, len(hourly))
        if not hourly:
            return pd.DataFrame()
        try:
            hdf = pd.DataFrame(hourly, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            hdf['timestamp'] = pd.to_datetime(hdf['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                hdf[col] = pd.to_numeric(hdf[col], errors='coerce')
            hdf.set_index('timestamp', inplace=True)
            ddf = hdf.resample('D').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna()
            if ddf.empty:
                return pd.DataFrame()
            ddf = ddf.reset_index()
            ddf['timestamp'] = (ddf['timestamp'].astype('int64') // 1_000_000)
            df = ddf[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except Exception:
            logging.debug("Failed to convert hourly candles to daily for %s", symbol)
            return pd.DataFrame()
    else:
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def get_current_price(symbol):
    """Fetch a current/last price for a symbol from the 24hr ticker as a fallback."""
    endpoint = "/trade/api/v2/24hr/all-pairs/ticker"
    params = {"exchange": EXCHANGE}
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params=params)
    if not res:
        return None
    try:
        body = res.json()
    except Exception:
        return None
    data = body.get('data', {}) if isinstance(body, dict) else {}
    # The keys in the data might be symbol strings; try direct lookup
    entry = data.get(symbol) or {}
    # Try common fields where last/close price may appear
    for key in ('lastPrice', 'last', 'close', 'price'):
        val = entry.get(key)
        if val is not None:
            try:
                return float(val)
            except Exception:
                continue
    # Some providers use nested structures; try to find any numeric in the dict
    if isinstance(entry, dict):
        for v in entry.values():
            try:
                return float(v)
            except Exception:
                continue
    return None


def dump_api_samples(symbol):
    """Fetch and log trimmed JSON samples for candles (daily/hourly) and ticker for diagnosis."""
    logging.info("Dumping API samples for %s", symbol)
    endpoint = "/trade/api/v2/candles"
    end_time = int(time.time() * 1000)
    start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # one week

    def _call_candles(interval):
        params = {"symbol": symbol, "exchange": EXCHANGE, "interval": str(interval), "start_time": start_time, "end_time": end_time}
        headers, url = get_headers("GET", endpoint, params=params)
        res = safe_get(url, headers, params=params)
        if not res:
            logging.info("No response for candles interval %s", interval)
            return
        try:
            body = res.json()
            # Print a trimmed version
            snippet = json.dumps(body)[:2000]
            logging.info("Candles interval %s snippet: %s", interval, snippet)
        except Exception as e:
            logging.info("Failed to dump candles JSON for %s interval %s: %s", symbol, interval, e)

    _call_candles(1440)
    _call_candles(60)

    # Ticker
    endpoint2 = "/trade/api/v2/24hr/all-pairs/ticker"
    headers, url = get_headers("GET", endpoint2, params={"exchange": EXCHANGE})
    res = safe_get(url, headers, params={"exchange": EXCHANGE})
    if not res:
        logging.info("No response for ticker")
        return
    try:
        body = res.json()
        snippet = json.dumps(body.get('data', {} if isinstance(body, dict) else body))[:2000]
        logging.info("Ticker snippet: %s", snippet)
    except Exception as e:
        logging.info("Failed to dump ticker JSON: %s", e)

def calculate_features(df):
    """Calculates technical indicators to be used as features for the ML model."""
    print("[INFO] Calculating technical features (SMA, RSI)...")
    df['SMA_10'] = df['close'].rolling(window=10).mean() # 10-day Simple Moving Average
    df['SMA_30'] = df['close'].rolling(window=30).mean() # 30-day Simple Moving Average
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs)) # 14-day Relative Strength Index
    df.dropna(inplace=True)
    return df

def create_labels(df, look_ahead=7, threshold=0.03):
    """Creates the target labels (BUY, SELL, HOLD) for training."""
    print("[INFO] Generating BUY/SELL/HOLD labels for training data...")
    df['future_price'] = df['close'].shift(-look_ahead)
    df['price_change'] = (df['future_price'] - df['close']) / df['close']
    
    def get_label(change):
        if change > threshold: return 'BUY'
        elif change < -threshold: return 'SELL'
        else: return 'HOLD'
        
    df['label'] = df['price_change'].apply(get_label)
    df.dropna(inplace=True)
    return df

def train_and_predict(symbol):
    """Trains a model for a symbol and predicts the next action."""
    df = get_historical_data(symbol)
    if df.empty:
        return "HOLD", 0.0
    if len(df) < MIN_HISTORICAL_ROWS:
        logging.warning("Not enough historical rows for %s: %d (need %d)", symbol, len(df), MIN_HISTORICAL_ROWS)
        return "HOLD", float('nan')
    
    df_features = calculate_features(df.copy())
    df_labeled = create_labels(df_features.copy())

    if df_labeled.empty:
        print("[WARNING] Not enough data to create labels and train model.")
        return "HOLD", df['close'].iloc[-1]
    
    # Defining my features (X) and target (y)
    features = ['SMA_10', 'SMA_30', 'RSI']
    X = df_labeled[features]
    y = df_labeled['label']
    
    # Splitting data for training and testing (good practice for model evaluation)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Using a RandomForestClassifier - it's a solid choice for this kind of problem
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print(f"[INFO] Model for {symbol} trained. Accuracy: {model.score(X_test, y_test):.2f}")
    
    # Predicting the action for the most recent data point
    latest_features = df_features[features].iloc[-1:].values
    prediction = model.predict(latest_features)[0]
    current_price = df_features['close'].iloc[-1]
    
    return prediction, current_price

def place_buy_order(symbol, price, qty):
    """Submits a limit buy order to the exchange."""
    logging.info("[ACTION] Placing BUY order for %s of %s at ~₹%.2f", qty, symbol, price)
    # [cite: 25, 675] The endpoint for creating a new order.
    endpoint = "/trade/api/v2/order"
    payload = { "side": "buy", "symbol": symbol, "type": "limit", "price": price, "quantity": qty, "exchange": EXCHANGE }
    # Inject a trial order_id if requested for diagnostics (will be included in dry-run dumps)
    if TRIAL_ORDER_ID:
        payload['order_id'] = TRIAL_ORDER_ID
    headers, url = get_headers("POST", endpoint, body=payload)

    # For live sends (not dry-run and not dump), ensure an order_id is present for idempotency
    if not DRY_RUN and not DUMP_POST:
        try:
            import uuid
            if TRIAL_ORDER_ID:
                payload['order_id'] = TRIAL_ORDER_ID
            else:
                payload.setdefault('order_id', str(uuid.uuid4()))
        except Exception:
            pass

    # Honor dry-run mode: log the payload but do not send any network requests
    if DRY_RUN:
        logging.info("[DRY-RUN] Would submit order to %s with payload: %s", url, json.dumps(payload))
        return

    # If debugging dump of the POST was requested, print exact diagnostic info and do not send
    if DUMP_POST:
        logging.info("[DUMP-POST] URL: %s", url)
        logging.info("[DUMP-POST] Headers: %s", json.dumps(headers))
        logging.info("[DUMP-POST] Payload: %s", json.dumps(payload, separators=(',', ':'), sort_keys=True))
        logging.info("[DUMP-POST] Canonical message used for signing: %s", LAST_SIGN.get('message'))
        logging.info("[DUMP-POST] Epoch header: %s", LAST_SIGN.get('epoch'))
        logging.info("[DUMP-POST] Signature (hex): %s", LAST_SIGN.get('signature'))
        return

    # Prompt for confirmation unless the user passed --yes
    if not AUTO_YES:
        try:
            resp = input(f"Confirm placing BUY order for {qty} {symbol} at ~₹{price:.2f}? (y/N): ").strip().lower()
        except Exception:
            resp = 'n'
        if resp != 'y':
            logging.info("[SKIP] Order cancelled by user.")
            return

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        try:
            logging.info("[TRADE] Order submitted successfully: %s", res.json())
        except Exception:
            logging.info("[TRADE] Order submitted successfully. (response parsing failed)")
    except requests.exceptions.RequestException as e:
        logging.error("[ERROR] Order placement failed for %s: %s", symbol, e)
        if getattr(e, 'response', None) is not None:
            try:
                logging.debug("Response body: %s", e.response.text)
            except Exception:
                pass

# --- MAIN SCRIPT EXECUTION ---
def run_ml_trading_bot():
    """Main function to run the bot's logic."""
    if not API_KEY or not SECRET_KEY:
        print("[ERROR] API_KEY and SECRET_KEY must be set as environment variables.")
        return

    print("[START] ML Trading Bot v2.0 Initializing...")
    if DEBUG:
        logging.debug("Debug mode enabled. LAST_SIGN: %s", LAST_SIGN)
        # Provide a lightweight sample signature run for quick inspection without calling removed helpers
        try:
            _ = generate_signature("GET", "/trade/api/v2/user/portfolio", None, None, get_server_time())
            logging.debug("Sample signature created. Message: %s", LAST_SIGN.get('message'))
        except Exception as e:
            logging.debug("Could not generate sample signature: %s", e)
    # If user requested API sample dump, do it and exit
    if DUMP_SYMBOL:
        dump_api_samples(DUMP_SYMBOL)
        return
    available_balance = get_inr_balance()
    print(f"[INFO] Current INR Balance: ₹{available_balance:.2f}")

    if available_balance < 100: # Need a reasonable balance to start
        print("[STOP] Balance is too low to execute trades. Exiting.")
        return
        
    top_symbols = get_top_symbols_by_volume()
    if not top_symbols:
        print("[STOP] Could not fetch top symbols. Exiting.")
        return
        
    print(f"[INFO] Top symbols by volume: {top_symbols}")

    for symbol in top_symbols:
        print(f"\n--- Analyzing {symbol} ---")
        prediction, price = train_and_predict(symbol)
        print(f"[PREDICTION] The ML model predicts: **{prediction}** for {symbol} at price ₹{price:.2f}")
        
        if prediction == 'BUY':
            if available_balance > 100: # Final check on balance
                investment_amount = available_balance * TRADE_PERCENT_OF_BALANCE
                quantity_to_buy = round(investment_amount / price, 6) # Using a generic precision
                place_buy_order(symbol, price, quantity_to_buy)
                available_balance -= investment_amount # Update balance to avoid over-spending
            else:
                print("[SKIP] Predicted BUY, but remaining balance is too low.")

        # If user requested a forced test-order, place a tiny order for the first symbol that is tradable
        if TEST_ORDER:
            logging.info("--test-order flag detected. Preparing a small test order of ₹%s", TEST_ORDER_AMOUNT)
            # Use price if available, otherwise skip
            if not price or not (price > 0):
                logging.warning("Skipping test-order for %s due to invalid price: %s", symbol, price)
            else:
                # If price is NaN or falsy, attempt ticker fallback
                if not price or not (price > 0):
                    fallback = get_current_price(symbol)
                    if fallback and fallback > 0:
                        logging.info("Using ticker fallback price %s for %s", fallback, symbol)
                        price = fallback
                    else:
                        logging.warning("Skipping test-order for %s due to invalid price: %s", symbol, price)
                        continue
                test_qty = round(TEST_ORDER_AMOUNT / price, 6)
                logging.info("Test order: %s INR => qty %s at price %s", TEST_ORDER_AMOUNT, test_qty, price)
                place_buy_order(symbol, price, test_qty)
                # Only run one test order
                break
        time.sleep(2) # Pause between analyzing coins

    print("\n[DONE] Bot has completed its run.")

if __name__ == "__main__":
    run_ml_trading_bot()