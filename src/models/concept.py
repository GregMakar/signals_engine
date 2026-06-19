from dataclasses import dataclass, field

@dataclass(frozen=True)
class Concept:
    id: str
    description: str
    score: float
    terms: list[str]
    gdelt: dict[str, float | list[str]]

