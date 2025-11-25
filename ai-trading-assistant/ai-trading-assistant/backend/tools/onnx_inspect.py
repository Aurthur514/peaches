"""Inspect an ONNX model and print inputs/outputs and suggested mapping.

Usage:
  python backend/tools/onnx_inspect.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from backend import config

try:
    import onnx
    import onnxruntime as ort
except Exception as e:
    print('Please install onnx and onnxruntime to use this tool:', e)
    raise

MODEL = config.resolve_model_path()
print('Inspecting model at', MODEL)
if not MODEL.exists():
    print('Model file not found. Place your model at', MODEL)
    sys.exit(1)

sess = ort.InferenceSession(str(MODEL))
print('\nInputs:')
for inp in sess.get_inputs():
    print('-', inp.name, 'shape', [d.dim_value for d in inp.type.tensor_type.shape.dim])

print('\nOutputs:')
for out in sess.get_outputs():
    print('-', out.name, 'shape', [d.dim_value for d in out.type.tensor_type.shape.dim])

print('\nSuggested mapping (heuristic):')
for inp in sess.get_inputs():
    name = inp.name.lower()
    if 'ema20' in name:
        print(name, '-> ema20')
    elif 'ema50' in name:
        print(name, '-> ema50')
    elif 'rsi' in name:
        print(name, '-> rsi')
    elif 'price' in name or 'last' in name:
        print(name, '-> last_price')
    else:
        print(name, '-> (no suggestion)')
