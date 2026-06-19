from dataclasses import dataclass, field

from src.models.evidence_hit import EvidenceHit
from src.models.types import RoutingDecision


@dataclass(frozen=True)
class ScoreComponent:
    name: str
    value: float
    reason: str


@dataclass(frozen=True)
class ScoredEvidenceHit:
    evidence_hit: EvidenceHit

    total_score: float
    relevance_score: float
    severity_score: float
    confidence_score: float
    novelty_score: float = 0.0

    relevance_label: str = "low"
    score_components: list[ScoreComponent] = field(default_factory=list)

    routing_decision: RoutingDecision = "store_only"