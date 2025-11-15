#!/usr/bin/env python3
"""
ultron_futures_new.py
A fresh, safety-first futures trading bot for CoinSwitch PRO.

Features:
 - Robust fetching of futures klines
 - Deterministic Ed25519 signing for authenticated endpoints
 - Lightweight RF classifier signal (optional) + fallback rule-based signal
 - ATR-driven TP/SL (volatility adaptive)
 - Minimum-quote & precision parsing for order quantity
 - Position sizing (min-quote and risk-per-trade support)
 - Dry-run default (safe). Use --live --yes to execute (dangerous!)

Usage:
 python ultron_futures_new.py --debug --dry-run --symbols=BTC/USDT,ETH/USDT
Env:
 API_KEY, SECRET_KEY (hex), optional BASE_URL, EXCHANGE
"""
from __future__ import annotations
import os, sys, time, json, math, random, logging
import requests, urllib
from urllib.parse import urlencode
import pandas as pd, numpy as np
from typing import Optional, Tuple, Dict, Any, List
from cryptography.hazmat.primitives.asymmetric import ed25519
from sklearn.ensemble import RandomForestClassifier

# ------------- CONFIG & CLI -------------
DEBUG = '--debug' in sys.argv
DRY_RUN_FLAG = '--dry-run' in sys.argv
LIVE_FLAG = '--live' in sys.argv
AUTO_YES = '--yes' in sys.argv

# CLI overrides
CLI_INTERVAL = None
CLI_BARS = None
for a in sys.argv:
    if a.startswith('--interval='):
        try: CLI_INTERVAL = int(a.split('=',1)[1])
        except: pass
    if a.startswith('--bars='):
        try: CLI_BARS = int(a.split('=',1)[1])
        except: pass

API_KEY = os.environ.get("API_KEY")
SECRET_KEY_HEX = os.environ.get("SECRET_KEY")
BASE_URL = os.environ.get("BASE_URL", "https://coinswitch.co")
EXCHANGE = os.environ.get("EXCHANGE", "EXCHANGE_2")
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "15"))

DEFAULT_INTERVAL_MIN = CLI_INTERVAL or int(os.environ.get("CANDLE_INTERVAL_MIN", "240"))  # 4h default per your request
DEFAULT_BARS = CLI_BARS or int(os.environ.get("LOOKBACK_BARS", "48"))

# Position sizing settings
RISK_PER_TRADE_QUOTE = float(os.environ.get("RISK_PER_TRADE_QUOTE", "10.0"))  # $ amount risk per trade fallback
FALLBACK_MIN_QUOTE = float(os.environ.get("FALLBACK_MIN_QUOTE", "10.0"))
FALLBACK_BASE_PREC = int(os.environ.get("FALLBACK_BASE_PREC", "6"))

DRY_RUN = True if (DRY_RUN_FLAG or not LIVE_FLAG) else False
if LIVE_FLAG and DRY_RUN_FLAG:
    # explicit precedence if both present -> DRY_RUN if --dry-run
    DRY_RUN = True

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO, format='[%(levelname)s] %(message)s')

# ------------- ENDPOINTS -------------
EP_TIME = "/trade/api/v2/time"
EP_FUT_KLINES = "/trade/api/v2/futures/klines"
EP_FUT_ORDER = "/trade/api/v2/futures/order"
EP_FUT_TICKER = "/trade/api/v2/futures/ticker"
EP_TRADEINFO = "/trade/api/v2/tradeInfo"
EP_EXCHANGE_PREC = "/trade/api/v2/exchangePrecision"
EP_FUT_INSTRUMENT = "/trade/api/v2/futures/instrument_info"

# ------------- HELPERS -------------
def debug(*a, **k):
    if DEBUG:
        print(*a, **k)

def jitter_sleep(s=0.5):
    time.sleep(s + random.random()*0.25)

def _canonical_query(params: Optional[dict]) -> str:
    if not params: return ""
    return "?" + urlencode(sorted(params.items()))

