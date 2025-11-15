"""
Finance Anomaly Radar (FAR)
==========================

A Real-Time Early-Warning Radar for Detecting Financial Fraud, Scams & Market Manipulation
Using AI + Multimodal Signals.

Author: Your Name
Version: 1.0.0
Date: November 2024
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "AI-powered financial fraud and market manipulation detection system"

from .core.radar_engine import RadarEngine
from .core.config_manager import ConfigManager
from .ai_engines.nlp_detector import NLPScamDetector
from .ai_engines.market_detector import MarketManipulationDetector
from .ai_engines.transaction_analyzer import TransactionAnomalyAnalyzer
from .ai_engines.social_graph import SocialTrustGraph
from .ai_engines.fusion_engine import RadarFusionEngine
from .alert_system.alert_manager import AlertManager

__all__ = [
    "RadarEngine",
    "ConfigManager", 
    "NLPScamDetector",
    "MarketManipulationDetector",
    "TransactionAnomalyAnalyzer",
    "SocialTrustGraph",
    "RadarFusionEngine",
    "AlertManager"
]