from dataclasses import dataclass, field
from datetime import datetime
from src.models.match_reason import MatchReason
from src.models.source_ref import SourceRecordRef
from src.models.types import HitScope
from typing import Any

@dataclass(frozen=True)
class EvidenceHit:

    """
    one found piece of evidence
    """
    evidence_id: str
    record_ref: SourceRecordRef
    hit_scope: HitScope

    # Entity/context relationship
    subject_entity_id: str | None
    subject_entity_name: str | None
    related_entity_ids: list[str] = field(default_factory=list)
    context_keys: list[str] = field(default_factory=list)

    # Display/content
    title: str | None = None
    description: str | None = None
    url: str | None = None
    language: str | None = None
    content_type: str | None = None  # article, filing, paper, event_record, etc.

    # Time
    published_at: datetime | None = None
    occurred_at: datetime | None = None
    collected_at: datetime | None = None

    # Event typing
    event_type_code: str | None = None
    event_type_label: str | None = None
    event_base_code: str | None = None
    event_base_label: str | None = None
    event_root_code: str | None = None
    event_root_label: str | None = None

    # Domain enrichment
    geography: list[str] = field(default_factory=list)
    commodities: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)

    # Attribution
    publishers: list[str] = field(default_factory=list)
    authors: list[dict[str, Any]] = field(default_factory=list)

    # Matching/audit
    matched_aliases: list[str] = field(default_factory=list)
    matched_concept_ids: list[str] = field(default_factory=list)
    matched_terms_by_concept: dict[str, list[str]] = field(default_factory=dict)
    matched_negative_terms: list[str] = field(default_factory=list)
    match_reasons: list[MatchReason] = field(default_factory=list)

    # Source-specific retained fields
    source_fields: dict[str, Any] = field(default_factory=dict)

    @property
    def matching_text(self) -> str:
        parts = [
            self.title or "",
            self.description or "",
            self.url or "",
            self.event_type_label or "",
            self.event_root_label or "",
            " ".join(self.geography),
            " ".join(self.commodities),
            " ".join(self.sectors),
        ]
        return " ".join(part for part in parts if part).strip()
