from dataclasses import dataclass
from typing import Literal, Any


MatcherType = Literal[
    "entity_alias",
    "country_code",
    "geo_match",
    "cameo_code",
    "concept_keyword",
    "url_keyword",
    "source_name",
]

@dataclass(frozen=True)
class MatchReason:
    """
    ex. MatchReason(
    matcher="cameo_code",
    field="EventCode",
    value="143",
    matched_id="labor_disruption",
    matched_label="Conduct strike or boycott",
    weight=0.85,
    reason="CAMEO 143 maps to labor disruption"
)
    """

    matcher: MatcherType
    field: str
    value: str
    matched_id: str
    matched_label: str | None = None
    weight: float = 0.0
    reason: str = ""
    metadata: dict[str, Any] | None = None