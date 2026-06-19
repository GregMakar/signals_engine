from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.models.source_ref import SourceRecordRef
from src.models.types import HitScope
from src.models.match_reason import MatchReason


@dataclass(frozen=True)
class CandidateHit:
    """
    Raw potential match.

    Means:
        A source row matched at least one configured rule and is worth
        validating/normalizing.

    Main purpose:
        Explain why a raw source row survived the DataFrame filter.
    """

    record_ref: SourceRecordRef
    hit_scope: HitScope

    # Optional display fields
    title: str | None = None
    description: str | None = None
    url: str | None = None

    # Time fields
    published_at: datetime | None = None
    occurred_at: datetime | None = None
    collected_at: datetime | None = None

    # Matching output
    matched_entity_ids: list[str] = field(default_factory=list)
    matched_context_keys: list[str] = field(default_factory=list)
    matched_concept_ids: list[str] = field(default_factory=list)
    match_reasons: list[MatchReason] = field(default_factory=list)

    # Raw/source-specific fields retained for normalization/debugging
    source_fields: dict[str, Any] = field(default_factory=dict)