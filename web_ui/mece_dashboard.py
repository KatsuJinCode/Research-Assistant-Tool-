"""
MECE Quality Dashboard

Provides visualization and monitoring of MECE clustering quality.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import plotly
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Install with: pip install plotly")


def create_mece_dashboard(validation_results: Dict[str, Any]) -> Optional[object]:
    """
    Create comprehensive MECE quality dashboard.

    Args:
        validation_results: Output from MECEValidator.validate_mece()

    Returns:
        Plotly figure with 4 subplots (or None if plotly not available)
    """
    if not PLOTLY_AVAILABLE:
        logger.warning("Cannot create dashboard: plotly not installed")
        return None

    # Create 2x2 subplot grid
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'MECE Score Breakdown',
            'Mutual Exclusivity Metrics',
            'Comprehensiveness Metrics',
            'Cluster Quality Metrics'
        ),
        specs=[
            [{'type': 'indicator'}, {'type': 'bar'}],
            [{'type': 'bar'}, {'type': 'bar'}]
        ]
    )

    # 1. Overall MECE Score (gauge)
    mece_score = validation_results['mece_score']
    grade = validation_results['grade'].split(' - ')[0]  # Extract letter grade

    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=mece_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"MECE Score<br><span style='font-size:0.8em'>Grade: {grade}</span>"},
            delta={'reference': 0.7, 'increasing': {'color': 'green'}},
            gauge={
                'axis': {'range': [None, 1]},
                'bar': {'color': get_score_color(mece_score)},
                'steps': [
                    {'range': [0, 0.5], 'color': 'lightgray'},
                    {'range': [0.5, 0.7], 'color': 'lightyellow'},
                    {'range': [0.7, 1], 'color': 'lightgreen'}
                ],
                'threshold': {
                    'line': {'color': 'red', 'width': 4},
                    'thickness': 0.75,
                    'value': 0.6
                }
            }
        ),
        row=1, col=1
    )

    # 2. Mutual Exclusivity Metrics
    exclusivity = validation_results['mutual_exclusivity']
    fig.add_trace(
        go.Bar(
            x=['Overlap Ratio', 'Inter-Cluster Sim', 'Partition Coef'],
            y=[
                exclusivity['overlap_ratio'],
                exclusivity['inter_cluster_similarity'],
                1 - exclusivity['partition_coefficient']  # Invert so lower is better
            ],
            marker_color=['red' if exclusivity['overlap_ratio'] > 0 else 'green',
                         'red' if exclusivity['inter_cluster_similarity'] > 0.6 else 'green',
                         'green'],
            text=[f"{v:.3f}" for v in [
                exclusivity['overlap_ratio'],
                exclusivity['inter_cluster_similarity'],
                1 - exclusivity['partition_coefficient']
            ]],
            textposition='auto'
        ),
        row=1, col=2
    )

    # 3. Comprehensiveness Metrics
    comprehensiveness = validation_results['comprehensiveness']
    fig.add_trace(
        go.Bar(
            x=['Coverage Ratio', 'Semantic Coverage'],
            y=[
                comprehensiveness['coverage_ratio'],
                comprehensiveness['semantic_coverage']
            ],
            marker_color=[
                'green' if comprehensiveness['coverage_ratio'] >= 0.95 else 'orange',
                'green' if comprehensiveness['semantic_coverage'] > 0.8 else 'orange'
            ],
            text=[f"{v:.3f}" for v in [
                comprehensiveness['coverage_ratio'],
                comprehensiveness['semantic_coverage']
            ]],
            textposition='auto'
        ),
        row=2, col=1
    )

    # 4. Cluster Quality Metrics
    quality = validation_results['cluster_quality']
    fig.add_trace(
        go.Bar(
            x=['Silhouette', 'Cohesion', 'DB Index (inv)'],
            y=[
                quality['silhouette_score'],
                quality['avg_cohesion'],
                1 / (1 + quality['davies_bouldin_index'])  # Normalize
            ],
            marker_color=[
                'green' if quality['silhouette_score'] > 0.5 else 'orange',
                'green' if quality['avg_cohesion'] > 0.5 else 'orange',
                'green'
            ],
            text=[
                f"{quality['silhouette_score']:.3f}",
                f"{quality['avg_cohesion']:.3f}",
                f"DB: {quality['davies_bouldin_index']:.3f}"
            ],
            textposition='auto'
        ),
        row=2, col=2
    )

    # Update layout
    fig.update_layout(
        title_text=f"MECE Quality Dashboard - {validation_results['grade']}",
        showlegend=False,
        height=700
    )

    # Add reference lines
    fig.add_hline(y=0.95, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Target: 0.95")
    fig.add_hline(y=0.6, line_dash="dash", line_color="orange", row=1, col=2, annotation_text="Threshold: 0.6")

    return fig


def get_score_color(score: float) -> str:
    """Get color based on MECE score."""
    if score >= 0.8:
        return 'green'
    elif score >= 0.7:
        return 'lightgreen'
    elif score >= 0.6:
        return 'orange'
    elif score >= 0.5:
        return 'darkorange'
    else:
        return 'red'


def create_mece_summary_html(validation_results: Dict[str, Any]) -> str:
    """
    Create HTML summary of MECE validation results (fallback for when plotly unavailable).

    Args:
        validation_results: Output from MECEValidator.validate_mece()

    Returns:
        HTML string with formatted results
    """
    mece_score = validation_results['mece_score']
    grade = validation_results['grade']
    passed = validation_results['passed']

    exclusivity = validation_results['mutual_exclusivity']
    comprehensiveness = validation_results['comprehensiveness']
    quality = validation_results['cluster_quality']

    status_color = 'green' if passed else 'red'
    score_color = get_score_color(mece_score)

    html = f"""
    <div class="mece-summary" style="border: 2px solid {status_color}; padding: 20px; border-radius: 8px;">
        <h2 style="color: {score_color};">MECE Validation Results</h2>

        <div class="overall-score">
            <h3>Overall Score: {mece_score:.3f} / 1.0</h3>
            <p><strong>Grade:</strong> {grade}</p>
            <p><strong>Status:</strong> <span style="color: {status_color};">{'PASSED' if passed else 'FAILED'}</span></p>
        </div>

        <div class="metrics">
            <h3>Mutual Exclusivity</h3>
            <ul>
                <li>Overlap Ratio: {exclusivity['overlap_ratio']:.3f} (target: 0.0) {'✓' if exclusivity['overlap_ratio'] == 0 else '✗'}</li>
                <li>Inter-Cluster Similarity: {exclusivity['inter_cluster_similarity']:.3f} (target: &lt; 0.6) {'✓' if exclusivity['inter_cluster_similarity'] < 0.6 else '✗'}</li>
                <li>Partition Coefficient: {exclusivity['partition_coefficient']:.3f} (target: 1.0) {'✓' if exclusivity['partition_coefficient'] == 1.0 else '○'}</li>
            </ul>

            <h3>Comprehensiveness</h3>
            <ul>
                <li>Coverage Ratio: {comprehensiveness['coverage_ratio']:.3f} (target: ≥ 0.95) {'✓' if comprehensiveness['coverage_ratio'] >= 0.95 else '✗'}</li>
                <li>Semantic Coverage: {comprehensiveness['semantic_coverage']:.3f} (target: &gt; 0.8) {'✓' if comprehensiveness['semantic_coverage'] > 0.8 else '○'}</li>
                <li>Missing Claims: {comprehensiveness['num_missing']}</li>
            </ul>

            <h3>Cluster Quality</h3>
            <ul>
                <li>Silhouette Score: {quality['silhouette_score']:.3f} (target: &gt; 0.5) {'✓' if quality['silhouette_score'] > 0.5 else '○'}</li>
                <li>Davies-Bouldin Index: {quality['davies_bouldin_index']:.3f} (target: &lt; 1.0) {'✓' if quality['davies_bouldin_index'] < 1.0 else '○'}</li>
                <li>Average Cohesion: {quality['avg_cohesion']:.3f} (target: &gt; 0.5) {'✓' if quality['avg_cohesion'] > 0.5 else '○'}</li>
            </ul>
        </div>
    </div>
    """

    return html
