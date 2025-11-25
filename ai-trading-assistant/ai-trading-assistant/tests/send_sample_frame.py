"""Simple test script: generates a small JPEG and POSTs to /process-frame

Usage:
  python tests/send_sample_frame.py

It expects the backend to be running at http://127.0.0.1:8000
"""

import io
import requests
from PIL import Image

URL = 'http://127.0.0.1:8000/process-frame'

# create a small red image for testing
img = Image.new('RGB', (320, 240), color=(200, 60, 60))
buf = io.BytesIO()
img.save(buf, format='JPEG')
buf.seek(0)

files = {'frame': ('frame.jpg', buf, 'image/jpeg')}
try:
    r = requests.post(URL, files=files, timeout=10)
    print('status', r.status_code)
    try:
        print('json:', r.json())
    except Exception:
        print('text:', r.text)
except Exception as e:
    print('error sending frame:', e)
