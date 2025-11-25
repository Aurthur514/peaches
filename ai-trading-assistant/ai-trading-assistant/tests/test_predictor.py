import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.predictor import predict_signal


def test_predictor_returns_expected_keys():
    features = {'ema20': 101.0, 'ema50': 100.0, 'rsi': 30, 'last_price': 120.0, 'explanations': ['test']}
    out = predict_signal(features)
    assert isinstance(out, dict)
    assert 'signal' in out
    assert 'confidence' in out
    assert 'reason' in out
