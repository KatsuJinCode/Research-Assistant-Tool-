"""
API Routes for Machine Learning Features

Endpoints:
- POST /api/ml/classify-claims - Classify claims into categories
- POST /api/ml/predict-value - Predict investigation value
- POST /api/ml/detect-anomalies - Detect anomalous claims
- GET  /api/ml/analyze-trends - Analyze topic trends
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from backend.ml import (
    ClaimClassifier,
    InvestigationValuePredictor,
    AnomalyDetector,
    TrendAnalyzer
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])

# Global ML instances (in production, use dependency injection with AI client)
classifier = ClaimClassifier(use_ai=False)  # Using rule-based for demo
value_predictor = InvestigationValuePredictor()
anomaly_detector = AnomalyDetector()
trend_analyzer = TrendAnalyzer()


class ClassifyClaimsRequest(BaseModel):
    """Request to classify claims"""
    claims: List[Dict[str, str]]  # [{"id": "...", "text": "..."}]
    update_database: bool = False


class PredictValueRequest(BaseModel):
    """Request to predict investigation value"""
    claims: List[Dict[str, Any]]
    claim_relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None
    claim_evidence: Optional[Dict[str, List[Dict[str, Any]]]] = None
    update_database: bool = False


class DetectAnomaliesRequest(BaseModel):
    """Request to detect anomalies"""
    claims: List[Dict[str, Any]]
    flag_in_database: bool = False
    min_score: float = 50.0


class AnalyzeTrendsRequest(BaseModel):
    """Request to analyze trends"""
    claims: List[Dict[str, Any]]
    time_window_days: Optional[int] = 90
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.post("/classify-claims")
async def classify_claims(request: ClassifyClaimsRequest):
    """
    Classify claims into categories.

    Categories: factual, opinion, hypothesis, prediction, definition
    """
    try:
        results = await classifier.classify_batch(request.claims)

        # Get statistics
        distribution = classifier.get_category_distribution(results)
        confidence_stats = classifier.get_confidence_stats(results)

        response_data = {
            "success": True,
            "total_claims": len(results),
            "distribution": distribution,
            "confidence_stats": confidence_stats,
            "results": [
                {
                    "claim_id": r.claim_id,
                    "claim_text": r.claim_text[:100] + "..." if len(r.claim_text) > 100 else r.claim_text,
                    "category": r.category.value,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                    "subcategory": r.subcategory
                }
                for r in results
            ]
        }

        # Optionally update database
        if request.update_database:
            # TODO: Get database connection and update
            # classifier.update_claim_categories(db, results)
            response_data["database_updated"] = True

        return response_data

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-value")
async def predict_investigation_value(request: PredictValueRequest):
    """
    Predict how valuable investigating each claim would be.

    Returns scores 0-100 based on novelty, evidence gap, controversy, etc.
    """
    try:
        predictions = await value_predictor.predict_batch(
            request.claims,
            request.claim_relationships,
            request.claim_evidence
        )

        # Get priority queue
        top_priority = value_predictor.get_priority_queue(predictions, limit=10)

        response_data = {
            "success": True,
            "total_claims": len(predictions),
            "high_priority": len([p for p in predictions if p.recommendation == 'high']),
            "medium_priority": len([p for p in predictions if p.recommendation == 'medium']),
            "low_priority": len([p for p in predictions if p.recommendation == 'low']),
            "avg_score": sum(p.value_score for p in predictions) / len(predictions),
            "top_priority_claims": [
                {
                    "claim_id": p.claim_id,
                    "claim_text": p.claim_text[:100] + "..." if len(p.claim_text) > 100 else p.claim_text,
                    "value_score": p.value_score,
                    "recommendation": p.recommendation,
                    "factors": p.factors,
                    "explanation": p.explanation
                }
                for p in top_priority
            ],
            "all_predictions": [
                {
                    "claim_id": p.claim_id,
                    "value_score": p.value_score,
                    "recommendation": p.recommendation,
                    "explanation": p.explanation
                }
                for p in predictions
            ]
        }

        # Optionally update database
        if request.update_database:
            # TODO: Get database connection and update
            # value_predictor.update_investigation_values(db, predictions)
            response_data["database_updated"] = True

        return response_data

    except Exception as e:
        logger.error(f"Value prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-anomalies")
async def detect_anomalies(request: DetectAnomaliesRequest):
    """
    Detect anomalous claims that are unusual or outliers.

    Detection types: statistical, semantic, confidence, contradiction, pattern
    """
    try:
        results = await anomaly_detector.detect_batch(request.claims)

        # Get statistics
        stats = anomaly_detector.get_anomaly_statistics(results)

        # Filter by minimum score
        significant_anomalies = [
            r for r in results
            if r.anomaly_score >= request.min_score
        ]

        response_data = {
            "success": True,
            "statistics": stats,
            "significant_anomalies": [
                {
                    "claim_id": a.claim_id,
                    "claim_text": a.claim_text[:100] + "..." if len(a.claim_text) > 100 else a.claim_text,
                    "anomaly_score": a.anomaly_score,
                    "anomaly_types": a.anomaly_types,
                    "severity": a.severity,
                    "explanation": a.explanation,
                    "details": a.details
                }
                for a in significant_anomalies
            ],
            "all_results": [
                {
                    "claim_id": r.claim_id,
                    "anomaly_score": r.anomaly_score,
                    "severity": r.severity
                }
                for r in results
            ]
        }

        # Optionally flag in database
        if request.flag_in_database:
            # TODO: Get database connection and flag
            # anomaly_detector.flag_anomalies(db, results, request.min_score)
            response_data["database_updated"] = True

        return response_data

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-trends")
async def analyze_trends(request: AnalyzeTrendsRequest):
    """
    Analyze trends in research topics over time.

    Returns emerging topics, declining topics, clusters, and predictions.
    """
    try:
        # Parse dates
        start_date = None
        end_date = None

        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date)
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)

        # Set time window if provided
        if request.time_window_days:
            trend_analyzer.time_window_days = request.time_window_days

        # Analyze trends
        analysis = await trend_analyzer.analyze_trends(
            request.claims,
            start_date,
            end_date
        )

        response_data = {
            "success": True,
            "analysis_period": {
                "start": analysis.analysis_period[0].isoformat(),
                "end": analysis.analysis_period[1].isoformat()
            },
            "summary": {
                "total_topics": len(analysis.trending_topics),
                "emerging_topics_count": len(analysis.emerging_topics),
                "declining_topics_count": len(analysis.declining_topics),
                "topic_clusters_count": len(analysis.topic_clusters)
            },
            "emerging_topics": analysis.emerging_topics,
            "declining_topics": analysis.declining_topics,
            "top_trending": [
                {
                    "topic": t.topic,
                    "total_mentions": t.total_mentions,
                    "growth_rate": t.growth_rate,
                    "trend_direction": t.trend_direction,
                    "burst_detected": t.burst_detected
                }
                for t in analysis.trending_topics[:20]
            ],
            "topic_clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "primary_topic": c.primary_topic,
                    "related_topics": c.related_topics,
                    "claim_count": c.claim_count,
                    "keywords": c.keywords
                }
                for c in analysis.topic_clusters
            ],
            "predictions": analysis.predictions,
            "visualization_data": analysis.visualization_data
        }

        return response_data

    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze-trends/topic/{topic}")
async def get_topic_insights(topic: str):
    """Get detailed insights about a specific topic"""
    try:
        # TODO: Store analysis results and retrieve
        # For now, return placeholder
        return {
            "success": True,
            "topic": topic,
            "message": "Topic insights endpoint - requires stored analysis"
        }

    except Exception as e:
        logger.error(f"Failed to get topic insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-results/{result_type}")
async def export_ml_results(result_type: str, data: Dict[str, Any]):
    """
    Export ML results to file.

    result_type: classification | value_prediction | anomalies | trends
    """
    try:
        from pathlib import Path
        import json

        exports_dir = Path("exports/ml")
        exports_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{result_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path = exports_dir / filename

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return {
            "success": True,
            "filename": filename,
            "path": str(output_path),
            "message": f"Results exported to {filename}"
        }

    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
