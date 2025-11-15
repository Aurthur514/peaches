"""
CoinSwitch PRO - Automated ML Trading Bot v3.2 (FUTURES - USDT)
-----------------------------------------------------------------------
Features:
✅ Sets desired leverage before trading (if possible).
✅ Trades only if --trade-amount meets the specific coin's min order value.
✅ No predetermined minimum balance check.
✅ Exclusively for FUTURES trading (USDT pairs).
✅ Opens LONG on BUY, opens SHORT on SELL (if no opposing position exists).
✅ Fetches dynamic trade rules (min qty, precision).
✅ Analyzes 4-Hour chart data.
✅ Automatically places Bracket Orders (Entry, TP, SL).
✅ Robust logging to a rotating file (bot_run_futures.log).
✅ Handles HTTP 423 (Locked) gracefully.

Usage:
    python coinswitch_ml_futures_bot_v3.2.py --trade-amount <USDT> [--leverage <X>] [--tp-percent 5.0] [--sl-percent 2.0] [--debug] [--dry-run] [--yes]
    Example: python coinswitch_ml_futures_bot_v3.2.py --trade-amount 8.5 --leverage 15 --tp-percent 5 --sl-percent 2

Dependencies:
    pip install requests pandas numpy scikit-learn cryptography
"""

import os
import time
import json
import requests
import urllib
import pandas as pd
from urllib.parse import urlencode, urlparse
from cryptography.hazmat.primitives.asymmetric import ed25519
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import sys
import logging
from logging.handlers import RotatingFileHandler
import argparse
import math

# --------------------------------------------------------------
# Flags and configuration
# --------------------------------------------------------------
parser = argparse.ArgumentParser(description="CoinSwitch PRO ML Futures Bot v3.2")
parser.add_argument('--trade-amount', type=float, required=True, help="Fixed USDT amount per trade.")
# --- Correctly defining the --leverage argument ---
parser.add_argument('--leverage', type=int, default=10, help="Desired leverage (e.g., 10 for 10x).")
# --- End fix ---
parser.add_argument('--debug', action='store_true', help="Enable debug logging.")
parser.add_argument('--dry-run', action='store_true', help="Run without executing trades.")
parser.add_argument('--yes', action='store_true', help="Auto-confirm all trade prompts.")
parser.add_argument('--tp-percent', type=float, default=5.0, help="Take Profit percentage.")
parser.add_argument('--sl-percent', type=float, default=2.0, help="Stop Loss percentage.")
# Removed --max-positions from this version for simplicity, can be added back if needed
args = parser.parse_args()


# --- Futures Config ---
API_KEY = os.environ.get("API_KEY"); SECRET_KEY = os.environ.get("SECRET_KEY")
BASE_URL = "https://coinswitch.co"; FUTURES_EXCHANGE = "EXCHANGE_2"; FUTURES_SYMBOL_SUFFIX = "USDT"
REQUEST_TIMEOUT = 12; HISTORICAL_DAYS = 90; CHART_INTERVAL = "240"
MIN_HISTORICAL_ROWS = 100; ML_LOOK_AHEAD = 12; ML_THRESHOLD_PERCENT = 0.03

# Global Cache & State
TRADE_INFO_CACHE = {}; LAST_SIGN, LAST_REQUEST = {}, {}
FEATURE_NAMES = ['SMA_10', 'SMA_30', 'RSI']

if args.trade_amount <= 0: print("Error: --trade-amount must be positive."); sys.exit(1)
if args.leverage <= 0: print("Error: --leverage must be positive."); sys.exit(1)

