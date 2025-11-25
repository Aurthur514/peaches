# Compute derived features from OCR / market data
def compute_features(parsed):
    ind = parsed.get('indicators', {})
    features = {
        'last_price': parsed.get('last_price', 0.0),
        'ema20': ind.get('EMA20', 0.0),
        'ema50': ind.get('EMA50', 0.0),
        'rsi': ind.get('RSI', 50),
        'explanations': []
    }
    # simple explanations
    if features['ema20'] > features['ema50']:
        features['explanations'].append('EMA20 > EMA50')
    else:
        features['explanations'].append('EMA20 <= EMA50')
    if features['rsi'] < 35:
        features['explanations'].append('RSI oversold')
    return features
