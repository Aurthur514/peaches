"""Predictor wrapper that prefers an ONNX model if available, otherwise falls back to a heuristic.

Drop an ONNX model at `../models/model.onnx` (relative to this file) to enable model-based prediction.
"""
import os
from pathlib import Path
from backend import config

# Resolve model path via config.resolve_model_path()
MODEL_PATH = config.resolve_model_path()

_onnx_session = None
_onnx_available = False
try:
    import onnxruntime as ort
    _onnx_available = True
except Exception:
    _onnx_available = False


def _load_onnx():
    global _onnx_session
    if not _onnx_available:
        return None
    if _onnx_session is not None:
        return _onnx_session
    if MODEL_PATH.exists():
        try:
            _onnx_session = ort.InferenceSession(str(MODEL_PATH))
            return _onnx_session
        except Exception:
            _onnx_session = None
            return None
    return None


def _heuristic_predict(features):
    ema20 = features.get('ema20', 0)
    ema50 = features.get('ema50', 0)
    rsi = features.get('rsi', 50)
    explanations = features.get('explanations', [])

    score = 0.5
    if ema20 > ema50:
        score += 0.15
    else:
        score -= 0.1
    if rsi < 35:
        score += 0.1
    score = max(0.01, min(0.99, score))

    if score > 0.65:
        signal = 'BUY'
    elif score < 0.35:
        signal = 'SELL'
    else:
        signal = 'NO TRADE'

    return {
        'signal': signal,
        'confidence': round(score, 3),
        'expected_move_5min': '+0.4%' if signal == 'BUY' else ('-0.3%' if signal == 'SELL' else '0%'),
        'reason': explanations,
        'model': 'heuristic'
    }


def predict_signal(features):
    """Try ONNX model first; fall back to heuristic.

    Expected features: dict with numeric values. If ONNX model expects other inputs, adapt this wrapper.
    """
    sess = _load_onnx()
    if sess is not None:
        try:
            # Basic mapping: attempt to feed EMA and RSI values as float inputs named accordingly
            input_names = [i.name for i in sess.get_inputs()]
            feed = {}
            # Use ONNX input map from config if provided
            input_map = {k.lower(): v for k, v in getattr(config, 'ONNX_INPUT_MAP', {}).items()}
            for name in input_names:
                lname = name.lower()
                mapped_key = None
                # config-based mapping
                for ik, fk in input_map.items():
                    if ik in lname or ik == lname:
                        mapped_key = fk
                        break
                if mapped_key is None:
                    # fallback heuristics
                    if 'ema20' in lname:
                        mapped_key = 'ema20'
                    elif 'ema50' in lname:
                        mapped_key = 'ema50'
                    elif 'rsi' in lname:
                        mapped_key = 'rsi'
                    elif 'price' in lname or 'last' in lname:
                        mapped_key = 'last_price'
                    else:
                        mapped_key = None

                if mapped_key is not None:
                    feed[name] = float(features.get(mapped_key, 0.0))
                else:
                    feed[name] = 0.0

            out = sess.run(None, feed)
            # interpret output: if single scalar or probability-like
            if isinstance(out, list) and len(out) > 0:
                val = out[0]
                # handle common shapes
                try:
                    score = float(val.flatten()[0])
                except Exception:
                    # best-effort fallback
                    score = 0.5
            else:
                score = 0.5

            score = max(0.01, min(0.99, score))
            if score > 0.65:
                signal = 'BUY'
            elif score < 0.35:
                signal = 'SELL'
            else:
                signal = 'NO TRADE'

            return {
                'signal': signal,
                'confidence': round(score, 3),
                'expected_move_5min': '+0.4%' if signal == 'BUY' else ('-0.3%' if signal == 'SELL' else '0%'),
                'reason': features.get('explanations', []),
                'model': 'onnx'
            }
        except Exception:
            # any failure -> fallback
            return _heuristic_predict(features)
    else:
        return _heuristic_predict(features)


def reload_onnx():
    """Clear cached ONNX session and attempt to load again. Returns True if loaded."""
    global _onnx_session
    _onnx_session = None
    sess = _load_onnx()
    return sess is not None