def _load_private_key(hexstr: str) -> Optional[bytes]:
    if not hexstr: return None
    s = hexstr.strip()
    if all(c in "0123456789abcdefABCDEF" for c in s) and len(s) % 2 == 0:
        b = bytes.fromhex(s)
        if len(b) >= 32:
            return b[:32]
    raise RuntimeError("SECRET_KEY must be hex (32 or 64 hex chars)")

try:
    PRIVATE_KEY = _load_private_key(SECRET_KEY_HEX)
except Exception as e:
    PRIVATE_KEY = None
    debug("[WARN] SECRET_KEY parse:", e)

def server_time_ms() -> str:
    try:
        r = requests.get(BASE_URL + EP_TIME, timeout=REQUEST_TIMEOUT)
        if r.ok:
            j = r.json()
            st = j.get("serverTime") or j.get("time")
            return str(int(st))
    except Exception:
        pass
    return str(int(time.time() * 1000))

def sign_message(method: str, endpoint: str, params: Optional[dict], body: Optional[dict], epoch: str) -> str:
    if PRIVATE_KEY is None:
        raise RuntimeError("SECRET_KEY missing")
    method = method.upper()
    query = ""
    if method == "GET" and params:
        query = "?" + urlencode(sorted(params.items()))
    unquoted = urllib.parse.unquote_plus(endpoint + query)
    body_str = ""
    if method == "POST" and body:
        body_str = json.dumps(body, separators=(',', ':'), sort_keys=True)
    msg = method + unquoted + epoch + body_str
    key = ed25519.Ed25519PrivateKey.from_private_bytes(PRIVATE_KEY)
    return key.sign(msg.encode()).hex()

def build_headers(method: str, endpoint: str, params=None, body=None) -> dict:
    epoch = server_time_ms()
    sig = sign_message(method, endpoint, params, body, epoch)
    return {
        "Content-Type": "application/json",
        "X-AUTH-APIKEY": API_KEY or "",
        "X-AUTH-SIGNATURE": sig,
        "X-AUTH-EPOCH": epoch
    }

def safe_get(endpoint: str, params: Optional[dict]=None, retries=3) -> Optional[requests.Response]:
    url = BASE_URL + endpoint + (_canonical_query(params) if params else "")
    for i in range(retries):
        try:
            headers = build_headers("GET", endpoint, params, None)
            r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if r.ok:
                return r
            text = getattr(r, "text", "")[:1000]
            logging.warning("GET %s -> %s: %s", url, r.status_code, text)
            if r.status_code in (429, 500, 502):
                jitter_sleep(2**i)
                continue
            return r
        except Exception as e:
            logging.error("GET attempt %d failed: %s", i+1, e)
            jitter_sleep(2**i)
    return None

def safe_post(endpoint: str, payload: dict, retries=3) -> Optional[requests.Response]:
    url = BASE_URL + endpoint
    for i in range(retries):
        try:
            headers = build_headers("POST", endpoint, None, payload)
            r = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
            if r.ok:
                return r
            text = getattr(r, "text", "")[:1000]
            logging.warning("POST %s -> %s: %s", endpoint, r.status_code, text)
            if r.status_code in (429, 500, 502):
                jitter_sleep(2**i)
                continue
            return r
        except Exception as e:
            logging.error("POST attempt %d failed: %s", i+1, e)
            jitter_sleep(2**i)
    return None

# ------------- MARKET DATA -------------
def normalize_symbol(sym: str) -> str:
    return sym.replace("/", "").upper()