# --------------------------------------------------------------
# Logging Setup (Unchanged)
# --------------------------------------------------------------
def setup_logging(debug=False):
    logger = logging.getLogger(); logger.setLevel(logging.DEBUG)
    for handler in logger.handlers[:]: logger.removeHandler(handler)
    log_file = "bot_run_futures.log"
    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    fh.setLevel(logging.DEBUG if debug else logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s-%(levelname)s-[%(filename)s:%(lineno)d]-%(message)s'); fh.setFormatter(file_formatter)
    ch = logging.StreamHandler(); ch.setLevel(logging.DEBUG if debug else logging.INFO)
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s'); ch.setFormatter(console_formatter)
    logger.addHandler(fh); logger.addHandler(ch); logging.info(f"Log init FUTURES. File:{log_file}")

# --------------------------------------------------------------
# API Auth & Network Utils (Unchanged)
# --------------------------------------------------------------
def is_locked_response(resp): # Unchanged
    if not resp: return False;
    if getattr(resp, "status_code", None) == 423: logging.error("423 Locked"); logging.info("Wait 30s..."); time.sleep(30); return True
    return False
def _log_request_error(e, method, url): # Unchanged
    logging.error(f"{method} fail: {e}"); response = getattr(e, 'response', None);
    if response is not None: status_code = getattr(response, 'status_code', 'N/A');
    try: resp_text = response.text
    except Exception: resp_text = "(Decode fail)"
    logging.error(f"Status:{status_code}, Resp:{resp_text}");
    if status_code == 400: logging.warning("400 Bad Request - check payload.");
    if status_code == 401: logging.warning("401 Unauthorized - check keys/signature.");
    if status_code == 429: logging.warning("429 Rate Limit - pausing."); time.sleep(10);
    if args.debug: logging.debug(f"URL:{url}"); logging.debug(f"Signed:{LAST_SIGN.get('message')}"); logging.debug(f"Sig:{LAST_SIGN.get('signature')}"); logging.debug(f"Headers:{LAST_REQUEST.get('headers')}")
def safe_get(url, headers, params=None): # Unchanged
    retries=3;
    for attempt in range(retries):
        try: res = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT);
        except requests.exceptions.RequestException as e: _log_request_error(e, "GET", url); time.sleep(attempt + 2); continue
        if is_locked_response(res): time.sleep(attempt + 2); continue
        try: res.raise_for_status(); return res
        except requests.exceptions.RequestException as e: _log_request_error(e, "GET", url); time.sleep(attempt + 2);
    logging.error(f"All GET retries failed: {url}"); return None
def safe_post(url, headers, payload): # Unchanged
    retries=3;
    for attempt in range(retries):
        try: res = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT);
        except requests.exceptions.RequestException as e: _log_request_error(e, "POST", url); time.sleep(attempt + 2); continue
        if is_locked_response(res): time.sleep(attempt + 2); continue
        try: res.raise_for_status(); return res
        except requests.exceptions.RequestException as e: _log_request_error(e, "POST", url); time.sleep(attempt + 2);
    logging.error(f"All POST retries failed: {url}"); return None
def get_server_time(): # Unchanged
    res = safe_get(f"{BASE_URL}/trade/api/v2/time", headers={});
    if res: return str(res.json().get("serverTime", str(int(time.time() * 1000))))
    return str(int(time.time() * 1000))
def generate_signature(method, endpoint, params, body, epoch_time): # Unchanged
    method_u=method.upper(); query=('?' + urlencode(params) if params else ""); path_with_query=endpoint + query; unquoted_path=urllib.parse.unquote_plus(path_with_query); message_to_sign=method_u + unquoted_path + epoch_time; LAST_SIGN['message']=message_to_sign; LAST_SIGN['epoch']=epoch_time; request_string=message_to_sign.encode('utf-8'); secret_bytes=bytes.fromhex(SECRET_KEY); key=ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes); signature_bytes=key.sign(request_string); signature=signature_bytes.hex(); LAST_SIGN['signature']=signature; logging.debug(f"Msg:{message_to_sign},Sig:{signature}"); return signature
def get_headers(method, endpoint, params=None, body=None): # Unchanged
    epoch_time=get_server_time(); signature=generate_signature(method, endpoint, params, body, epoch_time); headers={'Content-Type': 'application/json', 'X-AUTH-APIKEY': API_KEY, 'X-AUTH-SIGNATURE': signature, 'X-AUTH-EPOCH': epoch_time}; LAST_REQUEST.update({'method': method, 'endpoint': endpoint, 'params': params, 'body': body, 'headers': headers, 'url': BASE_URL + endpoint}); return headers, BASE_URL + endpoint

# --------------------------------------------------------------
# Market-Agnostic Helpers (Unchanged)
# --------------------------------------------------------------
def round_to_precision(value, precision): # Unchanged
    if precision >= 0: return round(value, precision)
    else: factor = 10 ** abs(precision); return round(value / factor) * factor
def adjust_quantity_to_step(value, step_size): # Unchanged
    if step_size > 0:
        if value > 0 and value < step_size: return step_size
        return math.floor(value / step_size) * step_size
    return value

