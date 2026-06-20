from dataclasses import dataclass
from typing import Literal, Any


MatcherType = Literal[
    "entity_alias",
    "wikidata_alias",
    "country_code",
    "geo_match",
    "cameo_code",
    "concept_keyword",
    "url_keyword",
    "source_name",
    "related_entity"
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
    field: str # which source field was checked Actor1Name, title etc..
    value: str # the actual value found in the field above, Codelco, "copper supply disruption"

    matched_id: str # internal thing it matched to
    matched_label: str | None = None # human readable

    weight: float = 0.0
    reason: str = ""

    metadata: dict[str, Any] | None = None