from dataclasses import dataclass, field

from src.models.evidence_hit import EvidenceHit
from src.models.types import RoutingDecision


@dataclass(frozen=True)
class ScoreComponent:
    """
    ex.
    [
    ScoreComponent("direct_entity_match", 3.0, "Actor1Name matched Codelco"),
    ScoreComponent("cameo_severity", 2.5, "EventCode 143 = strike/boycott"),
    ScoreComponent("source_count", 1.0, "NumSources >= 5"),
    ]
    """
    name: str
    value: float
    reason: str


@dataclass(frozen=True)
class ScoredEvidenceHit:
    evidence_hit: EvidenceHit

    total_score: float # relevance + severity + confidence + novelty
    relevance_score: float #
    severity_score: float
    confidence_score: float
    recency_score: float
    novelty_score: float = 0.0

    relevance_label: str = "low"
    score_components: list[ScoreComponent] = field(default_factory=list)

    routing_decision: RoutingDecision = "store_only"