"""OCR reader with optional pytesseract/EasyOCR support.

This module attempts to use `pytesseract` if available and the tesseract binary installed.
If not available, it falls back to a deterministic stub useful for local testing.
"""
from PIL import Image
import io
import os
from backend import config

_has_tesseract = False
_has_easyocr = False
try:
    import pytesseract
    _has_tesseract = True
except Exception:
    _has_tesseract = False

if config.ENABLE_EASYOCR:
    try:
        import easyocr
        _has_easyocr = True
        _easyocr_reader = easyocr.Reader(['en'], gpu=False)
    except Exception:
        _has_easyocr = False


def _parse_text_for_numbers(text):
    # Very small heuristic parser to find numeric-like tokens
    parts = text.replace(',', ' ').split()
    nums = []
    for p in parts:
        try:
            v = float(p)
            nums.append(v)
        except Exception:
            # try stripping non-numeric
            s = ''.join(ch for ch in p if (ch.isdigit() or ch in '.-'))
            try:
                v = float(s)
                nums.append(v)
            except Exception:
                continue
    return nums


def extract_numbers(image_bytes):
    """Return a dict with last_price and a simple indicators map.

    image_bytes should be bytes of an image (JPEG/PNG) as provided by the frontend.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    except Exception:
        # fallback stub
        return {
            'last_price': 100.0,
            'candles': [],
            'indicators': {'EMA20': 99.5, 'EMA50': 100.2, 'RSI': 30}
        }

    # Try EasyOCR first if enabled
    if _has_easyocr:
        try:
            res = _easyocr_reader.readtext(img)
            text = ' '.join([r[1] for r in res])
            nums = _parse_text_for_numbers(text)
            last_price = nums[-1] if len(nums) > 0 else 0.0
            indicators = {
                'EMA20': nums[-3] if len(nums) > 2 else last_price * 0.99,
                'EMA50': nums[-2] if len(nums) > 1 else last_price * 1.01,
                'RSI': int(nums[-4]) if len(nums) > 3 else 50
            }
            return {'last_price': float(last_price), 'candles': [], 'indicators': indicators}
        except Exception:
            pass

    if _has_tesseract:
        try:
            text = pytesseract.image_to_string(img)
            nums = _parse_text_for_numbers(text)
            last_price = nums[-1] if len(nums) > 0 else 0.0
            # best-effort heuristic values
            indicators = {
                'EMA20': nums[-3] if len(nums) > 2 else last_price * 0.99,
                'EMA50': nums[-2] if len(nums) > 1 else last_price * 1.01,
                'RSI': int(nums[-4]) if len(nums) > 3 else 50
            }
            return {'last_price': float(last_price), 'candles': [], 'indicators': indicators}
        except Exception:
            pass

    # default deterministic stub when OCR not available
    return {'last_price': 100.0, 'candles': [], 'indicators': {'EMA20': 99.5, 'EMA50': 100.2, 'RSI': 30}}
