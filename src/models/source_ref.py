from dataclasses import dataclass

@dataclass(frozen=True)
class SourceRecordRef:
    """
    ex.
    SourceRecordRef(
    source="GDELT",
    dataset="events_mentions",
    source_record_id="1309503389",
    batch_id="20260617171500",
    raw_event_path="data/raw/gdelt/...",
    raw_mentions_path="data/raw/gdelt/...",
)
    """
    source: str
    dataset: str | None
    source_record_id: str
    batch_id: str
    raw_event_path: str | None = None # GDLET
    raw_mentions_path: str | None = None # GDLET