# --------------------------------------------------------------
# ML Logic (Unchanged)
# --------------------------------------------------------------
def calculate_features(df): # Unchanged
    df['SMA_10']=df['close'].rolling(window=10).mean(); df['SMA_30']=df['close'].rolling(window=30).mean(); delta=df['close'].diff(); gain=(delta.where(delta > 0, 0)).rolling(window=14).mean(); loss=(-delta.where(delta < 0, 0)).rolling(window=14).mean(); rs=gain / loss; df['RSI']=100 - (100 / (1 + rs)); df.dropna(inplace=True); return df
def create_labels(df, look_ahead=ML_LOOK_AHEAD, threshold=ML_THRESHOLD_PERCENT): # Unchanged
    df['future_price']=df['close'].shift(-look_ahead); df['price_change']=(df['future_price'] - df['close']) / df['close']; df['label']=df['price_change'].apply(lambda x: 'BUY' if x > threshold else ('SELL' if x < -threshold else 'HOLD')); df.dropna(inplace=True); return df
def train_and_predict(symbol, historical_data_df): # Unchanged
    df=historical_data_df;
    if df.empty or len(df) < MIN_HISTORICAL_ROWS: logging.warning(f"Not enough data {symbol}({len(df)}<{MIN_HISTORICAL_ROWS}).Skip train."); return "HOLD", df['close'].iloc[-1] if not df.empty else float('nan')
    df_features=calculate_features(df.copy()); df_labeled=create_labels(df_features.copy());
    if df_labeled.empty: logging.warning(f"Not enough labels {symbol}.Skip train."); return "HOLD", df['close'].iloc[-1] if not df.empty else float('nan')
    X=df_labeled[FEATURE_NAMES]; y=df_labeled['label']; X_train,X_test,y_train,y_test=train_test_split(X, y, test_size=0.2, random_state=42); model=RandomForestClassifier(n_estimators=100, random_state=42); model.fit(X_train, y_train); logging.info(f"{symbol} model trained.Acc:{model.score(X_test, y_test):.2f}"); latest_features_df=pd.DataFrame(df_features[FEATURE_NAMES].iloc[-1:].values, columns=FEATURE_NAMES); prediction=model.predict(latest_features_df)[0]; current_price=df_features['close'].iloc[-1]; return prediction, current_price

# ==============================================================
# FUTURES MARKET LOGIC
# ==============================================================

def get_futures_balance(): # Unchanged
    endpoint="/trade/api/v2/futures/wallet_balance"; headers, url = get_headers("GET", endpoint); res = safe_get(url, headers);
    if not res: return 0; data = res.json().get("data", {});
    for bi in data.get("base_asset_balances", []):
        if bi.get("base_asset") == "USDT": return float(bi.get("balances", {}).get("total_available_balance", 0))
    logging.warning("USDT balance not found."); return 0

def get_futures_symbols_and_prices(): # Unchanged
    endpoint="/trade/api/v2/futures/all-pairs/ticker"; params={"exchange": FUTURES_EXCHANGE}; headers, url = get_headers("GET", endpoint, params=params); res = safe_get(url, headers, params=params);
    if not res: return []; all_pairs_data=res.json().get("data", {}); symbols_prices=[];
    for sd in all_pairs_data.values():
        sym=sd.get("symbol","").upper(); lp_str=sd.get("last_price"); vol_str=sd.get("quote_asset_volume_24h","0");
        if sym.endswith(FUTURES_SYMBOL_SUFFIX) and lp_str and float(vol_str)>0:
            try: lp=float(lp_str)
            except ValueError: continue
            if lp>0: symbols_prices.append({"symbol": sym, "price": lp})
    logging.info(f"Fetched {len(symbols_prices)} FUTURES pairs."); return symbols_prices

