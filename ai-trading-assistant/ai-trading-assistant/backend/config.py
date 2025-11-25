from pathlib import Path
import os
# Try to load .env if present
try:
    from dotenv import load_dotenv
    _here = Path(__file__).resolve().parents[0]
    env_path = _here / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass
# Configuration for the AI Trading Assistant backend.

# Path to ONNX model (relative to backend/)
MODEL_PATH = Path(os.environ.get('MODEL_PATH', 'models/model.onnx'))

# Enable OCR backends
ENABLE_TESSERACT = os.environ.get('ENABLE_TESSERACT', '1') == '1'
ENABLE_EASYOCR = os.environ.get('ENABLE_EASYOCR', '0') == '1'

# ONNX input mapping: map model input name (lowercased) -> feature key in incoming features
# Example: {'input_0': 'ema20', 'input_1': 'ema50', 'input_2': 'rsi'}
ONNX_INPUT_MAP = {
    # default mapping; adapt to your model's inputs
    'ema20': 'ema20',
    'ema50': 'ema50',
    'rsi': 'rsi',
    'last_price': 'last_price'
}

# Thresholds and behavior
CONFIDENCE_BUY = float(os.environ.get('CONFIDENCE_BUY', '0.65'))
CONFIDENCE_SELL = float(os.environ.get('CONFIDENCE_SELL', '0.35'))

# Admin token for model upload / admin API. Set to a strong random value in production.
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

def resolve_model_path():
    p = Path(MODEL_PATH)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[0] / p
    return p
