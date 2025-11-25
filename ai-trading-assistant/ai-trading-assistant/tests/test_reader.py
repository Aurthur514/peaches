import io
import sys
import os
from PIL import Image
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ocr.reader import extract_numbers


def test_reader_stub_returns_indicators():
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    data = extract_numbers(buf.read())
    assert 'last_price' in data
    assert 'indicators' in data
    assert isinstance(data['indicators'], dict)