def get_futures_trade_info(symbol): # Unchanged
    symbol_upper=symbol.upper();
    if symbol_upper in TRADE_INFO_CACHE:
        if TRADE_INFO_CACHE[symbol_upper] is None: return None
        return TRADE_INFO_CACHE[symbol_upper]
    if not TRADE_INFO_CACHE:
        logging.info("Fetching ALL FUTURES instrument info..."); endpoint="/trade/api/v2/futures/instrument_info"; params={"exchange": FUTURES_EXCHANGE}; headers, url = get_headers("GET", endpoint, params=params); res = safe_get(url, headers, params=params);
        if not res: logging.error("Could not get instrument info."); return None
        try: all_instruments=res.json().get("data",{});
        except json.JSONDecodeError: logging.error("Failed decode instrument info."); return None
        for key, data in all_instruments.items():
             key_upper=key.upper();
             try: info={"min_qty": float(data.get("min_base_quantity")),"qty_precision": int(data.get("quantity_precision")), "qty_step": float(data.get("base_quantity_step_size")),"price_precision": int(data.get("price_precision")), "tick_size": float(10**(-int(data.get("price_precision")))), "max_leverage": int(data.get("max_leverage"))}; TRADE_INFO_CACHE[key_upper]=info # Added max_leverage
             except (TypeError, ValueError, AttributeError) as parse_err: logging.warning(f"Parse error {key_upper}: {parse_err}. Skip cache."); TRADE_INFO_CACHE[key_upper]=None
        logging.info(f"Cached info for {len(TRADE_INFO_CACHE)} instruments.")
    result = TRADE_INFO_CACHE.get(symbol_upper)
    if result is None: logging.warning(f"Trade info {symbol_upper} not found after fetch.")
    return result


def get_futures_historical_data(symbol): # Unchanged
    logging.info(f"Fetching {HISTORICAL_DAYS}d {CHART_INTERVAL}m FUTURES data {symbol}..."); endpoint="/trade/api/v2/futures/klines"; end_time=int(time.time()*1000); start_time=end_time-(HISTORICAL_DAYS*24*60*60*1000); params={"symbol":symbol,"exchange":FUTURES_EXCHANGE,"interval":CHART_INTERVAL,"start_time":start_time,"end_time":end_time,"limit":1000}; headers,url=get_headers("GET",endpoint,params=params); res=safe_get(url,headers,params=params);
    if not res: return pd.DataFrame(); data=res.json().get("data",[]);
    if not data: logging.warning(f"No FUTURES hist data {symbol}."); return pd.DataFrame();
    df=pd.DataFrame(data); df.rename(columns={'start_time':'timestamp','o':'open','h':'high','l':'low','c':'close'},inplace=True); df['timestamp']=pd.to_datetime(df['timestamp'],unit='ms');
    for col in ['open','high','low','close','volume']: df[col]=pd.to_numeric(df[col],errors='coerce');
    df.dropna(subset=['open','high','low','close','volume'],inplace=True); return df[['timestamp','open','high','low','close','volume']]

def get_futures_position(symbol=None): # Modified to fetch all if no symbol
    """Fetches open position(s). If symbol is None, fetches all."""
    logging.debug(f"Fetching position details for {symbol or 'ALL'}...")
    endpoint = "/trade/api/v2/futures/positions" #
    params = {"exchange": FUTURES_EXCHANGE}
    if symbol:
        params["symbol"] = symbol.upper() #
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params=params)
    if not res:
        logging.error(f"Failed to fetch positions for {symbol or 'ALL'}.")
        return None if symbol else [] # Return None for single, empty list for all

    try: # <<< The try block starts here
        positions = res.json().get("data", [])
        active_positions = []
        for pos in positions: # <<< Line 210 in your error
             position_size = float(pos.get("position_size", 0))
             if abs(position_size) > 1e-9: # Check if size is meaningful
                  pos_data = {
                      "symbol": pos.get("symbol", "").upper(),
                      "side": pos.get("position_side", "").upper(),
                      "size": position_size,
                      "entry_price": float(pos.get("avg_entry_price", 0))
                  }
                  if symbol and pos_data["symbol"] == symbol.upper(): # If fetching single, return it
                      logging.info(f"Found active {pos_data['side']} position for {symbol}: Size={position_size}")
                      return pos_data
                  elif not symbol: # If fetching all, add to list
                       active_positions.append(pos_data)

        if symbol: # If fetching single and loop finished without match
            logging.info(f"No active position found for {symbol}.")
            return None
        else: # If fetching all
             logging.info(f"Found {len(active_positions)} total active FUTURES positions.")
             return active_positions

    # --- ADD THIS MISSING BLOCK ---
    except Exception as e:
        logging.error(f"Error parsing position data for {symbol or 'ALL'}: {e}", exc_info=True)
        return None if symbol else []
    # --- END ADDITION ---

