from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvidenceHit:
    """
    one found piece of evidence
    IMPORTANT: make sure to freeze evidence hit when creating an instance of it
    through the API.
    """
    entity_internal_id: str
    entity_source_id: str
    entity_name: str
    source: str
    title: str
    language: str | None
    _format: str | None # article, book, etc...
    url: str | None
    published_at : datetime | None
    publisher_inst: list[str] | None # institutions, companies
    authors: list[dict] | None # person(s) who authored the instance
    description: str | None


    matched_aliases: list[str] = field(default_factory=list)
    matched_concepts: dict[str, list[str]] = field(default_factory=dict)
    matched_negative_terms: list[str] = field(default_factory=list)

    relevance_score: int = 0
    relevance_label: str = "low"
    reason: str = ""
    raw_file_path: str | None = None

    _frozen: bool = field(default=False, init=False, repr=False)
    _mutable_when_frozen = {"matched_aliases", "matched_concepts","matched_negative_terms",
                            "relevance_score", "relevance_label","reason", "raw_file_path",
                            "_frozen"}

    def __setattr__(self, key, value):
        if (
                getattr(self, "_frozen", False)
                and key not in self._mutable_when_frozen
        ):
            raise AttributeError(f"Cannot modify '{key}' because object is frozen")

        super().__setattr__(key, value)

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        self._frozen = False

    def __str__(self) -> str:
        concepts = "\n".join(
            f"    - {concept}: {', '.join(matches)}"
            for concept, matches in self.matched_concepts.items()
        )

        return f"""
EvidenceHit
-----------
Entity:      {self.entity_name} ({self.entity_internal_id})
Source:      {self.source}
Published:   {self.published_at}
Score:       {self.relevance_score} ({self.relevance_label})

Title:
  {self.title}

Description:
  {self.description}

URL:
  {self.url}

Matched aliases:
  {", ".join(self.matched_aliases) or "None"}

Matched concepts:
{concepts or "  None"}

Negative terms:
  {", ".join(self.matched_negative_terms) or "None"}

Reason:
  {self.reason}

Raw file:
  {self.raw_file_path}
""".strip()

    @property
    def matching_text(self) -> str:
        return f"{self.title or ''} {self.description or ''}"