def fetch_futures_klines(symbol: str, exchange=EXCHANGE, interval_min=DEFAULT_INTERVAL_MIN, bars=DEFAULT_BARS) -> pd.DataFrame:
    sym = normalize_symbol(symbol)
    end_ms = int(time.time()*1000)
    lookback_ms = bars * interval_min * 60 * 1000
    start_ms = end_ms - lookback_ms
    params = {"exchange": exchange, "symbol": sym, "interval": str(interval_min), "start_time": str(start_ms), "end_time": str(end_ms)}
    logging.debug("Request klines %s %s", EP_FUT_KLINES, params)
    r = safe_get(EP_FUT_KLINES, params=params)
    if not r:
        logging.warning("No klines response for %s", sym)
        return pd.DataFrame()
    try:
        j = r.json()
    except Exception:
        logging.error("Klines JSON parse error")
        return pd.DataFrame()
    data = j.get("data") or j.get("result") or j
    if isinstance(data, dict):
        # common shapes: list under 'data' or symbol key
        cand = data.get(sym) or data.get('candles') or data.get('klines') or []
    else:
        cand = data if isinstance(data, list) else []
    rows = []
    for it in cand:
        try:
            o = float(it.get('o') or it.get('open') or it.get('O'))
            h = float(it.get('h') or it.get('high') or it.get('H'))
            l = float(it.get('l') or it.get('low') or it.get('L'))
            c = float(it.get('c') or it.get('close') or it.get('C'))
            v = float(it.get('v') or it.get('volume') or it.get('q') or 0)
            ts = int(it.get('t') or it.get('timestamp') or it.get('start_time') or it.get('close_time') or 0)
            if ts:
                rows.append([ts, o, h, l, c, v])
        except Exception:
            continue
    if not rows:
        logging.warning("No rows parsed for klines %s", sym)
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["timestamp","open","high","low","close","volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df

# ------------- EXCHANGE METADATA -------------
def get_trade_info(exchange: str, symbol: str) -> dict:
    # Try GET with multiple formats then POST fallback
    candidates = [symbol.replace("/", ""), symbol if "/" in symbol else (symbol[:3] + "/" + symbol[3:])]
    for s in candidates:
        r = safe_get(EP_TRADEINFO, params={"exchange": exchange, "symbol": s})
        if r is None:
            continue
        try:
            j = r.json()
        except Exception:
            continue
        if r.ok and (j.get('data') or j):
            return j.get('data') or j
    # POST fallback
    for s in candidates:
        r = safe_post(EP_TRADEINFO, {"exchange": exchange, "symbol": s})
        if r and r.ok:
            try:
                j = r.json()
                return j.get('data') or j
            except:
                pass
    return {}

def get_exchange_precision(exchange: str, symbol: str) -> dict:
    candidates = [symbol.replace("/", ""), symbol if "/" in symbol else (symbol[:3] + "/" + symbol[3:])]
    for s in candidates:
        r = safe_post(EP_EXCHANGE_PREC, {"exchange": exchange, "symbol": s})
        if r is None:
            continue
        try:
            j = r.json()
        except Exception:
            continue
        if r.ok and (j.get('data') or j):
            return j.get('data') or j
    return {}

def get_futures_instrument_info(exchange: str, symbol: str) -> dict:
    s = normalize_symbol(symbol)
    r = safe_get(EP_FUT_INSTRUMENT, params={"exchange": exchange, "symbol": s})
    if not r:
        return {}
    try:
        j = r.json()
    except:
        return {}
    return j.get('data') or j

# ------------- ML SIGNALS & RULES -------------
def featurize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret"] = df["close"].pct_change().fillna(0)
    df["SMA_3"] = df["close"].rolling(3).mean()
    df["SMA_6"] = df["close"].rolling(6).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(6).mean()
    loss = (-delta.clip(upper=0)).rolling(6).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs.replace(np.nan, 0)))
    return df.dropna()

def label_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["future"] = df["close"].shift(-1)
    df["pct"] = (df["future"] - df["close"]) / df["close"]
    df["label"] = df["pct"].apply(lambda x: "LONG" if x > 0.005 else ("SHORT" if x < -0.005 else "HOLD"))
    return df.dropna()

def train_model(df: pd.DataFrame, min_bars=12):
    if len(df) < min_bars:
        return None
    Xdf = featurize(df)
    L = label_data(Xdf)
    X = L[["SMA_3","SMA_6","RSI","ret"]]
    y = L["label"]
    clf = RandomForestClassifier(n_estimators=80, random_state=42)
    clf.fit(X, y)
    return clf