def get_futures_order_status(order_id): # Unchanged
    logging.debug(f"Fetch status order:{order_id}..."); endpoint="/trade/api/v2/futures/order"; params={"order_id":order_id,"exchange":FUTURES_EXCHANGE}; headers, url = get_headers("GET", endpoint, params=params); res = safe_get(url, headers, params=params);
    if not res: logging.error(f"Failed fetch status {order_id}."); return None
    try: order_data=res.json().get("data",{}).get("order",{}); status=order_data.get("status"); logging.info(f"Order {order_id} status:{status}"); return status
    except Exception as e: logging.error(f"Error parse status {order_id}:{e}", exc_info=True); return None

# --- NEW: Leverage Functions ---
def get_current_leverage(symbol):
    """Fetches the current leverage for a symbol."""
    logging.debug(f"Fetching leverage for {symbol}...")
    endpoint = "/trade/api/v2/futures/leverage" # [cite: 1808]
    params = {"exchange": FUTURES_EXCHANGE, "symbol": symbol.upper()} # [cite: 1815-1820]
    headers, url = get_headers("GET", endpoint, params=params)
    res = safe_get(url, headers, params=params)
    if not res:
        logging.error(f"Failed to fetch leverage for {symbol}.")
        return None
    try:
        # Response: {"data": {"exchange": "EXCHANGE_2", "symbol": "BTCUSDT", "leverage": "13"}} [cite: 1847-1849]
        leverage_str = res.json().get("data", {}).get("leverage")
        if leverage_str:
             current_lev = int(leverage_str)
             logging.info(f"Current leverage for {symbol}: {current_lev}x")
             return current_lev
        else:
             logging.warning(f"Leverage data not found in response for {symbol}.")
             return None
    except Exception as e:
        logging.error(f"Error parsing leverage for {symbol}: {e}", exc_info=True)
        return None

def set_leverage(symbol, leverage, max_leverage):
    """Attempts to set the leverage, respecting max_leverage."""
    target_leverage = min(leverage, max_leverage) # Ensure we don't exceed max allowed
    if target_leverage != leverage:
         logging.warning(f"Desired leverage {leverage}x exceeds max {max_leverage}x for {symbol}. Using {target_leverage}x.")

    logging.info(f"Attempting to set leverage for {symbol} to {target_leverage}x...")
    endpoint = "/trade/api/v2/futures/leverage" # [cite: 1767]
    payload = {
        "symbol": symbol.upper(),     # [cite: 1791]
        "exchange": FUTURES_EXCHANGE, # [cite: 1791]
        "leverage": target_leverage          # [cite: 1791]
    }
    # Body needs to be passed for POST signature calculation in get_headers
    headers, url = get_headers("POST", endpoint, body=payload)
    res = safe_post(url, headers, payload) # Use safe_post
    if res:
        try:
             response_data = res.json().get("data", {})
             set_lev_str = response_data.get("leverage")
             # Check if response explicitly confirms the set leverage
             if set_lev_str and int(set_lev_str) == target_leverage:
                  logging.info(f"Successfully set leverage for {symbol} to {target_leverage}x.")
                  return True
             else:
                  # Handle specific known messages or generic failure
                  response_text = res.text.lower()
                  if "leverage not modified" in response_text:
                       logging.info(f"Leverage for {symbol} already at desired value ({target_leverage}x).")
                       return True # Consider it success if already set
                  elif "in case of open position or open orders, leverage change is not allowed" in response_text: # Check message
                       logging.warning(f"Could not set leverage for {symbol} due to open position/orders.")
                       return False
                  else:
                       logging.warning(f"Set leverage call succeeded (HTTP {res.status_code}) but response unclear. Resp: {res.text}")
                       # Return True optimistically, but log warning. Re-check before trading might be needed.
                       return True
        except Exception as parse_error:
             logging.error(f"Error parsing set leverage response: {parse_error}. Response: {res.text}")
             return False
    else:
        # Check if safe_post logged a specific reason related to open positions
        # Note: safe_post logs the error, we just return False here
        return False
# --- End NEW Leverage Functions ---

