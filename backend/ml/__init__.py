"""
Machine Learning Features

Advanced ML capabilities for Research Assistant Tool including:
- Automatic claim classification
- Investigation value prediction
- Anomaly detection
- Trend analysis
"""

from .claim_classifier import ClaimClassifier
from .value_predictor import InvestigationValuePredictor
from .anomaly_detector import AnomalyDetector
from .trend_analyzer import TrendAnalyzer

__all__ = [
    'ClaimClassifier',
    'InvestigationValuePredictor',
    'AnomalyDetector',
    'TrendAnalyzer'
]
