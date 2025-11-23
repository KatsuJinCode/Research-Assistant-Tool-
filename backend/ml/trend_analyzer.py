"""
Trend Analysis for Emerging Topics

Identifies trending topics in research claims over time.

Features:
- Track topic frequency over time
- Identify emerging vs declining topics
- Cluster related topics
- Trend visualization data
- Predict future trends

Methods:
- Time-series analysis
- Topic clustering (simple keyword-based or AI-based)
- Burst detection
- Network analysis
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class TrendData:
    """Time-series data for a topic"""
    topic: str
    time_points: List[datetime]
    counts: List[int]
    total_mentions: int
    growth_rate: float  # Percentage change
    trend_direction: str  # emerging/stable/declining
    burst_detected: bool


@dataclass
class TopicCluster:
    """Cluster of related topics"""
    cluster_id: int
    primary_topic: str
    related_topics: List[str]
    claim_count: int
    keywords: List[str]


@dataclass
class TrendAnalysis:
    """Complete trend analysis result"""
    analysis_period: Tuple[datetime, datetime]
    trending_topics: List[TrendData]
    topic_clusters: List[TopicCluster]
    emerging_topics: List[str]
    declining_topics: List[str]
    predictions: Dict[str, Any]
    visualization_data: Dict[str, Any]


class TrendAnalyzer:
    """
    Analyzes trends in research topics over time.

    Uses multiple methods:
    1. Time-series analysis: Track topic frequency over time
    2. Topic clustering: Group related topics
    3. Burst detection: Identify sudden increases
    4. Prediction: Forecast future trends
    """

    def __init__(
        self,
        time_window_days: int = 90,
        min_mentions: int = 3,
        burst_threshold: float = 2.0,
        ai_client: Any = None
    ):
        """
        Initialize trend analyzer.

        Args:
            time_window_days: Analysis time window
            min_mentions: Minimum mentions to consider a topic
            burst_threshold: Threshold for burst detection (multiplier)
            ai_client: Optional AI client for advanced analysis
        """
        self.time_window_days = time_window_days
        self.min_mentions = min_mentions
        self.burst_threshold = burst_threshold
        self.ai_client = ai_client

    async def analyze_trends(
        self,
        claims: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TrendAnalysis:
        """
        Perform complete trend analysis on claims.

        Args:
            claims: List of claim dicts with 'text' and 'created_at'
            start_date: Analysis start date (defaults to time_window_days ago)
            end_date: Analysis end date (defaults to now)

        Returns:
            TrendAnalysis
        """
        # Set date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=self.time_window_days)

        # Filter claims by date
        filtered_claims = self._filter_by_date(claims, start_date, end_date)

        if not filtered_claims:
            logger.warning("No claims in specified time range")
            return self._empty_analysis(start_date, end_date)

        # Extract topics from claims
        topic_data = self._extract_topics(filtered_claims)

        # Analyze each topic
        trending_topics = []
        for topic, topic_claims in topic_data.items():
            if len(topic_claims) < self.min_mentions:
                continue

            trend = self._analyze_topic_trend(topic, topic_claims, start_date, end_date)
            trending_topics.append(trend)

        # Sort by growth rate
        trending_topics.sort(key=lambda t: t.growth_rate, reverse=True)

        # Cluster topics
        topic_clusters = self._cluster_topics(topic_data)

        # Identify emerging/declining
        emerging = [t.topic for t in trending_topics if t.trend_direction == 'emerging']
        declining = [t.topic for t in trending_topics if t.trend_direction == 'declining']

        # Generate predictions
        predictions = self._predict_future_trends(trending_topics)

        # Create visualization data
        viz_data = self._create_visualization_data(trending_topics, topic_clusters)

        return TrendAnalysis(
            analysis_period=(start_date, end_date),
            trending_topics=trending_topics,
            topic_clusters=topic_clusters,
            emerging_topics=emerging[:10],  # Top 10
            declining_topics=declining[:10],
            predictions=predictions,
            visualization_data=viz_data
        )

    def _filter_by_date(
        self,
        claims: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Filter claims by date range"""
        filtered = []

        for claim in claims:
            created_at = claim.get('created_at')
            if not created_at:
                continue

            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    continue

            if start_date <= created_at <= end_date:
                filtered.append(claim)

        return filtered

    def _extract_topics(
        self,
        claims: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract topics from claims.

        Uses simple keyword extraction (can be enhanced with NLP/LDA).
        """
        topic_data = defaultdict(list)

        for claim in claims:
            text = claim.get('text', '').lower()

            # Simple keyword extraction
            # Remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'}

            words = text.split()
            keywords = [w.strip('.,!?;:') for w in words if w not in stop_words and len(w) > 3]

            # Use 2-grams as topics
            for i in range(len(keywords) - 1):
                topic = f"{keywords[i]} {keywords[i+1]}"
                topic_data[topic].append(claim)

            # Also use individual keywords
            for keyword in keywords:
                topic_data[keyword].append(claim)

        return dict(topic_data)

    def _analyze_topic_trend(
        self,
        topic: str,
        topic_claims: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> TrendData:
        """Analyze trend for a single topic"""
        # Create time buckets (weekly)
        bucket_size = timedelta(days=7)
        current = start_date
        time_points = []
        counts = []

        while current <= end_date:
            bucket_end = current + bucket_size
            count = sum(
                1 for claim in topic_claims
                if self._get_claim_date(claim) and current <= self._get_claim_date(claim) < bucket_end
            )
            time_points.append(current)
            counts.append(count)
            current = bucket_end

        # Calculate growth rate
        if len(counts) >= 2:
            first_half = sum(counts[:len(counts)//2])
            second_half = sum(counts[len(counts)//2:])

            if first_half > 0:
                growth_rate = ((second_half - first_half) / first_half) * 100
            else:
                growth_rate = 100.0 if second_half > 0 else 0.0
        else:
            growth_rate = 0.0

        # Determine trend direction
        if growth_rate > 50:
            trend_direction = 'emerging'
        elif growth_rate < -50:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'

        # Burst detection
        burst_detected = self._detect_burst(counts)

        return TrendData(
            topic=topic,
            time_points=time_points,
            counts=counts,
            total_mentions=len(topic_claims),
            growth_rate=growth_rate,
            trend_direction=trend_direction,
            burst_detected=burst_detected
        )

    def _get_claim_date(self, claim: Dict[str, Any]) -> Optional[datetime]:
        """Extract datetime from claim"""
        created_at = claim.get('created_at')
        if not created_at:
            return None

        if isinstance(created_at, str):
            try:
                return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return None

        return created_at

    def _detect_burst(self, counts: List[int]) -> bool:
        """
        Detect sudden burst in mentions.

        Uses simple threshold method: current count > threshold * average
        """
        if len(counts) < 3:
            return False

        avg = sum(counts[:-1]) / (len(counts) - 1)
        current = counts[-1]

        return current > (avg * self.burst_threshold) if avg > 0 else False

    def _cluster_topics(
        self,
        topic_data: Dict[str, List[Dict[str, Any]]]
    ) -> List[TopicCluster]:
        """
        Cluster related topics.

        Uses simple word overlap (can be enhanced with embeddings).
        """
        topics = list(topic_data.keys())
        clusters = []
        clustered = set()
        cluster_id = 0

        for topic in topics:
            if topic in clustered:
                continue

            # Find related topics (share words)
            topic_words = set(topic.split())
            related = [topic]

            for other_topic in topics:
                if other_topic == topic or other_topic in clustered:
                    continue

                other_words = set(other_topic.split())
                overlap = len(topic_words & other_words)

                if overlap > 0:
                    related.append(other_topic)
                    clustered.add(other_topic)

            # Get all keywords from cluster
            all_claims = []
            for t in related:
                all_claims.extend(topic_data[t])

            keywords = self._extract_cluster_keywords(all_claims)

            cluster = TopicCluster(
                cluster_id=cluster_id,
                primary_topic=topic,
                related_topics=related[1:],
                claim_count=len(all_claims),
                keywords=keywords[:10]  # Top 10
            )

            clusters.append(cluster)
            clustered.add(topic)
            cluster_id += 1

        # Sort by claim count
        clusters.sort(key=lambda c: c.claim_count, reverse=True)

        return clusters[:20]  # Top 20 clusters

    def _extract_cluster_keywords(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract representative keywords from claims"""
        word_counts = Counter()

        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'}

        for claim in claims:
            text = claim.get('text', '').lower()
            words = [w.strip('.,!?;:') for w in text.split() if w not in stop_words and len(w) > 3]
            word_counts.update(words)

        return [word for word, count in word_counts.most_common(10)]

    def _predict_future_trends(
        self,
        trending_topics: List[TrendData]
    ) -> Dict[str, Any]:
        """
        Predict future trends using simple extrapolation.

        For more advanced prediction, could use ARIMA, Prophet, or ML models.
        """
        predictions = {
            'top_emerging': [],
            'likely_to_grow': [],
            'likely_to_decline': []
        }

        for trend in trending_topics:
            if trend.trend_direction == 'emerging' and trend.growth_rate > 100:
                predictions['top_emerging'].append({
                    'topic': trend.topic,
                    'current_growth': trend.growth_rate,
                    'prediction': 'will likely continue growing'
                })

            if trend.growth_rate > 30:
                predictions['likely_to_grow'].append(trend.topic)
            elif trend.growth_rate < -30:
                predictions['likely_to_decline'].append(trend.topic)

        # Limit to top 5
        predictions['top_emerging'] = predictions['top_emerging'][:5]
        predictions['likely_to_grow'] = predictions['likely_to_grow'][:10]
        predictions['likely_to_decline'] = predictions['likely_to_decline'][:10]

        return predictions

    def _create_visualization_data(
        self,
        trending_topics: List[TrendData],
        topic_clusters: List[TopicCluster]
    ) -> Dict[str, Any]:
        """Create data for visualization"""
        return {
            'time_series': [
                {
                    'topic': t.topic,
                    'time_points': [tp.isoformat() for tp in t.time_points],
                    'counts': t.counts,
                    'trend': t.trend_direction
                }
                for t in trending_topics[:20]  # Top 20
            ],
            'growth_rates': [
                {
                    'topic': t.topic,
                    'growth_rate': t.growth_rate,
                    'total_mentions': t.total_mentions
                }
                for t in trending_topics[:20]
            ],
            'topic_network': [
                {
                    'cluster_id': c.cluster_id,
                    'primary_topic': c.primary_topic,
                    'related_topics': c.related_topics,
                    'size': c.claim_count
                }
                for c in topic_clusters[:15]
            ],
            'burst_topics': [
                t.topic for t in trending_topics if t.burst_detected
            ][:10]
        }

    def _empty_analysis(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> TrendAnalysis:
        """Return empty analysis when no data"""
        return TrendAnalysis(
            analysis_period=(start_date, end_date),
            trending_topics=[],
            topic_clusters=[],
            emerging_topics=[],
            declining_topics=[],
            predictions={},
            visualization_data={}
        )

    def export_analysis(
        self,
        analysis: TrendAnalysis,
        output_path: str
    ):
        """Export trend analysis to JSON"""
        import json

        export_data = {
            'analysis_period': {
                'start': analysis.analysis_period[0].isoformat(),
                'end': analysis.analysis_period[1].isoformat()
            },
            'summary': {
                'total_topics': len(analysis.trending_topics),
                'emerging_topics_count': len(analysis.emerging_topics),
                'declining_topics_count': len(analysis.declining_topics),
                'topic_clusters_count': len(analysis.topic_clusters)
            },
            'trending_topics': [
                {
                    'topic': t.topic,
                    'total_mentions': t.total_mentions,
                    'growth_rate': t.growth_rate,
                    'trend_direction': t.trend_direction,
                    'burst_detected': t.burst_detected
                }
                for t in analysis.trending_topics
            ],
            'emerging_topics': analysis.emerging_topics,
            'declining_topics': analysis.declining_topics,
            'topic_clusters': [
                {
                    'cluster_id': c.cluster_id,
                    'primary_topic': c.primary_topic,
                    'related_topics': c.related_topics,
                    'claim_count': c.claim_count,
                    'keywords': c.keywords
                }
                for c in analysis.topic_clusters
            ],
            'predictions': analysis.predictions,
            'visualization_data': analysis.visualization_data
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported trend analysis to {output_path}")

    async def get_topic_insights(
        self,
        topic: str,
        analysis: TrendAnalysis
    ) -> Dict[str, Any]:
        """Get detailed insights about a specific topic"""
        # Find topic in analysis
        topic_trend = None
        for trend in analysis.trending_topics:
            if trend.topic == topic:
                topic_trend = trend
                break

        if not topic_trend:
            return {'error': 'Topic not found'}

        # Find cluster
        topic_cluster = None
        for cluster in analysis.topic_clusters:
            if cluster.primary_topic == topic or topic in cluster.related_topics:
                topic_cluster = cluster
                break

        insights = {
            'topic': topic,
            'statistics': {
                'total_mentions': topic_trend.total_mentions,
                'growth_rate': topic_trend.growth_rate,
                'trend_direction': topic_trend.trend_direction,
                'burst_detected': topic_trend.burst_detected
            },
            'related_topics': topic_cluster.related_topics if topic_cluster else [],
            'cluster_keywords': topic_cluster.keywords if topic_cluster else [],
            'time_series': {
                'time_points': [tp.isoformat() for tp in topic_trend.time_points],
                'counts': topic_trend.counts
            }
        }

        return insights