def place_futures_order(symbol, side, order_type, qty, price=None, trigger_price=None, reduce_only=False, trade_info=None): # Unchanged
    # ... (same logic as v3.1) ...
    endpoint = "/trade/api/v2/futures/order"; payload={"side":side.upper(),"symbol":symbol.upper(),"order_type":order_type.upper(),"quantity":qty,"exchange":FUTURES_EXCHANGE};
    if not trade_info: logging.error(f"Missing info {symbol}."); return None;
    price_precision=trade_info.get("price_precision",2);
    if price: payload["price"]=round_to_precision(price,price_precision);
    if trigger_price: payload["trigger_price"]=round_to_precision(trigger_price,price_precision);
    if reduce_only: payload["reduce_only"]=True;
    if order_type.upper() in ["TAKE_PROFIT_MARKET","STOP_MARKET"]: payload["quantity"]=0;
    elif reduce_only and order_type.upper() == "MARKET": qty_precision=trade_info.get("qty_precision"); qty_step=trade_info.get("qty_step"); adjusted_qty=adjust_quantity_to_step(qty,qty_step); final_qty=round_to_precision(adjusted_qty,qty_precision); payload["quantity"]=final_qty; qty=final_qty;
    if final_qty<=0: logging.error(f"Close qty {qty} invalid."); return None;
    else: qty_precision=trade_info.get("qty_precision"); qty_step=trade_info.get("qty_step"); min_qty=trade_info.get("min_qty",0); adjusted_qty=adjust_quantity_to_step(qty,qty_step); final_qty=round_to_precision(adjusted_qty,qty_precision);
    if min_qty>0 and final_qty<min_qty: logging.error(f"Final qty {final_qty}<min {min_qty}. Cannot place."); return None;
    payload["quantity"]=final_qty; qty=final_qty;
    log_msg=f"[ACTION] Submit {order_type.upper()} {side.upper()} {symbol.upper()}(Qty:{qty})";
    if "price" in payload: log_msg+=f" @ Px:${payload['price']}";
    if "trigger_price" in payload: log_msg+=f" @ Trig:${payload['trigger_price']}"; logging.info(log_msg);
    if args.dry_run: logging.info(f"[DRY] Order:{json.dumps(payload)}"); return "DRY_RUN_ID";
# ---- CORRECTED BLOCK ----
if not args.yes:
    try:
        resp = input("Confirm (y/N): ").strip().lower()
        if resp != 'y':
            logging.info("[SKIP] Cancelled by user.")
            return None # Return None on cancellation
    except EOFError: # Handles cases where input isn't possible (e.g., running non-interactively without --yes)
        logging.warning("[SKIP] No input detected (EOFError). Cannot confirm order without --yes flag.")
        return None # Return None if confirmation fails
# ---- END CORRECTION ----    headers, url = get_headers("POST", endpoint, body=payload); res = safe_post(url, headers, payload);
    if res: try: order_id=res.json().get("data",{}).get("order_id"); logging.info(f"[TRADE] OK:{res.text}. ID:{order_id}"); return order_id; except Exception as e: logging.error(f"Fail parse ID:{e}-Resp:{res.text}"); return None;
    else: logging.error(f"[TRADE] FAIL {symbol}."); return None


