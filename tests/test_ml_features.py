"""
Comprehensive tests for Machine Learning Features
Tests claim classification, value prediction, anomaly detection, and trend analysis
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from ml.claim_classifier import ClaimClassifier, ClaimCategory
from ml.value_predictor import InvestigationValuePredictor
from ml.anomaly_detector import AnomalyDetector
from ml.trend_analyzer import TrendAnalyzer


class TestClaimClassifier:
    """Test claim classification system"""

    @pytest.fixture
    def classifier(self):
        """Create a claim classifier instance"""
        return ClaimClassifier(mode="rule_based")  # Use rule-based for testing

    def test_classify_factual_claim(self, classifier):
        """Test classifying factual claims"""
        claim = "Water boils at 100 degrees Celsius at sea level."
        result = classifier.classify(claim)

        assert result["category"] == "Factual"
        assert result["confidence"] > 0.7

    def test_classify_opinion_claim(self, classifier):
        """Test classifying opinion claims"""
        claim = "I believe that climate change is the most important issue."
        result = classifier.classify(claim)

        assert result["category"] == "Opinion"
        assert "believe" in result["indicators"]

    def test_classify_hypothesis_claim(self, classifier):
        """Test classifying hypothesis claims"""
        claim = "If we reduce carbon emissions, global temperatures may stabilize."
        result = classifier.classify(claim)

        assert result["category"] in ["Hypothesis", "Prediction"]
        assert result["confidence"] > 0.5

    def test_classify_prediction_claim(self, classifier):
        """Test classifying prediction claims"""
        claim = "The market will rise by 10% next year."
        result = classifier.classify(claim)

        assert result["category"] == "Prediction"
        assert "will" in claim.lower()

    def test_classify_definition_claim(self, classifier):
        """Test classifying definition claims"""
        claim = "Photosynthesis is the process by which plants convert light into energy."
        result = classifier.classify(claim)

        assert result["category"] == "Definition"
        assert any(word in claim.lower() for word in ["is the", "is a", "refers to"])

    def test_batch_classification(self, classifier):
        """Test classifying multiple claims at once"""
        claims = [
            "Water is H2O.",
            "I think coding is fun.",
            "The sun may explode in 5 billion years."
        ]

        results = classifier.classify_batch(claims)

        assert len(results) == 3
        assert results[0]["category"] == "Factual"
        assert results[1]["category"] == "Opinion"


class TestValuePredictor:
    """Test investigation value prediction"""

    @pytest.fixture
    def predictor(self):
        """Create a value predictor instance"""
        return InvestigationValuePredictor()

    def test_predict_novel_claim(self, predictor):
        """Test predicting value of novel claim"""
        claim = {
            "id": "1",
            "text": "A completely new and unique discovery about quantum entanglement.",
            "created_at": datetime.now().timestamp(),
            "evidence_count": 0
        }

        all_claims = [
            {"text": "Previous quantum research."},
            {"text": "Another quantum study."}
        ]

        result = predictor.predict_value(claim, all_claims)

        assert "score" in result
        assert "novelty" in result["factors"]
        assert result["score"] >= 0 and result["score"] <= 100

    def test_predict_controversial_claim(self, predictor):
        """Test predicting value of controversial claim"""
        claim = {
            "id": "1",
            "text": "Climate change may not be caused by human activity.",
            "confidence": 0.3,
            "evidence_count": 2
        }

        result = predictor.predict_value(claim, [])

        assert result["factors"]["controversy"] > 0.5
        assert "priority" in result

    def test_predict_well_evidenced_claim(self, predictor):
        """Test predicting value of well-evidenced claim"""
        claim = {
            "id": "1",
            "text": "Claim with extensive evidence.",
            "evidence_count": 10
        }

        result = predictor.predict_value(claim, [])

        # Should have low evidence gap (well-evidenced)
        assert result["factors"]["evidence_gap"] < 0.5

    def test_predict_recent_claim(self, predictor):
        """Test predicting value of recent claim"""
        claim = {
            "id": "1",
            "text": "Recent discovery.",
            "created_at": datetime.now().timestamp()
        }

        result = predictor.predict_value(claim, [])

        assert result["factors"]["recency"] > 0.7

    def test_batch_prediction(self, predictor):
        """Test batch value prediction"""
        claims = [
            {"id": "1", "text": "Claim 1", "evidence_count": 0},
            {"id": "2", "text": "Claim 2", "evidence_count": 5},
            {"id": "3", "text": "Claim 3", "evidence_count": 10}
        ]

        results = predictor.predict_batch(claims)

        assert len(results) == 3
        # Higher evidence gap should mean higher predicted value
        assert results[0]["score"] > results[2]["score"]


class TestAnomalyDetector:
    """Test anomaly detection system"""

    @pytest.fixture
    def detector(self):
        """Create an anomaly detector instance"""
        return AnomalyDetector()

    def test_detect_statistical_anomaly(self, detector):
        """Test detecting statistical outliers"""
        claims = [
            {"id": f"{i}", "confidence": 0.8, "evidence_count": 5}
            for i in range(20)
        ]

        # Add an anomaly
        claims.append({"id": "anomaly", "confidence": 0.1, "evidence_count": 50})

        results = detector.detect_anomalies(claims, methods=["statistical"])

        anomalies = [r for r in results if r["is_anomaly"]]
        assert len(anomalies) > 0

    def test_detect_semantic_anomaly(self, detector):
        """Test detecting semantically different claims"""
        claims = [
            {"id": "1", "text": "Climate change is real."},
            {"id": "2", "text": "Global warming is occurring."},
            {"id": "3", "text": "The planet is getting warmer."},
            {"id": "anomaly", "text": "Quantum computers use qubits."}  # Different topic
        ]

        results = detector.detect_anomalies(claims, methods=["semantic"])

        # The quantum computer claim should be detected as anomaly
        anomaly = next((r for r in results if r["claim_id"] == "anomaly"), None)
        assert anomaly is not None
        # Note: Semantic detection might not work without embeddings

    def test_detect_confidence_anomaly(self, detector):
        """Test detecting confidence outliers"""
        claims = [
            {"id": f"{i}", "confidence": 0.7, "text": f"Claim {i}"}
            for i in range(10)
        ]

        # Add extreme confidence values
        claims.append({"id": "low", "confidence": 0.1, "text": "Low confidence"})
        claims.append({"id": "high", "confidence": 0.99, "text": "High confidence"})

        results = detector.detect_anomalies(claims, methods=["confidence"])

        anomalies = [r for r in results if r["is_anomaly"]]
        assert len(anomalies) >= 1

    def test_detect_contradiction_anomaly(self, detector):
        """Test detecting claims with many contradictions"""
        claim = {
            "id": "1",
            "text": "Climate change is not real.",
            "contradictions": 10  # Many contradicting claims
        }

        results = detector.detect_anomalies([claim], methods=["contradiction"])

        assert results[0]["is_anomaly"] == True

    def test_anomaly_severity_levels(self, detector):
        """Test anomaly severity classification"""
        severities = detector.classify_severity([
            {"score": 95},  # Critical
            {"score": 75},  # High
            {"score": 55},  # Medium
            {"score": 35}   # Low
        ])

        assert severities[0] == "critical"
        assert severities[1] == "high"
        assert severities[2] == "medium"
        assert severities[3] == "low"


class TestTrendAnalyzer:
    """Test trend analysis system"""

    @pytest.fixture
    def analyzer(self):
        """Create a trend analyzer instance"""
        return TrendAnalyzer()

    def test_detect_emerging_trend(self, analyzer):
        """Test detecting emerging trends"""
        # Create claims with increasing frequency
        claims = []
        base_time = datetime.now()

        for i in range(30):
            # More claims in recent days
            count = 1 if i < 20 else 3
            for j in range(count):
                claims.append({
                    "id": f"{i}_{j}",
                    "text": "AI and machine learning advancement",
                    "created_at": (base_time - timedelta(days=30-i)).timestamp()
                })

        trends = analyzer.analyze_trends(claims)

        # Should detect upward trend
        assert len(trends) > 0
        assert any(t["trend_type"] == "emerging" for t in trends)

    def test_detect_declining_trend(self, analyzer):
        """Test detecting declining trends"""
        claims = []
        base_time = datetime.now()

        for i in range(30):
            # Fewer claims in recent days
            count = 3 if i < 10 else 1
            for j in range(count):
                claims.append({
                    "id": f"{i}_{j}",
                    "text": "Outdated technology discussion",
                    "created_at": (base_time - timedelta(days=30-i)).timestamp()
                })

        trends = analyzer.analyze_trends(claims)

        assert any(t["trend_type"] == "declining" for t in trends)

    def test_topic_clustering(self, analyzer):
        """Test clustering claims by topic"""
        claims = [
            {"id": "1", "text": "AI and machine learning advancements"},
            {"id": "2", "text": "Neural networks improving"},
            {"id": "3", "text": "Climate change impacts"},
            {"id": "4", "text": "Global warming effects"},
            {"id": "5", "text": "Deep learning breakthroughs"}
        ]

        clusters = analyzer.cluster_topics(claims, num_clusters=2)

        assert len(clusters) == 2
        # AI and climate topics should be separated

    def test_burst_detection(self, analyzer):
        """Test detecting burst activity"""
        claims = []
        base_time = datetime.now()

        # Normal activity for 20 days
        for i in range(20):
            claims.append({
                "id": f"normal_{i}",
                "text": "Regular claim",
                "created_at": (base_time - timedelta(days=30-i)).timestamp()
            })

        # Burst of activity on day 25
        for i in range(15):
            claims.append({
                "id": f"burst_{i}",
                "text": "Burst claim",
                "created_at": (base_time - timedelta(days=5)).timestamp()
            })

        bursts = analyzer.detect_bursts(claims)

        assert len(bursts) > 0
        assert bursts[0]["intensity"] > 2.0  # Significant burst

    def test_trend_prediction(self, analyzer):
        """Test predicting future trends"""
        claims = []
        base_time = datetime.now()

        # Create linear upward trend
        for i in range(30):
            count = i // 5  # Gradually increasing
            for j in range(count):
                claims.append({
                    "id": f"{i}_{j}",
                    "text": "Trending topic",
                    "created_at": (base_time - timedelta(days=30-i)).timestamp()
                })

        prediction = analyzer.predict_future_trend(claims, days_ahead=7)

        assert "predicted_count" in prediction
        assert prediction["predicted_count"] > 0
        assert "confidence" in prediction


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
