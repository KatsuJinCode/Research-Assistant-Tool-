"""Research agents for autonomous investigation."""

from .base_agent import BaseAgent
from .support_agent import SupportAgent
from .challenge_agent import ChallengeAgent
from .analysis_agent import AnalysisAgent

__all__ = [
    "BaseAgent",
    "SupportAgent",
    "ChallengeAgent",
    "AnalysisAgent",
]