def run_futures_bot():
    """Main logic loop for FUTURES trading."""
    logging.info("[START] Running FUTURES Market Logic...")
    logging.info(f"Trade Amt:${args.trade_amount:.2f}|Leverage:{args.leverage}x|TP:{args.tp_percent}%|SL:{args.sl_percent}%") # Removed Max Pos log

    initial_balance = get_futures_balance(); logging.info(f"Initial FUTURES Bal: ${initial_balance:.4f}")
    # No minimum balance check here

    futures_symbols = get_futures_symbols_and_prices();
    if not futures_symbols: logging.error("No FUTURES symbols."); return
    logging.info(f"Analyzing {len(futures_symbols)} FUTURES symbols...")

    processed_count = 0; traded_symbols_this_run = set()

    for item in futures_symbols:
        symbol = item["symbol"]; price = item["price"]
        logging.info(f"--- Check FUTURES: {symbol} (Px:${price:.4f}) ---")
        if symbol in traded_symbols_this_run: continue

        trade_info = get_futures_trade_info(symbol);
        if not trade_info: logging.warning(f"Skip {symbol}: No info."); time.sleep(1); continue

        current_balance = get_futures_balance()
        min_qty = trade_info.get("min_qty", float('inf'))
        if min_qty <= 0 or min_qty == float('inf'): logging.warning(f"Skip {symbol}: Invalid min_qty ({min_qty})."); time.sleep(1); continue
        min_order_value_usdt = min_qty * price; logging.debug(f"{symbol} Min Val:${min_order_value_usdt:.4f}")

        # Check 1: Balance >= Trade Amount?
        if current_balance < args.trade_amount: logging.info(f"Skip {symbol}. Bal ${current_balance:.4f} < TrdAmt ${args.trade_amount:.4f}."); continue
        # Check 2: Trade Amount >= Min Order Value?
        if args.trade_amount < min_order_value_usdt: logging.info(f"Skip {symbol}. TrdAmt ${args.trade_amount:.4f} < MinVal ${min_order_value_usdt:.4f}."); continue
        logging.info(f"Checks passed. Amt ${args.trade_amount:.4f} >= MinVal ${min_order_value_usdt:.4f}.")

        # --- Set Leverage ---
        max_leverage = trade_info.get("max_leverage", args.leverage) # Get max leverage from trade_info
        current_leverage = get_current_leverage(symbol)
        if current_leverage is None: logging.warning(f"Skip {symbol}: Could not get current leverage."); continue
        desired_leverage = min(args.leverage, max_leverage) # Ensure desired doesn't exceed max
        if current_leverage != desired_leverage:
            if not args.dry_run:
                 set_ok = set_leverage(symbol, desired_leverage, max_leverage) # Pass max_leverage to set function
                 if not set_ok: logging.warning(f"Failed or unable to set leverage {desired_leverage}x for {symbol}. Skipping trade."); continue
                 time.sleep(1) # Pause after setting
            else:
                 logging.info(f"[DRY] Would set leverage {desired_leverage}x for {symbol} (Max: {max_leverage}x).")

        # --- Balance, Min Value & Leverage OK - Proceed ---
        processed_count += 1
        investment_amount = args.trade_amount; quantity = investment_amount / price
        historical_data = get_futures_historical_data(symbol)
        prediction, current_price_from_data = train_and_predict(symbol, historical_data)
        live_price = price;
        if not math.isnan(current_price_from_data): live_price = current_price_from_data
        if math.isnan(live_price): logging.warning(f"Skip {symbol}: No valid price."); continue
        logging.info(f"[PREDICTION] {symbol}: {prediction} @ ${live_price:.{trade_info.get('price_precision', 4)}f}")

        position_info = get_futures_position(symbol) # Fetch just for this symbol now
        has_long_position = position_info and position_info["side"] == "LONG"
        has_short_position = position_info and position_info["side"] == "SHORT"

        # --- Act on BUY Signal ---
        if prediction == 'BUY':
            if has_short_position: logging.info(f"BUY signal {symbol}, closing SHORT size {position_info['size']}."); close_success = place_futures_order(symbol, "BUY", "MARKET", qty=position_info["size"], reduce_only=True, trade_info=trade_info); if close_success: traded_symbols_this_run.add(symbol); else: logging.error(f"Failed close SHORT {symbol}."); continue
            if has_long_position: logging.info(f"BUY signal {symbol}, already LONG. Skip."); continue

            price_precision=trade_info["price_precision"]; entry_price=live_price*(1-0.002); tp_price=entry_price*(1+args.tp_percent/100); sl_price=entry_price*(1-args.sl_percent/100);
            logging.info(f"Calc LONG: Qty~{quantity:.6f}, Invest~${investment_amount:.4f}, Entry~${entry_price:.{price_precision}f}, TP~${tp_price:.{price_precision}f}, SL~${sl_price:.{price_precision}f}")
            logging.info("Placing LONG Bracket..."); order_id = place_futures_order(symbol, "BUY", "LIMIT", qty=quantity, price=entry_price, trade_info=trade_info)
            if order_id:
                 traded_symbols_this_run.add(symbol); time.sleep(2); order_status = get_futures_order_status(order_id);
                 if order_status in ["RAISED", "OPEN", "PARTIALLY_EXECUTED"] or (order_id.startswith("DRY_RUN")): logging.info(f"Entry {order_id} OK. Placing TP/SL."); place_futures_order(symbol, "SELL", "TAKE_PROFIT_MARKET", qty=0, trigger_price=tp_price, reduce_only=True, trade_info=trade_info); place_futures_order(symbol, "SELL", "STOP_MARKET", qty=0, trigger_price=sl_price, reduce_only=True, trade_info=trade_info);
                 else: logging.warning(f"Entry {order_id} status '{order_status}'. No TP/SL placed.")
            else: logging.error(f"LONG Entry fail {symbol}. TP/SL not placed.")

        # --- Act on SELL Signal ---
        elif prediction == 'SELL':
            if has_long_position: logging.info(f"SELL signal {symbol}. Closing LONG size {position_info['size']}."); close_success = place_futures_order(symbol, "SELL", "MARKET", qty=position_info["size"], reduce_only=True, trade_info=trade_info); if close_success: traded_symbols_this_run.add(symbol); else: logging.error(f"Failed close LONG {symbol}."); continue
            if has_short_position: logging.info(f"SELL signal {symbol}, already SHORT. Skip."); continue

            logging.info(f"SELL signal {symbol}. Considering SHORT entry.")
            price_precision=trade_info["price_precision"]; entry_price=live_price*(1+0.002); tp_price=entry_price*(1-args.tp_percent/100); sl_price=entry_price*(1+args.sl_percent/100);
            logging.info(f"Calc SHORT: Qty~{quantity:.6f}, Invest~${investment_amount:.4f}, Entry~${entry_price:.{price_precision}f}, TP~${tp_price:.{price_precision}f}, SL~${sl_price:.{price_precision}f}")
            logging.info("Placing SHORT Bracket..."); order_id = place_futures_order(symbol, "SELL", "LIMIT", qty=quantity, price=entry_price, trade_info=trade_info)
            if order_id:
                 traded_symbols_this_run.add(symbol); time.sleep(2); order_status = get_futures_order_status(order_id);
                 if order_status in ["RAISED", "OPEN", "PARTIALLY_EXECUTED"] or (order_id.startswith("DRY_RUN")): logging.info(f"Entry {order_id} OK. Placing TP/SL."); place_futures_order(symbol, "BUY", "TAKE_PROFIT_MARKET", qty=0, trigger_price=tp_price, reduce_only=True, trade_info=trade_info); place_futures_order(symbol, "BUY", "STOP_MARKET", qty=0, trigger_price=sl_price, reduce_only=True, trade_info=trade_info);
                 else: logging.warning(f"Entry {order_id} status '{order_status}'. No TP/SL placed.")
            else: logging.error(f"SHORT Entry fail {symbol}. TP/SL not placed.")

        elif prediction == 'HOLD':
            logging.info(f"ML predicts HOLD for {symbol}. No action.")

        time.sleep(2) # Delay between checking each coin

    logging.info(f"Analyzed {processed_count} FUTURES symbols where trade amount OK.")
    logging.info("[DONE] FUTURES Bot run complete.")

