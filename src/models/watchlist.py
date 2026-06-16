from dataclasses import dataclass, field

@dataclass(frozen=True)
class Identifiers:
    ticker: str | None = None
    sec_cik: str | None = None
    wikidata_id: str | None = None

@dataclass(frozen=True)
class WatchlistEntity:
    id: str
    name: str
    entity_type: str
    priority: str
    manual_aliases: list[str]
    identifiers: Identifiers = field(default_factory=Identifiers)
    related_entities: list[str] = field(default_factory=list)
    priority_concepts: list[str] = field(default_factory=list)
    negative_terms: list[str] = field(default_factory=list)