def predict(clf, df: pd.DataFrame) -> Tuple[str,float]:
    if clf is None:
        return "HOLD", float(df["close"].iloc[-1])
    Xdf = featurize(df)
    x = Xdf[["SMA_3","SMA_6","RSI","ret"]].tail(1)
    if x.empty:
        return "HOLD", float(df["close"].iloc[-1])
    pred = clf.predict(x)[0]
    return pred, float(df["close"].iloc[-1])

# ------------- RISK & TP/SL -------------
def compute_atr(df: pd.DataFrame, n=14) -> float:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(n).mean().iloc[-1]
    return float(atr) if not math.isnan(atr) else 0.0

def determine_tp_sl(side: str, price: float, df: pd.DataFrame) -> Tuple[float,float]:
    atr = compute_atr(df)
    if atr <= 0 or math.isnan(price):
        pct_sl = 0.02
        pct_tp = 0.04
        if side == "BUY":
            return price*(1+pct_tp), price*(1-pct_sl)
        else:
            return price*(1-pct_sl), price*(1+pct_tp)
    if side == "BUY":
        tp = price + 2*atr
        sl = price - 1*atr
    else:
        tp = price - 2*atr
        sl = price + 1*atr
    return float(tp), float(sl)

def qty_from_min_quote(min_quote: float, price: float, base_prec: int) -> float:
    if price <= 0:
        return 0.0
    qty = max(0.000001, float(min_quote) / float(price))
    fmt = "{:." + str(int(base_prec)) + "f}"
    return float(fmt.format(qty))

# ------------- ORDERING -------------
def place_order(symbol: str, side: str, price: float, qty: float, exchange=EXCHANGE, order_type="LIMIT", reduce_only=False) -> Optional[dict]:
    payload = {
        "exchange": exchange,
        "symbol": normalize_symbol(symbol),
        "price": price,
        "side": side.lower(),
        "order_type": order_type,
        "quantity": qty,
        "reduce_only": reduce_only
    }
    r = safe_post(EP_FUT_ORDER, payload)
    if not r:
        return None
    try:
        return r.json()
    except:
        return {"status_code": getattr(r, "status_code", None), "text": getattr(r, "text", None)}

