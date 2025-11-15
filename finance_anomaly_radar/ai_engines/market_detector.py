"""
Market Manipulation Detector for Finance Anomaly Radar
Uses LSTM and Isolation Forest to detect abnormal market movements and pump-and-dump schemes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
except ImportError:
    print("Warning: TensorFlow not available. Using fallback methods for market detection.")
    tf = None
    Sequential = None
    LSTM = None
    Dense = None
    Dropout = None
    BatchNormalization = None
    Adam = None
    EarlyStopping = None
    ReduceLROnPlateau = None
    load_model = None

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import classification_report
from scipy import stats
import joblib
from loguru import logger

class MarketManipulationDetector:
    """Detects market manipulation using LSTM and anomaly detection algorithms."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.window_size = config.get('window_size', 100)
        self.anomaly_threshold = config.get('anomaly_threshold', 2.5)
        self.min_volume_spike = config.get('min_volume_spike', 3.0)
        self.lookback_periods = config.get('lookback_periods', 50)
        
        # Models
        self.lstm_model = None
        self.anomaly_detector = None
        self.scaler = MinMaxScaler()
        self.volume_scaler = StandardScaler()
        
        # Model states
        self.is_trained = False
        self.model_metrics = {}
        
        # Market pattern databases
        self.pump_patterns = self._load_pump_patterns()
        self.manipulation_indicators = self._load_manipulation_indicators()
        
        self._initialize_models()
    
    def _load_pump_patterns(self) -> Dict[str, Any]:
        """Load known pump-and-dump patterns."""
        return {
            'price_patterns': {
                'rapid_increase_threshold': 0.2,  # 20% increase
                'rapid_increase_timeframe': 3600,  # 1 hour
                'dump_threshold': 0.15,  # 15% decrease after pump
                'pump_duration_max': 7200,  # 2 hours max pump duration
                'volume_spike_ratio': 5.0  # 5x normal volume
            },
            'volume_patterns': {
                'sudden_spike_multiplier': 10,
                'sustained_high_volume_hours': 2,
                'volume_decay_pattern': 0.5  # Volume should decay after pump
            },
            'order_book_patterns': {
                'bid_ask_spread_increase': 2.0,
                'large_orders_ratio': 0.7,
                'order_cancellation_rate': 0.8
            },
            'timing_patterns': {
                'coordinated_buying_window': 300,  # 5 minutes
                'off_hours_activity': True,  # Activity during off-market hours
                'weekend_manipulation': True
            }
        }
    
    def _load_manipulation_indicators(self) -> Dict[str, Any]:
        """Load market manipulation indicators."""
        return {
            'spoofing_indicators': {
                'large_order_placement': 0.1,  # Orders > 10% of average
                'quick_cancellation_rate': 0.9,  # 90% cancellation rate
                'layering_depth': 5  # Multiple price levels
            },
            'wash_trading_indicators': {
                'self_trade_ratio': 0.3,  # 30% self-trades
                'circular_trading_pattern': True,
                'artificial_volume_inflation': 2.0
            },
            'insider_trading_indicators': {
                'unusual_pre_news_activity': True,
                'informed_trading_pattern': 0.8,
                'timing_correlation': 0.7
            }
        }
    
    def _initialize_models(self) -> None:
        """Initialize LSTM and anomaly detection models."""
        try:
            # Try to load pre-trained models
            model_path = self.config.get('model_path')
            if model_path:
                self._load_models(model_path)
            else:
                self._create_models()
        
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            self._create_fallback_models()
    
    def _create_models(self) -> None:
        """Create new LSTM and anomaly detection models."""
        if tf and Sequential:
            # Create LSTM model for price prediction
            self.lstm_model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(self.window_size, 5)),  # 5 features: OHLCV
                Dropout(0.2),
                BatchNormalization(),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(25, return_sequences=False),
                Dropout(0.2),
                Dense(25, activation='relu'),
                Dense(1, activation='linear')
            ])
            
            self.lstm_model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',
                metrics=['mae']
            )
        
        # Create Isolation Forest for anomaly detection
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # 10% expected anomalies
            random_state=42,
            n_estimators=100
        )
        
        logger.info("Models created successfully")
    
    def _create_fallback_models(self) -> None:
        """Create fallback models when TensorFlow is not available."""
        # Use only Isolation Forest for anomaly detection
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        logger.info("Fallback models created (Isolation Forest only)")
    
    async def analyze_market_data(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market data for manipulation patterns.
        
        Args:
            market_data: List of market data points
            
        Returns:
            Analysis results with manipulation probability and indicators
        """
        analysis_result = {
            'timestamp': datetime.utcnow().isoformat(),
            'data_points_analyzed': len(market_data),
            'manipulation_probability': 0.0,
            'risk_level': 'LOW',
            'detected_patterns': [],
            'anomaly_scores': {},
            'statistical_indicators': {},
            'lstm_predictions': {},
            'recommendation': 'HOLD'
        }
        
        try:
            if not market_data or len(market_data) < 10:
                analysis_result['error'] = 'Insufficient data for analysis'
                return analysis_result
            
            # Convert to DataFrame for analysis
            df = self._prepare_market_dataframe(market_data)
            
            # Statistical analysis
            statistical_result = self._analyze_statistical_patterns(df)
            analysis_result['statistical_indicators'] = statistical_result
            
            # LSTM-based prediction (if available)
            if self.lstm_model and len(df) >= self.window_size:
                lstm_result = await self._analyze_with_lstm(df)
                analysis_result['lstm_predictions'] = lstm_result
            
            # Anomaly detection
            anomaly_result = self._detect_anomalies(df)
            analysis_result['anomaly_scores'] = anomaly_result
            
            # Pattern detection
            pattern_result = self._detect_manipulation_patterns(df)
            analysis_result['detected_patterns'] = pattern_result
            
            # Volume analysis
            volume_result = self._analyze_volume_patterns(df)
            analysis_result['volume_analysis'] = volume_result
            
            # Calculate final manipulation probability
            manipulation_prob = self._calculate_manipulation_probability(analysis_result)
            analysis_result['manipulation_probability'] = manipulation_prob
            analysis_result['risk_level'] = self._determine_risk_level(manipulation_prob)
            analysis_result['recommendation'] = self._get_trading_recommendation(manipulation_prob)
        
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def _prepare_market_dataframe(self, market_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare market data for analysis."""
        # Extract relevant fields and create DataFrame
        df_data = []
        
        for data_point in market_data:
            if data_point.get('asset_type') in ['stock', 'cryptocurrency']:
                df_data.append({
                    'timestamp': pd.to_datetime(data_point['timestamp']),
                    'symbol': data_point['symbol'],
                    'price': data_point['price'],
                    'volume': data_point.get('volume', 0),
                    'high': data_point.get('high', data_point['price']),
                    'low': data_point.get('low', data_point['price']),
                    'open': data_point.get('open', data_point['price']),
                    'price_change_percent': data_point.get('price_change_percent', 0),
                    'volume_ratio': data_point.get('volume_ratio', 1.0)
                })
        
        if not df_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(df_data)
        df = df.sort_values('timestamp')
        
        # Calculate additional technical indicators
        df['returns'] = df['price'].pct_change()
        df['volatility'] = df['returns'].rolling(window=10).std()
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['price_ma'] = df['price'].rolling(window=20).mean()
        
        return df.fillna(0)
    
    def _analyze_statistical_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze statistical patterns in market data."""
        if df.empty:
            return {}
        
        try:
            latest_data = df.iloc[-10:]  # Last 10 data points
            
            return {
                'price_volatility': float(latest_data['returns'].std()),
                'volume_surge': float(latest_data['volume'].max() / latest_data['volume'].mean()) if latest_data['volume'].mean() > 0 else 0,
                'price_momentum': float(latest_data['price'].iloc[-1] - latest_data['price'].iloc[0]) / latest_data['price'].iloc[0] if latest_data['price'].iloc[0] > 0 else 0,
                'abnormal_returns': float(abs(latest_data['returns'].mean()) / latest_data['returns'].std()) if latest_data['returns'].std() > 0 else 0,
                'volume_price_correlation': float(latest_data['volume'].corr(latest_data['price'])) if len(latest_data) > 1 else 0,
                'trend_strength': self._calculate_trend_strength(latest_data)
            }
        
        except Exception as e:
            logger.warning(f"Error in statistical analysis: {e}")
            return {}
    
    async def _analyze_with_lstm(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market data using LSTM model."""
        if not self.lstm_model or df.empty or len(df) < self.window_size:
            return {}
        
        try:
            # Prepare data for LSTM
            features = ['price', 'volume', 'high', 'low', 'open']
            data = df[features].values
            
            # Scale data
            scaled_data = self.scaler.fit_transform(data)
            
            # Create sequences
            X = []
            for i in range(self.window_size, len(scaled_data)):
                X.append(scaled_data[i-self.window_size:i])
            
            if not X:
                return {}
            
            X = np.array(X)
            
            # Predict
            predictions = self.lstm_model.predict(X)
            
            # Calculate prediction accuracy/deviation
            actual_prices = data[self.window_size:, 0]  # Price column
            predicted_prices = self.scaler.inverse_transform(
                np.concatenate([predictions, np.zeros((len(predictions), 4))], axis=1)
            )[:, 0]
            
            deviation = np.abs((predicted_prices - actual_prices) / actual_prices)
            
            return {
                'prediction_accuracy': float(1 - np.mean(deviation)),
                'average_deviation': float(np.mean(deviation)),
                'max_deviation': float(np.max(deviation)),
                'prediction_anomaly_score': float(np.mean(deviation > 0.1))  # Predictions with >10% deviation
            }
        
        except Exception as e:
            logger.warning(f"LSTM analysis failed: {e}")
            return {}
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest."""
        if df.empty or not self.anomaly_detector:
            return {}
        
        try:
            # Prepare features for anomaly detection
            features = ['price', 'volume', 'returns', 'volatility', 'volume_ratio']
            available_features = [f for f in features if f in df.columns]
            
            if not available_features:
                return {}
            
            X = df[available_features].values
            X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
            
            # Fit and predict anomalies
            if not hasattr(self.anomaly_detector, 'n_features_in_') or self.anomaly_detector.n_features_in_ != X.shape[1]:
                self.anomaly_detector.fit(X)
            
            anomaly_scores = self.anomaly_detector.decision_function(X)
            anomalies = self.anomaly_detector.predict(X)
            
            return {
                'anomaly_count': int(np.sum(anomalies == -1)),
                'anomaly_ratio': float(np.mean(anomalies == -1)),
                'average_anomaly_score': float(np.mean(anomaly_scores)),
                'min_anomaly_score': float(np.min(anomaly_scores)),
                'recent_anomalies': int(np.sum(anomalies[-10:] == -1))  # Anomalies in last 10 points
            }
        
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
            return {}
    
    def _detect_manipulation_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect specific manipulation patterns."""
        patterns = []
        
        if df.empty:
            return patterns
        
        try:
            # Pump and dump detection
            pump_dump = self._detect_pump_and_dump(df)
            if pump_dump:
                patterns.extend(pump_dump)
            
            # Spoofing detection
            spoofing = self._detect_spoofing_patterns(df)
            if spoofing:
                patterns.extend(spoofing)
            
            # Volume manipulation
            volume_manip = self._detect_volume_manipulation(df)
            if volume_manip:
                patterns.extend(volume_manip)
            
            # Price ramping
            price_ramping = self._detect_price_ramping(df)
            if price_ramping:
                patterns.extend(price_ramping)
        
        except Exception as e:
            logger.warning(f"Pattern detection failed: {e}")
        
        return patterns
    
    def _detect_pump_and_dump(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect pump and dump patterns."""
        patterns = []
        
        if len(df) < 20:
            return patterns
        
        try:
            # Look for rapid price increases followed by decreases
            recent_data = df.iloc[-20:]  # Last 20 periods
            
            # Calculate rolling price changes
            price_changes = recent_data['price'].pct_change(periods=5)  # 5-period change
            volume_changes = recent_data['volume'] / recent_data['volume'].rolling(10).mean()
            
            # Pump detection criteria
            rapid_increase = price_changes.max() > self.pump_patterns['price_patterns']['rapid_increase_threshold']
            high_volume = volume_changes.max() > self.pump_patterns['price_patterns']['volume_spike_ratio']
            
            if rapid_increase and high_volume:
                # Look for subsequent dump
                pump_idx = price_changes.idxmax()
                post_pump_data = recent_data.loc[pump_idx:]
                
                if len(post_pump_data) > 5:
                    post_pump_decline = (post_pump_data['price'].iloc[-1] - post_pump_data['price'].iloc[0]) / post_pump_data['price'].iloc[0]
                    
                    if post_pump_decline < -self.pump_patterns['price_patterns']['dump_threshold']:
                        patterns.append({
                            'pattern_type': 'pump_and_dump',
                            'confidence': 0.8,
                            'pump_magnitude': float(price_changes.max()),
                            'dump_magnitude': float(abs(post_pump_decline)),
                            'volume_spike': float(volume_changes.max()),
                            'description': 'Rapid price increase followed by significant decline with volume spike'
                        })
        
        except Exception as e:
            logger.warning(f"Pump and dump detection failed: {e}")
        
        return patterns
    
    def _detect_spoofing_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect spoofing patterns (simplified version)."""
        patterns = []
        
        try:
            # Look for unusual price movements with low volume
            recent_data = df.iloc[-10:]
            
            if len(recent_data) > 5:
                price_volatility = recent_data['returns'].std()
                avg_volume = recent_data['volume'].mean()
                
                # High volatility with low volume might indicate spoofing
                if price_volatility > 0.05 and avg_volume < recent_data['volume_ma'].iloc[-1] * 0.5:
                    patterns.append({
                        'pattern_type': 'potential_spoofing',
                        'confidence': 0.6,
                        'volatility': float(price_volatility),
                        'volume_ratio': float(avg_volume / recent_data['volume_ma'].iloc[-1]) if recent_data['volume_ma'].iloc[-1] > 0 else 0,
                        'description': 'High price volatility with unusually low volume'
                    })
        
        except Exception as e:
            logger.warning(f"Spoofing detection failed: {e}")
        
        return patterns
    
    def _detect_volume_manipulation(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume manipulation patterns."""
        patterns = []
        
        try:
            if 'volume_ratio' in df.columns:
                recent_ratios = df['volume_ratio'].iloc[-10:]
                
                # Detect sustained high volume without price movement
                high_volume_periods = recent_ratios > 3.0
                price_changes = df['returns'].iloc[-10:].abs()
                
                if high_volume_periods.sum() > 5 and price_changes.mean() < 0.02:
                    patterns.append({
                        'pattern_type': 'volume_manipulation',
                        'confidence': 0.7,
                        'high_volume_periods': int(high_volume_periods.sum()),
                        'average_price_change': float(price_changes.mean()),
                        'description': 'High volume activity without corresponding price movement'
                    })
        
        except Exception as e:
            logger.warning(f"Volume manipulation detection failed: {e}")
        
        return patterns
    
    def _detect_price_ramping(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect price ramping patterns."""
        patterns = []
        
        try:
            if len(df) > 10:
                recent_prices = df['price'].iloc[-10:]
                
                # Look for consistent upward trend in small increments
                price_increases = recent_prices.diff() > 0
                consecutive_increases = 0
                max_consecutive = 0
                
                for increase in price_increases:
                    if increase:
                        consecutive_increases += 1
                        max_consecutive = max(max_consecutive, consecutive_increases)
                    else:
                        consecutive_increases = 0
                
                if max_consecutive >= 6:  # 6 consecutive small increases
                    total_increase = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0]
                    
                    patterns.append({
                        'pattern_type': 'price_ramping',
                        'confidence': 0.7,
                        'consecutive_increases': int(max_consecutive),
                        'total_price_increase': float(total_increase),
                        'description': 'Consistent small price increases suggesting artificial ramping'
                    })
        
        except Exception as e:
            logger.warning(f"Price ramping detection failed: {e}")
        
        return patterns
    
    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns for manipulation indicators."""
        if df.empty or 'volume' not in df.columns:
            return {}
        
        try:
            recent_volume = df['volume'].iloc[-10:]
            historical_volume = df['volume'].iloc[:-10] if len(df) > 10 else df['volume']
            
            return {
                'volume_spike_factor': float(recent_volume.max() / historical_volume.mean()) if historical_volume.mean() > 0 else 0,
                'volume_consistency': float(1 - recent_volume.std() / recent_volume.mean()) if recent_volume.mean() > 0 else 0,
                'volume_trend': 'increasing' if recent_volume.iloc[-1] > recent_volume.iloc[0] else 'decreasing',
                'unusual_volume_periods': int(sum(recent_volume > historical_volume.mean() + 2 * historical_volume.std()))
            }
        
        except Exception as e:
            logger.warning(f"Volume analysis failed: {e}")
            return {}
    
    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength using linear regression."""
        try:
            if len(data) < 5:
                return 0.0
            
            x = np.arange(len(data))
            y = data['price'].values
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Return R-squared as trend strength
            return float(r_value ** 2)
        
        except Exception:
            return 0.0
    
    def _calculate_manipulation_probability(self, analysis_result: Dict[str, Any]) -> float:
        """Calculate overall manipulation probability."""
        try:
            score = 0.0
            
            # Statistical indicators (30% weight)
            stats = analysis_result.get('statistical_indicators', {})
            if stats.get('volume_surge', 0) > 5:
                score += 0.1
            if abs(stats.get('price_momentum', 0)) > 0.2:
                score += 0.1
            if stats.get('abnormal_returns', 0) > 3:
                score += 0.1
            
            # Anomaly scores (25% weight)
            anomalies = analysis_result.get('anomaly_scores', {})
            anomaly_ratio = anomalies.get('anomaly_ratio', 0)
            score += min(anomaly_ratio * 0.25, 0.25)
            
            # Pattern detection (35% weight)
            patterns = analysis_result.get('detected_patterns', [])
            pattern_score = 0
            for pattern in patterns:
                if pattern['pattern_type'] == 'pump_and_dump':
                    pattern_score += 0.2
                elif pattern['pattern_type'] in ['potential_spoofing', 'volume_manipulation']:
                    pattern_score += 0.1
                elif pattern['pattern_type'] == 'price_ramping':
                    pattern_score += 0.05
            score += min(pattern_score, 0.35)
            
            # LSTM predictions (10% weight)
            lstm = analysis_result.get('lstm_predictions', {})
            if lstm.get('prediction_anomaly_score', 0) > 0.3:
                score += 0.1
            
            return min(score, 1.0)
        
        except Exception as e:
            logger.error(f"Error calculating manipulation probability: {e}")
            return 0.0
    
    def _determine_risk_level(self, probability: float) -> str:
        """Determine risk level based on manipulation probability."""
        if probability >= 0.7:
            return 'HIGH'
        elif probability >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_trading_recommendation(self, probability: float) -> str:
        """Get trading recommendation based on manipulation probability."""
        if probability >= 0.8:
            return 'AVOID'
        elif probability >= 0.6:
            return 'CAUTION'
        elif probability >= 0.3:
            return 'MONITOR'
        else:
            return 'NORMAL'
    
    def train_model(self, training_data: List[Dict[str, Any]], labels: List[int]) -> Dict[str, Any]:
        """Train the manipulation detection model.
        
        Args:
            training_data: Market data for training
            labels: Labels (0 = normal, 1 = manipulation)
            
        Returns:
            Training metrics
        """
        try:
            df = self._prepare_market_dataframe(training_data)
            
            if df.empty or len(df) != len(labels):
                raise ValueError("Training data and labels length mismatch")
            
            # Train anomaly detector
            features = ['price', 'volume', 'returns', 'volatility', 'volume_ratio']
            available_features = [f for f in features if f in df.columns]
            X = df[available_features].values
            X = np.nan_to_num(X)
            
            self.anomaly_detector.fit(X)
            
            # Train LSTM if available and sufficient data
            if self.lstm_model and len(df) >= self.window_size * 2:
                lstm_metrics = self._train_lstm_model(df, labels)
                self.model_metrics['lstm'] = lstm_metrics
            
            self.is_trained = True
            
            # Evaluate on training data
            predictions = self.anomaly_detector.predict(X)
            accuracy = np.mean((predictions == -1) == np.array(labels))
            
            self.model_metrics['anomaly_detector'] = {
                'accuracy': float(accuracy),
                'training_samples': len(labels)
            }
            
            logger.info("Model training completed successfully")
            
            return self.model_metrics
        
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {'error': str(e)}
    
    def _train_lstm_model(self, df: pd.DataFrame, labels: List[int]) -> Dict[str, Any]:
        """Train LSTM model for price prediction."""
        try:
            if not self.lstm_model:
                return {'error': 'LSTM model not available'}
            
            # Prepare sequences for LSTM training
            features = ['price', 'volume', 'high', 'low', 'open']
            data = df[features].values
            
            scaled_data = self.scaler.fit_transform(data)
            
            X, y = [], []
            for i in range(self.window_size, len(scaled_data)):
                X.append(scaled_data[i-self.window_size:i])
                y.append(scaled_data[i, 0])  # Predict price
            
            X, y = np.array(X), np.array(y)
            
            # Split data
            split = int(0.8 * len(X))
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]
            
            # Callbacks
            callbacks = []
            if EarlyStopping:
                callbacks.append(EarlyStopping(patience=10, restore_best_weights=True))
            if ReduceLROnPlateau:
                callbacks.append(ReduceLROnPlateau(factor=0.5, patience=5))
            
            # Train model
            history = self.lstm_model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=50,
                batch_size=32,
                callbacks=callbacks,
                verbose=0
            )
            
            # Evaluate
            train_loss = self.lstm_model.evaluate(X_train, y_train, verbose=0)
            val_loss = self.lstm_model.evaluate(X_val, y_val, verbose=0)
            
            return {
                'train_loss': float(train_loss[0]) if isinstance(train_loss, list) else float(train_loss),
                'val_loss': float(val_loss[0]) if isinstance(val_loss, list) else float(val_loss),
                'epochs_trained': len(history.history['loss']),
                'training_samples': len(X_train)
            }
        
        except Exception as e:
            logger.error(f"LSTM training failed: {e}")
            return {'error': str(e)}
    
    def save_model(self, path: str) -> None:
        """Save trained models."""
        try:
            if self.lstm_model:
                self.lstm_model.save(f"{path}_lstm.h5")
            
            if self.anomaly_detector:
                joblib.dump(self.anomaly_detector, f"{path}_anomaly.pkl")
            
            joblib.dump(self.scaler, f"{path}_scaler.pkl")
            
            logger.info(f"Models saved to {path}")
        
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self, path: str) -> None:
        """Load pre-trained models."""
        try:
            if tf and load_model:
                try:
                    self.lstm_model = load_model(f"{path}_lstm.h5")
                except:
                    pass
            
            self.anomaly_detector = joblib.load(f"{path}_anomaly.pkl")
            self.scaler = joblib.load(f"{path}_scaler.pkl")
            
            self.is_trained = True
            logger.info(f"Models loaded from {path}")
        
        except Exception as e:
            logger.warning(f"Could not load models from {path}: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            'is_trained': self.is_trained,
            'has_lstm': self.lstm_model is not None,
            'has_anomaly_detector': self.anomaly_detector is not None,
            'window_size': self.window_size,
            'anomaly_threshold': self.anomaly_threshold,
            'model_metrics': self.model_metrics
        }