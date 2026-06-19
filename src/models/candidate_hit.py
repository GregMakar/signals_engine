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

    a CandidateHit graduates to EvidenceHit only if it...
    1. Has a source record ID (GDELT)_
    2. Has at least one meaningful match reason
    3. Has a usable event/date/time
    4. Has either:
       - direct entity match
       - related entity match
       - valid context/concept match
    5. Has enough source provenance to trace it back
    6. Is not obviously excluded by negative terms/rules
    7. Can be mapped into the generic EvidenceHit schema

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