# ------------- RUN -------------
def analyze_and_trade(symbols: List[str], interval_min:int=DEFAULT_INTERVAL_MIN, bars:int=DEFAULT_BARS):
    if not API_KEY or not SECRET_KEY:
        logging.warning("API_KEY or SECRET_KEY missing — will still run but authenticated calls will fail.")
    summary = {"started": int(time.time()*1000), "actions":[]}
    for sym in symbols:
        sym = sym.strip()
        fut_sym = normalize_symbol(sym)
        logging.info("=== analyzing %s ===", fut_sym)

        # 1) candles
        df = fetch_futures_klines(fut_sym, exchange=EXCHANGE, interval_min=interval_min, bars=bars)
        if df.empty or len(df) < 6:
            logging.warning("Insufficient candles for %s (%d rows)", fut_sym, len(df))
            summary["actions"].append({"symbol": fut_sym, "action": "SKIP_NO_DATA"})
            continue

        # 2) instrument/precision/tradeInfo
        trade_info = get_trade_info(EXCHANGE, fut_sym)
        precision_info = get_exchange_precision(EXCHANGE, fut_sym)
        fut_inst = get_futures_instrument_info(EXCHANGE, fut_sym)

        # parse min_quote (quote currency min) and base precision
        min_quote = None
        base_prec = None
        # Try futures instrument info first
        try:
            if isinstance(fut_inst, dict) and fut_inst:
                # many shapes exist; attempt to detect sensible fields
                # look for min quote under 'quote' or 'min_quote' or 'min_trade_amount'
                candidate = fut_inst.get(fut_sym) if fut_sym in fut_inst else next(iter(fut_inst.values()), fut_inst)
                if isinstance(candidate, dict):
                    q = candidate.get("quote") or candidate.get("quoteFilter") or {}
                    min_quote = min_quote or (float(q.get("min")) if q.get("min") else None)
                    # lotSizeFilter stepSize -> base precision
                    lf = candidate.get("lotSizeFilter") or {}
                    step = lf.get("stepSize") or lf.get("minQty")
                    if step:
                        s = str(step)
                        if "." in s:
                            base_prec = len(s.split(".")[-1].rstrip("0"))
                        else:
                            base_prec = 0
        except Exception:
            pass

        # fallback parsing from trade_info / precision_info
        try:
            if not min_quote and isinstance(trade_info, dict):
                # inspect nested dicts
                data = trade_info.get("data") if "data" in trade_info else trade_info
                for k,v in (data.items() if isinstance(data, dict) else []):
                    if isinstance(v, dict):
                        for sym_k, sym_v in v.items():
                            if isinstance(sym_v, dict):
                                q = sym_v.get("quote") or {}
                                if q.get("min"):
                                    min_quote = float(q.get("min"))
                                    break
        except Exception:
            pass

        try:
            if not base_prec and isinstance(precision_info, dict):
                # try to find base precision for fut_sym
                for k,v in precision_info.items():
                    if isinstance(v, dict) and fut_sym in v and isinstance(v[fut_sym], dict):
                        base_prec = v[fut_sym].get("base") or base_prec
                    elif isinstance(v, dict) and "base" in v and "quote" in v:
                        base_prec = v.get("base") or base_prec
        except Exception:
            pass

        # final fallbacks
        if not min_quote:
            min_quote = FALLBACK_MIN_QUOTE
        if not base_prec:
            base_prec = FALLBACK_BASE_PREC

        logging.debug("min_quote=%s base_prec=%s", min_quote, base_prec)

        # 3) model train+predict
        model = train_model(df)
        pred, price = predict(model, df)
        logging.info("PREDICT %s -> %s @ %.8f", fut_sym, pred, price)

        if pred == "HOLD":
            summary["actions"].append({"symbol": fut_sym, "action": "HOLD"})
            continue

        side = "BUY" if pred == "LONG" else "SELL"

        # 4) qty & sizing
        qty = qty_from_min_quote(min_quote, price, int(base_prec))
        # ensure minimal sanity
        qty = max(qty, 0.000001)

        # 5) TP / SL
        tp, sl = determine_tp_sl(side, price, df)

        logging.info("ACTION %s %s qty=%s price=%.8f TP=%.8f SL=%.8f", side, fut_sym, qty, price, tp, sl)

        # record summary
        if DRY_RUN:
            logging.info("[DRY-RUN] simulated order not sent")
            summary["actions"].append({"symbol": fut_sym, "action":"DRY_RUN", "side": side, "qty": qty, "price": price, "tp": tp, "sl": sl})
            continue

        # confirmation if not auto
        if not AUTO_YES:
            ans = input(f"Confirm {side} {fut_sym} qty {qty} @ {price:.8f}? (y/N): ").strip().lower()
            if ans != 'y':
                summary["actions"].append({"symbol": fut_sym, "action":"ABORT_USER"})
                continue

        resp = place_order(fut_sym, side, price, qty, exchange=EXCHANGE)
        logging.info("Order response: %s", resp)
        summary["actions"].append({"symbol": fut_sym, "action":"TRADE", "side": side, "qty": qty, "price": price, "resp": resp})
        jitter_sleep(1)

    summary["finished"] = int(time.time()*1000)
    print(json.dumps(summary, indent=2))
    return summary

# ------------- MAIN -------------
if __name__ == "__main__":
    syms = ["BTC/USDT"]
    for a in sys.argv:
        if a.startswith('--symbols='):
            syms = [s.strip() for s in a.split('=',1)[1].split(',') if s.strip()]
    analyze_and_trade(syms, interval_min=CLI_INTERVAL or DEFAULT_INTERVAL_MIN, bars=CLI_BARS or DEFAULT_BARS)
