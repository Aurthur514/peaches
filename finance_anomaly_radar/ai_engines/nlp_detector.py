"""
NLP Scam Detector for Finance Anomaly Radar
Uses BERT and other NLP techniques to detect scam patterns in text messages.
"""

import re
import pickle
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    import torch
except ImportError:
    print("Warning: transformers and torch not available. Using fallback NLP methods.")
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    pipeline = None
    torch = None

from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import joblib
from loguru import logger

class NLPScamDetector:
    """BERT-based NLP detector for identifying scam messages and content."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('model_name', 'distilbert-base-uncased')
        self.confidence_threshold = config.get('confidence_threshold', 0.75)
        self.max_length = config.get('max_length', 512)
        
        # Initialize models
        self.bert_model = None
        self.tokenizer = None
        self.classifier_pipeline = None
        self.fallback_model = None
        self.tfidf_vectorizer = None
        
        # Scam patterns and keywords
        self.scam_patterns = self._load_scam_patterns()
        self.language_patterns = self._load_language_patterns()
        
        self._initialize_models()
    
    def _load_scam_patterns(self) -> Dict[str, List[str]]:
        """Load comprehensive scam patterns and keywords."""
        return {
            'financial_scams': [
                'guaranteed returns', 'risk-free investment', 'double your money',
                'get rich quick', 'easy money', 'passive income', 'financial freedom',
                'exclusive investment opportunity', 'limited time offer', 
                'secret trading method', 'insider information', 'proven strategy'
            ],
            'crypto_scams': [
                'cryptocurrency mining', 'crypto trading bot', 'altcoin investment',
                'bitcoin doubler', 'ethereum giveaway', 'new ico', 'defi project',
                'yield farming', 'staking rewards', 'nft investment', 'meme coin'
            ],
            'pyramid_schemes': [
                'multi-level marketing', 'network marketing', 'referral program',
                'earn by recruiting', 'build your downline', 'matrix system',
                'binary plan', 'spillover system', 'forced matrix'
            ],
            'urgency_tactics': [
                'act now', 'limited spots', 'offer expires', 'hurry up',
                'don\'t miss out', 'last chance', 'time sensitive', 'urgent action',
                'immediate response required', 'deadline approaching'
            ],
            'social_proof': [
                'others are making money', 'successful members', 'testimonials',
                'join thousands', 'exclusive group', 'vip members only',
                'verified results', 'proven track record'
            ],
            'authority_claims': [
                'financial expert', 'trading guru', 'investment advisor',
                'certified professional', 'years of experience', 'market insider',
                'wall street veteran', 'hedge fund manager'
            ],
            'contact_methods': [
                'whatsapp group', 'telegram channel', 'private message',
                'click link below', 'visit our website', 'download app',
                'call this number', 'send email to', 'dm for details'
            ],
            'payment_requests': [
                'send money now', 'transfer funds', 'make payment',
                'deposit required', 'registration fee', 'activation amount',
                'processing charges', 'membership fee', 'wallet transfer'
            ]
        }
    
    def _load_language_patterns(self) -> Dict[str, Any]:
        """Load language-specific patterns for different regions."""
        return {
            'hindi_romanized': [
                'paisa', 'kamao', 'invest', 'group join karo', 'zarur try karo',
                'guarantee hai', 'risk nahi hai', 'bharosa karo'
            ],
            'broken_english': [
                'you can earn money very easily',
                'i am giving you guarantee',
                'no risk in this business',
                'join fast before group is full'
            ],
            'emotional_manipulation': [
                'change your life', 'financial struggle', 'family future',
                'children education', 'dream house', 'luxury lifestyle'
            ]
        }
    
    def _initialize_models(self) -> None:
        """Initialize BERT and fallback models."""
        try:
            if AutoTokenizer and AutoModelForSequenceClassification:
                # Try to load pre-trained BERT model
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
                # For this demo, we'll use a general sentiment classifier
                # In production, you would fine-tune BERT on scam detection data
                self.classifier_pipeline = pipeline(
                    'text-classification',
                    model=self.model_name,
                    tokenizer=self.tokenizer,
                    device=0 if torch and torch.cuda.is_available() else -1
                )
                
                logger.info(f"BERT model initialized: {self.model_name}")
            
        except Exception as e:
            logger.warning(f"Could not initialize BERT model: {e}")
        
        # Initialize fallback TF-IDF + RandomForest model
        self._initialize_fallback_model()
    
    def _initialize_fallback_model(self) -> None:
        """Initialize fallback model using traditional ML techniques."""
        try:
            # Try to load pre-trained models
            model_path = self.config.get('fallback_model_path')
            if model_path:
                try:
                    self.fallback_model = joblib.load(model_path)
                    self.tfidf_vectorizer = joblib.load(model_path.replace('.pkl', '_tfidf.pkl'))
                    logger.info("Loaded pre-trained fallback model")
                    return
                except FileNotFoundError:
                    pass
            
            # Create and train a new fallback model
            self._train_fallback_model()
            
        except Exception as e:
            logger.error(f"Error initializing fallback model: {e}")
    
    def _train_fallback_model(self) -> None:
        """Train a fallback model using synthetic data and patterns."""
        try:
            # Generate synthetic training data
            training_data = self._generate_synthetic_training_data()
            
            if training_data:
                texts, labels = zip(*training_data)
                
                # Create TF-IDF vectorizer
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 3),
                    stop_words='english',
                    lowercase=True
                )
                
                X = self.tfidf_vectorizer.fit_transform(texts)
                y = np.array(labels)
                
                # Train Random Forest classifier
                self.fallback_model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                
                self.fallback_model.fit(X, y)
                
                logger.info("Fallback model trained successfully")
        
        except Exception as e:
            logger.error(f"Error training fallback model: {e}")
    
    def _generate_synthetic_training_data(self) -> List[Tuple[str, int]]:
        """Generate synthetic training data for scam detection."""
        training_data = []
        
        # Positive examples (scams)
        scam_templates = [
            "Join our exclusive {investment_type} group! Guaranteed {percentage}% returns in {timeframe}!",
            "Limited time offer: {authority} is sharing {method} for {benefit}. Act now!",
            "Urgent: Send {amount} to activate your account and receive {reward}.",
            "Secret {trading_type} strategy revealed! {social_proof}. Contact {contact_method}.",
            "Don't miss out! {urgency_phrase} to join our {group_type} and {benefit}."
        ]
        
        # Generate scam examples
        for template in scam_templates:
            for _ in range(20):  # Generate 20 variations per template
                text = self._fill_template(template)
                training_data.append((text, 1))  # 1 = scam
        
        # Negative examples (legitimate messages)
        legitimate_examples = [
            "Hi, how are you doing today?",
            "Meeting scheduled for 3 PM tomorrow.",
            "Thank you for your purchase. Your order will be delivered soon.",
            "Happy birthday! Hope you have a wonderful day.",
            "The weather is beautiful today, perfect for a walk.",
            "Please review the attached document and provide feedback.",
            "Reminder: Your subscription expires next month.",
            "Great job on the presentation! The client was impressed.",
            "Would you like to grab lunch tomorrow?",
            "The movie was amazing! You should definitely watch it."
        ] * 20  # Repeat to balance dataset
        
        for text in legitimate_examples:
            training_data.append((text, 0))  # 0 = legitimate
        
        return training_data
    
    def _fill_template(self, template: str) -> str:
        """Fill template with random scam-related terms."""
        import random
        
        replacements = {
            'investment_type': ['crypto', 'forex', 'stock', 'binary options', 'commodity'],
            'percentage': ['200', '500', '1000', '300', '750'],
            'timeframe': ['30 days', '1 week', '24 hours', '3 months', '1 month'],
            'authority': ['Expert trader', 'Financial guru', 'Market insider', 'Investment advisor'],
            'method': ['trading signals', 'secret strategy', 'proven system', 'exclusive method'],
            'benefit': ['financial freedom', 'passive income', 'easy money', 'guaranteed profits'],
            'amount': ['₹1000', '$100', '₹5000', '$500', '₹10000'],
            'reward': ['₹50000', '$5000', '₹100000', '$10000', 'double amount'],
            'trading_type': ['crypto', 'forex', 'binary', 'stock', 'option'],
            'social_proof': ['Join 10000+ successful traders', 'Verified by experts', '99% success rate'],
            'contact_method': ['WhatsApp', 'Telegram', 'our website', 'this link'],
            'urgency_phrase': ['Only 24 hours left', 'Limited spots available', 'Offer expires today'],
            'group_type': ['VIP group', 'exclusive community', 'trading signals group']
        }
        
        result = template
        for placeholder, options in replacements.items():
            if f'{{{placeholder}}}' in result:
                result = result.replace(f'{{{placeholder}}}', random.choice(options))
        
        return result
    
    async def analyze_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze text for scam indicators.
        
        Args:
            text: Text to analyze
            context: Additional context (sender info, platform, etc.)
            
        Returns:
            Analysis results with scam probability and indicators
        """
        analysis_result = {
            'text': text,
            'timestamp': datetime.utcnow().isoformat(),
            'scam_probability': 0.0,
            'confidence': 0.0,
            'risk_level': 'LOW',
            'indicators': {
                'pattern_matches': [],
                'language_flags': [],
                'structural_anomalies': [],
                'sentiment_analysis': {},
                'entity_extraction': {}
            },
            'model_predictions': {}
        }
        
        try:
            # BERT-based analysis
            if self.classifier_pipeline:
                bert_result = await self._analyze_with_bert(text)
                analysis_result['model_predictions']['bert'] = bert_result
            
            # Fallback model analysis
            if self.fallback_model:
                fallback_result = self._analyze_with_fallback(text)
                analysis_result['model_predictions']['fallback'] = fallback_result
            
            # Pattern-based analysis
            pattern_result = self._analyze_patterns(text)
            analysis_result['indicators']['pattern_matches'] = pattern_result
            
            # Language analysis
            language_result = self._analyze_language(text)
            analysis_result['indicators']['language_flags'] = language_result
            
            # Structural analysis
            structural_result = self._analyze_structure(text)
            analysis_result['indicators']['structural_anomalies'] = structural_result
            
            # Sentiment analysis
            sentiment_result = self._analyze_sentiment(text)
            analysis_result['indicators']['sentiment_analysis'] = sentiment_result
            
            # Entity extraction
            entity_result = self._extract_entities(text)
            analysis_result['indicators']['entity_extraction'] = entity_result
            
            # Calculate final probability
            final_probability, confidence = self._calculate_final_probability(analysis_result)
            analysis_result['scam_probability'] = final_probability
            analysis_result['confidence'] = confidence
            analysis_result['risk_level'] = self._determine_risk_level(final_probability)
            
        except Exception as e:
            logger.error(f"Error in text analysis: {e}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    async def _analyze_with_bert(self, text: str) -> Dict[str, Any]:
        """Analyze text using BERT model."""
        try:
            # Truncate text if too long
            if len(text) > self.max_length:
                text = text[:self.max_length]
            
            # Get prediction from pipeline
            result = self.classifier_pipeline(text)
            
            # Convert to scam probability
            # Note: This is simplified - in production, you'd fine-tune BERT for scam detection
            if isinstance(result, list) and len(result) > 0:
                prediction = result[0]
                
                # Map sentiment to scam probability (placeholder logic)
                if prediction['label'] == 'NEGATIVE' and prediction['score'] > 0.8:
                    scam_prob = 0.7  # High negative sentiment might indicate scam
                else:
                    scam_prob = 0.3
                
                return {
                    'scam_probability': scam_prob,
                    'confidence': prediction['score'],
                    'raw_prediction': prediction
                }
        
        except Exception as e:
            logger.warning(f"BERT analysis failed: {e}")
        
        return {'scam_probability': 0.5, 'confidence': 0.0, 'error': 'BERT analysis failed'}
    
    def _analyze_with_fallback(self, text: str) -> Dict[str, Any]:
        """Analyze text using fallback TF-IDF model."""
        try:
            if self.fallback_model and self.tfidf_vectorizer:
                # Vectorize text
                X = self.tfidf_vectorizer.transform([text])
                
                # Get prediction
                probability = self.fallback_model.predict_proba(X)[0]
                scam_prob = probability[1] if len(probability) > 1 else probability[0]
                
                return {
                    'scam_probability': float(scam_prob),
                    'confidence': 0.8,
                    'model_type': 'RandomForest + TF-IDF'
                }
        
        except Exception as e:
            logger.warning(f"Fallback analysis failed: {e}")
        
        return {'scam_probability': 0.5, 'confidence': 0.0, 'error': 'Fallback analysis failed'}
    
    def _analyze_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Analyze text for known scam patterns."""
        matches = []
        text_lower = text.lower()
        
        for category, patterns in self.scam_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    matches.append({
                        'category': category,
                        'pattern': pattern,
                        'confidence': 0.8
                    })
        
        return matches
    
    def _analyze_language(self, text: str) -> List[Dict[str, Any]]:
        """Analyze language patterns and anomalies."""
        flags = []
        
        # Check for language mixing
        if self._has_mixed_languages(text):
            flags.append({
                'flag': 'mixed_languages',
                'description': 'Text contains multiple languages',
                'severity': 'medium'
            })
        
        # Check for excessive capitalization
        if self._has_excessive_caps(text):
            flags.append({
                'flag': 'excessive_caps',
                'description': 'Text has excessive capital letters',
                'severity': 'low'
            })
        
        # Check for poor grammar/spelling
        if self._has_poor_grammar(text):
            flags.append({
                'flag': 'poor_grammar',
                'description': 'Text has grammar or spelling issues',
                'severity': 'medium'
            })
        
        return flags
    
    def _analyze_structure(self, text: str) -> List[Dict[str, Any]]:
        """Analyze structural anomalies in text."""
        anomalies = []
        
        # Check for excessive punctuation
        if text.count('!') > 3 or text.count('?') > 2:
            anomalies.append({
                'anomaly': 'excessive_punctuation',
                'count': text.count('!') + text.count('?'),
                'severity': 'medium'
            })
        
        # Check for excessive emojis
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]', text))
        if emoji_count > 5:
            anomalies.append({
                'anomaly': 'excessive_emojis',
                'count': emoji_count,
                'severity': 'low'
            })
        
        # Check for repeated words
        words = text.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        for word, count in word_counts.items():
            if count > 3 and len(word) > 3:
                anomalies.append({
                    'anomaly': 'repeated_words',
                    'word': word,
                    'count': count,
                    'severity': 'medium'
                })
        
        return anomalies
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob."""
        try:
            blob = TextBlob(text)
            
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity,
                'sentiment_label': self._get_sentiment_label(blob.sentiment.polarity)
            }
        
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0, 'sentiment_label': 'neutral'}
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text."""
        entities = {
            'urls': [],
            'emails': [],
            'phone_numbers': [],
            'monetary_amounts': [],
            'percentages': []
        }
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        entities['urls'] = re.findall(url_pattern, text)
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['emails'] = re.findall(email_pattern, text)
        
        # Extract phone numbers
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        entities['phone_numbers'] = re.findall(phone_pattern, text)
        
        # Extract monetary amounts
        money_pattern = r'[₹$€£]\s?[\d,]+(?:\.\d{2})?'
        entities['monetary_amounts'] = re.findall(money_pattern, text)
        
        # Extract percentages
        percentage_pattern = r'\d+(?:\.\d+)?\s?%'
        entities['percentages'] = re.findall(percentage_pattern, text)
        
        return entities
    
    def _has_mixed_languages(self, text: str) -> bool:
        """Check if text contains mixed languages."""
        # Simple check for Hindi romanized words
        hindi_words = ['paisa', 'kamao', 'zarur', 'bharosa', 'karo']
        return any(word in text.lower() for word in hindi_words)
    
    def _has_excessive_caps(self, text: str) -> bool:
        """Check for excessive capitalization."""
        if len(text) < 10:
            return False
        
        caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
        return caps_ratio > 0.3
    
    def _has_poor_grammar(self, text: str) -> bool:
        """Check for poor grammar (simplified)."""
        # Check for common grammar issues
        issues = [
            text.count('  ') > 2,  # Multiple spaces
            '...' in text and text.count('.') > 5,  # Excessive periods
            re.search(r'[a-z][A-Z]', text) is not None,  # Missing spaces between sentences
        ]
        
        return any(issues)
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """Convert polarity to sentiment label."""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_final_probability(self, analysis_result: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate final scam probability from all indicators."""
        try:
            scores = []
            weights = []
            
            # BERT model prediction
            bert_pred = analysis_result['model_predictions'].get('bert', {})
            if bert_pred and 'scam_probability' in bert_pred:
                scores.append(bert_pred['scam_probability'])
                weights.append(0.4 * bert_pred.get('confidence', 0.5))
            
            # Fallback model prediction
            fallback_pred = analysis_result['model_predictions'].get('fallback', {})
            if fallback_pred and 'scam_probability' in fallback_pred:
                scores.append(fallback_pred['scam_probability'])
                weights.append(0.3 * fallback_pred.get('confidence', 0.5))
            
            # Pattern-based score
            pattern_matches = analysis_result['indicators']['pattern_matches']
            pattern_score = min(len(pattern_matches) * 0.15, 0.9)
            scores.append(pattern_score)
            weights.append(0.2)
            
            # Language flags score
            language_flags = analysis_result['indicators']['language_flags']
            language_score = min(len(language_flags) * 0.1, 0.5)
            scores.append(language_score)
            weights.append(0.1)
            
            if not scores:
                return 0.5, 0.0
            
            # Calculate weighted average
            total_weight = sum(weights)
            if total_weight > 0:
                final_probability = sum(s * w for s, w in zip(scores, weights)) / total_weight
            else:
                final_probability = sum(scores) / len(scores)
            
            # Calculate confidence based on agreement between models
            confidence = 1.0 - (np.std(scores) if len(scores) > 1 else 0.5)
            
            return min(final_probability, 1.0), min(confidence, 1.0)
        
        except Exception as e:
            logger.error(f"Error calculating final probability: {e}")
            return 0.5, 0.0
    
    def _determine_risk_level(self, probability: float) -> str:
        """Determine risk level based on probability."""
        if probability >= 0.8:
            return 'HIGH'
        elif probability >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def save_model(self, path: str) -> None:
        """Save trained models to disk."""
        try:
            if self.fallback_model:
                joblib.dump(self.fallback_model, f"{path}_fallback.pkl")
            
            if self.tfidf_vectorizer:
                joblib.dump(self.tfidf_vectorizer, f"{path}_tfidf.pkl")
            
            logger.info(f"Models saved to {path}")
        
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models."""
        return {
            'bert_model': self.model_name if self.classifier_pipeline else None,
            'fallback_model': type(self.fallback_model).__name__ if self.fallback_model else None,
            'confidence_threshold': self.confidence_threshold,
            'max_length': self.max_length,
            'scam_pattern_categories': list(self.scam_patterns.keys())
        }