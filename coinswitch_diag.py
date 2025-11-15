# coinswitch_diag.py — diagnostic only
import os, requests, time, json
BASE_URL = os.environ.get("BASE_URL","https://coinswitch.co")
EXCHANGE = os.environ.get("EXCHANGE","EXCHANGE_2")
SYMBOLS = ["BTCUSDT","BTC/USDT","BTC/usdt","btcusdt"]

def call_tradeinfo(sym):
    url = BASE_URL + "/trade/api/v2/tradeInfo"
    params = {"exchange": EXCHANGE, "symbol": sym}
    print("GET", url, "params=", params)
    r = requests.get(url, params=params, timeout=15)
    print("status:", r.status_code)
    print("headers:", dict(list(r.headers.items())[:10]))
    print("body:", r.text[:4000])
    print("-"*60)

def call_precision(sym):
    url = BASE_URL + "/trade/api/v2/exchangePrecision"
    payload = {"exchange": EXCHANGE, "symbol": sym}
    print("POST", url, "json=", payload)
    r = requests.post(url, json=payload, timeout=15)
    print("status:", r.status_code)
    print("headers:", dict(list(r.headers.items())[:10]))
    print("body:", r.text[:4000])
    print("="*60)

if __name__ == "__main__":
    for s in SYMBOLS:
        call_tradeinfo(s)
        call_precision(s)
        time.sleep(1)
