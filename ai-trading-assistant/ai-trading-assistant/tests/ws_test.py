"""Test that posts a sample frame and receives a message via WebSocket.

Requires: `websocket-client`, `requests`, `Pillow`.

Run:
  python tests/ws_test.py
"""
import time
import threading
import io
import requests
from PIL import Image
from websocket import WebSocketApp

URL = 'http://127.0.0.1:8000/process-frame'
WS_URL = 'ws://127.0.0.1:8000/ws/signals'

received = None

def on_message(ws, message):
    global received
    print('ws got', message)
    received = message
    ws.close()

def on_error(ws, err):
    print('ws error', err)

def on_close(ws):
    print('ws closed')

def start_ws():
    ws = WebSocketApp(WS_URL, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever()

if __name__ == '__main__':
    # start ws client in thread
    t = threading.Thread(target=start_ws, daemon=True)
    t.start()
    time.sleep(1)

    # create sample image
    img = Image.new('RGB', (320,240), color=(100,150,200))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    files = {'frame': ('frame.jpg', buf, 'image/jpeg')}
    r = requests.post(URL, files=files)
    print('post status', r.status_code, r.text)

    # wait for ws to receive
    for _ in range(10):
        if received:
            print('received via ws:', received)
            break
        time.sleep(0.5)
    else:
        print('no ws message received')
