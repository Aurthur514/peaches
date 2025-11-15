import os
import time
import json
import hmac
import hashlib
import threading
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import requests
import socketio


# =========================
# Config & constants
# =========================

COINSWITCH_BASE = os.getenv("COINSWITCH_BASE", "https://coinswitch.co")
WS_BASE = os.getenv("WS_BASE", "wss://ws.coinswitch.co")
API_KEY = os.getenv("COINSWITCH_API_KEY", "<YOUR_API_KEY>")
SECRET_KEY = os.getenv("COINSWITCH_SECRET", "<YOUR_SECRET_HEX_OR_KEY>")  # keep secure
EXCHANGE = "EXCHANGE_2"  # Futures
USER_AGENT = "FuturesBot/1.0"

# Rate/circuit
MAX_RETRIES = 3
RETRY_BACKOFF = 0.8  # seconds
REQUEST_TIMEOUT = 10

# Risk config
MAX_NOTIONAL_USDT = 1000.0         # cap total notional risk
MAX_OPEN_ORDERS = 10               # throttle concurrent orders
DEFAULT_LEVERAGE = 3               # discipline default
SYMBOLS = ["BTCUSDT", "ETHUSDT"]   # trade universe

# Strategy config
ORDER_TIME_IN_FORCE = "GTC"
POSITION_MODE = 3  # Hedge mode (Both Sides)
MIN_SPREAD_BPS = 1.5  # e.g., refuse orders if spread too tight/erratic


# =========================
# Utilities
# =========================

def _headers(auth: bool = True) -> Dict[str, str]:
    """
    Build REST headers. Some endpoints require only API key + signature.
    """
    h = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "X-AUTH-APIKEY": API_KEY,
    }
    if auth:
        # For Futures v2 endpoints examples, signature header is required.
        # If ED25519 signing is mandated, implement per doc's signing scheme.
        # Here we attach a placeholder HMAC-based signature if backend accepts,
        # else build the exact signature per your server's requirement.
        # Consult CoinSwitch team if needed for the exact signing string.
        # For many Futures examples in doc, signature is present without epoch.
        message = "static-or-request-specific-signature"
        sig = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()
        h["X-AUTH-SIGNATURE"] = sig
    return h