# ==============================================================
# OPTIONS MARKET LOGIC (PLACEHOLDER - Unchanged)
# ==============================================================
def run_options_bot(): # Unchanged
    logging.warning("="*50); logging.warning("OPTIONS Logic Placeholder"); logging.warning("="*50); logging.warning("Options API requires whitelisting via email to api@coinswitch.co."); logging.info("1.Email:api@coinswitch.co"); logging.info("2.Subj:'Request for Options API Trading Access'"); logging.info("3.Include public API key."); logging.warning("Implement logic below after getting endpoints."); logging.warning("="*50); logging.info("[DONE] Options Bot run complete (Placeholder).")

# ==============================================================
# MAIN EXECUTION (Unchanged)
# ==============================================================
if __name__ == "__main__":
    # Removed market_type from setup_logging call - not needed as script is futures only now?
    # No, script is multi-market, setup_logging needs market_type
    setup_logging(args.market_type, args.debug) # Pass market_type here
    if not API_KEY or not SECRET_KEY: logging.critical("API Keys missing."); sys.exit(1)
    try:
        if args.market_type == 'spot': run_spot_bot() # Keep SPOT logic call
        elif args.market_type == 'futures': run_futures_bot() # This is the main focus now
        elif args.market_type == 'options': run_options_bot() # Keep OPTIONS placeholder call
        else: logging.error(f"Invalid market: {args.market_type}"); sys.exit(1)
    except KeyboardInterrupt: logging.info("Bot stopped manually.")
    except Exception as e: logging.critical("Bot error.", exc_info=True); sys.exit(1)