def _request(method: str, endpoint: str, params: Optional[Dict[str, Any]] = None,
             payload: Optional[Dict[str, Any]] = None, auth: bool = True) -> Dict[str, Any]:
    url = COINSWITCH_BASE + endpoint
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(
                method,
                url,
                headers=_headers(auth),
                params=params if method == "GET" else None,
                json=payload if method != "GET" else None,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 429:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            if 500 <= resp.status_code < 600:
                # Unknown status: reconcile with GET order where relevant
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_exc = e
            time.sleep(RETRY_BACKOFF * (attempt + 1))
    raise RuntimeError(f"Request failed: {endpoint} | last_exc={last_exc}")


# =========================
# Public market data
# =========================

class FuturesMarketData:
    @staticmethod
    def ticker(symbol: str) -> Dict[str, Any]:
        return _request("GET", "/trade/api/v2/futures/ticker",
                        params={"exchange": EXCHANGE, "symbol": symbol})["data"][EXCHANGE]  # includes mark, index, best bid/ask

    @staticmethod
    def order_book_l2(symbol: str) -> Dict[str, Any]:
        return _request("GET", "/trade/api/v2/futures/order_book",
                        params={"exchange": EXCHANGE, "symbol": symbol, "l2Orderbook": "true"})["data"]  # aggregated levels

    @staticmethod
    def klines(symbol: str, interval: str, start: Optional[int] = None, end: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"exchange": EXCHANGE, "symbol": symbol, "interval": interval}
        if start: params["start_time"] = start
        if end: params["end_time"] = end
        return _request("GET", "/trade/api/v2/futures/klines", params=params)["data"]  # o,h,l,c,volume

    @staticmethod
    def trades(symbol: str) -> List[Dict[str, Any]]:
        return _request("GET", "/trade/api/v2/futures/trades",
                        params={"exchange": EXCHANGE, "symbol": symbol})["data"]  # recent trades


# =========================
# Private trading & account
# =========================

class FuturesTrade:
    @staticmethod
    def set_leverage(symbol: str, leverage: int) -> Dict[str, Any]:
        return _request("POST", "/trade/api/v2/futures/leverage",
                        payload={"symbol": symbol.lower(), "exchange": EXCHANGE, "leverage": leverage})["data"]  # blocked if open pos/orders

    @staticmethod
    def get_leverage(symbol: str) -> Dict[str, Any]:
        return _request("GET", "/trade/api/v2/futures/leverage",
                        params={"symbol": symbol.lower(), "exchange": EXCHANGE})["data"]  # current leverage

    @staticmethod
    def place_order(symbol: str, side: str, order_type: str,
                    quantity: float, price: Optional[float] = None,
                    trigger_price: Optional[float] = None,
                    reduce_only: Optional[bool] = None) -> Dict[str, Any]:
        payload = {
            "symbol": symbol.lower(),
            "exchange": EXCHANGE,
            "side": side.upper(),  # BUY / SELL
            "order_type": order_type.upper(),  # LIMIT / MARKET / TAKE_PROFIT_MARKET / STOP_MARKET
            "quantity": quantity,
        }
        if price is not None:
            payload["price"] = price
        if trigger_price is not None:
            payload["trigger_price"] = trigger_price
        if reduce_only is not None:
            payload["reduce_only"] = reduce_only
        return _request("POST", "/trade/api/v2/futures/order", payload=payload)["data"]  # returns order_id & status (RAISED)

    @staticmethod
    def cancel_order(order_id: str) -> Dict[str, Any]:
        return _request("DELETE", "/trade/api/v2/futures/order",
                        payload={"exchange": EXCHANGE, "order_id": order_id})["data"]  # status may be CANCELLATION_RAISED

    @staticmethod
    def order_status(order_id: str) -> Dict[str, Any]:
        return _request("GET", "/trade/api/v2/futures/order",
                        params={"order_id": order_id})["data"]["order"]  # New/Cancelled/Executed etc.

    @staticmethod
    def open_orders(symbol: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        payload = {"exchange": EXCHANGE, "limit": min(limit, 50)}
        if symbol: payload["symbol"] = symbol.lower()
        return _request("POST", "/trade/api/v2/futures/orders/open", payload=payload)["data"]  # last 7 days constraint

    @staticmethod
    def closed_orders(symbol: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        payload = {"exchange": EXCHANGE, "limit": min(limit, 50)}
        if symbol: payload["symbol"] = symbol.lower()
        return _request("POST", "/trade/api/v2/futures/orders/closed", payload=payload)["data"]  # last 50 in 7 days window

    @staticmethod
    def add_margin(symbol: str, margin: float) -> Dict[str, Any]:
        return _request("POST", "/trade/api/v2/futures/add_margin",
                        payload={"exchange": EXCHANGE, "symbol": symbol.lower(), "margin": margin})["data"]  # must be ≤ available balance

    @staticmethod
    def cancel_all(symbol: Optional[str] = None) -> Dict[str, Any]:
        payload = {"exchange": EXCHANGE}
        if symbol: payload["symbol"] = symbol.lower()
        return _request("POST", "/trade/api/v2/futures/cancel_all", payload=payload)["data"]  # cancels TP/SL too


class FuturesAccount:
    @staticmethod
    def wallet_balance() -> Dict[str, Any]:
        return _request("GET", "/trade/api/v2/futures/wallet_balance")["data"]  # base_asset_balances etc.

    @staticmethod
    def positions(symbol: str) -> List[Dict[str, Any]]:
        return _request("GET", "/trade/api/v2/futures/positions",
                        params={"exchange": EXCHANGE, "symbol": symbol.lower()})["data"]  # includes markPrice, pnl


# =========================
# Sockets (market & user)
# =========================

class FuturesSockets:
    def __init__(self, exchange_namespace="/exchange_2"):
        self.sio = socketio.Client()
        self.namespace = exchange_namespace

    def connect(self):
        self.sio.connect(
            WS_BASE,
            namespaces=[self.namespace],
            transports="websocket",
            socketio_path="/pro/realtime-rates-socket/futures/exchange_2"  # futures handshake
        )

    def subscribe_ticker(self, pair: str, on_message):
        @self.sio.on("FETCH_TICKER_INFO_CS_PRO", namespace=self.namespace)
        def handler(data):
            on_message(data)

        self.sio.emit("FETCH_TICKER_INFO_CS_PRO", {"event": "subscribe", "pair": pair}, namespace=self.namespace)

    def subscribe_order_book(self, pair: str, on_message):
        @self.sio.on("FETCH_ORDER_BOOK_CS_PRO", namespace=self.namespace)
        def handler(data):
            on_message(data)
        self.sio.emit("FETCH_ORDER_BOOK_CS_PRO", {"event": "subscribe", "pair": pair}, namespace=self.namespace)

    def subscribe_trades(self, pair: str, on_message):
        @self.sio.on("FETCH_TRADES_CS_PRO", namespace=self.namespace)
        def handler(data):
            on_message(data)
        self.sio.emit("FETCH_TRADES_CS_PRO", {"event": "subscribe", "pair": pair}, namespace=self.namespace)

    def wait(self):
        self.sio.wait()


# =========================
# Strategy placeholder
# =========================

@dataclass
class Signal:
    symbol: str
    side: str        # BUY/SELL
    order_type: str  # LIMIT/MARKET
    price: Optional[float]
    qty: float
    reduce_only: Optional[bool] = None


class SimpleMakerStrategy:
    """
    Example: place small mean-reversion makers around mid-price if spread > threshold.
    Plug your model here (e.g., momentum, microstructure, volatility breakout).
    """

    def decide(self, ob: Dict[str, Any]) -> Optional[Signal]:
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])
        if not bids or not asks:
            return None
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid = (best_bid + best_ask) / 2.0
        spread_bps = 10000 * (best_ask - best_bid) / mid
        if spread_bps < MIN_SPREAD_BPS:
            return None

        # Example: place a tiny BUY below mid and SELL above mid
        qty = 0.001
        return Signal(symbol="BTCUSDT", side="BUY", order_type="LIMIT", price=round(mid * 0.999, 2), qty=qty)


# =========================
# Risk management
# =========================

class RiskManager:
    def __init__(self):
        self.open_orders = 0

    def check_wallet_and_limits(self, symbol: str) -> bool:
        wb = FuturesAccount.wallet_balance()
        total_avail = 0.0
        for b in wb.get("base_asset_balances", []):
            if b.get("base_asset") == "USDT":
                total_avail = float(b["balances"]["total_available_balance"])
        if total_avail > MAX_NOTIONAL_USDT and self.open_orders < MAX_OPEN_ORDERS:
            return True
        return False

    def before_order(self, signal: Signal) -> bool:
        return True

    def after_order(self):
        self.open_orders += 1

    def after_cancel(self):
        self.open_orders = max(0, self.open_orders - 1)


# =========================
# Bot orchestration
# =========================

class FuturesBot:
    def __init__(self):
        self.rm = RiskManager()
        self.strategy = SimpleMakerStrategy()
        self.md = FuturesMarketData()
        self.exec = FuturesTrade()
        self.sockets = FuturesSockets()

    def bootstrap(self):
        # Position mode and leverage discipline
        try:
            self.exec.set_leverage("btcusdt", DEFAULT_LEVERAGE)
        except Exception:
            pass  # leverage not modified or open pos/orders present is acceptable

    def run(self):
        self.bootstrap()

        def on_order_book(data):
            try:
                ob = data.get("data", {})
                sig = self.strategy.decide(ob)
                if not sig:
                    return
                if not self.rm.check_wallet_and_limits(sig.symbol):
                    return
                if not self.rm.before_order(sig):
                    return

                placed = self.exec.place_order(
                    symbol=sig.symbol,
                    side=sig.side,
                    order_type=sig.order_type,
                    quantity=sig.qty,
                    price=sig.price,
                    reduce_only=sig.reduce_only
                )
                order_id = placed.get("order_id")
                self.rm.after_order()

                # Poll resolution if status is RAISED
                if placed.get("status") == "RAISED" and order_id:
                    time.sleep(0.5)
                    status = self.exec.order_status(order_id)
                    # Optional: attach TP/SL for full position using STOP/TAKE_PROFIT_MARKET with quantity=0

            except Exception as e:
                # Backoff on errors (4XX/5XX) and avoid storming the API
                time.sleep(RETRY_BACKOFF)

        # Connect sockets
        self.sockets.connect()
        self.sockets.subscribe_order_book("BTCUSDT", on_order_book)
        self.sockets.wait()


if __name__ == "__main__":
    bot = FuturesBot()
    # Consider running in a daemon thread, plus a separate reconciliation loop:
    # - Regularly fetch open_orders/positions/wallet to ensure consistency
    # - Cancel stale makers via cancel_all if spread collapses or kill-switch triggers
    bot.run()
