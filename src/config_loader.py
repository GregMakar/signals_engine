from pathlib import Path
from dataclasses import dataclass
import yaml
from src.models.concept import Concept
from src.models.watchlist import WatchlistEntity, Identifiers

"""
load YAML
validate required groups exist
convert entities into WatchlistEntity objects
convert concepts into Concept objects
return a Config object
build validation logic
"""

@dataclass(frozen=True)
class ConfigProject:
    """
    project Metadata
    """
    name: str
    description: str


@dataclass(frozen=True)
class Settings:
    """
    to be used by collector, storer and report builder
    """
    max_results_per_query: int
    require_entity_match: bool
    min_relevance_score: int
    high_relevance_score: int
    medium_relevance_score: int


@dataclass(frozen=True)
class ConfigSources:
    """
    On/Off switch
    """
    enabled: bool
    purpose: str


@dataclass(frozen=True)
class ScoringConfig:
    """
    scoring rules
    """
    relevance: dict[str, dict[str, float]]
    severity: dict[str, dict[str, float | bool | dict[str, float] | list[str]]]
    confidence: dict[str, dict[str, float | dict[str, float]]]
    recency: dict[str, float]
    novelty: dict[str, float | bool]
    penalties: dict[str, float]
    labels: dict[str, dict[str, float]]
    routing: dict[str, float]


@dataclass(frozen=True)
class Config:
    """
    the whole point of this class is 1- Validation logic 2- convenience.
    Top level
    """
    version: int
    project: ConfigProject
    settings: Settings
    sources: dict[str, ConfigSources]
    entities: dict[str, WatchlistEntity]
    concepts: dict[str, Concept]
    scoring: ScoringConfig
    query_templates: dict[str, dict[str, list[str]]]

    def __post_init__(self):
        self.self_validate()

    # Validation Logic for instantiation of Config Object
    def self_validate(self) -> None:
        """

        :return: None
        """

        for entity in self.entities.values():
            for concept_id in entity.priority_concepts:
                if concept_id not in self.concepts:
                    raise ValueError(
                        f"Entity {entity.id} references unknown concept: {concept_id}"
                    )

        for source_name, source in self.sources.items():
            if source.enabled and source_name not in self.query_templates:
                raise ValueError(
                    f"Enabled source has no query templates: {source_name}"
                )


    def enabled_sources(self) -> list[str]:
        """
        :return: returns a list of all enabled sources
        """
        return [
            name for name, source in self.sources.items()
            if source.enabled
        ]


    def get_entity(self, entity_id: str) -> WatchlistEntity:
        """
        :param entity_id: ex. chile, codelco
        :return: returns specified WatchlistEntity object
        """
        try:
            return self.entities[entity_id]
        except KeyError:
            raise KeyError(f"Unknown entity_id: {entity_id}")


    def get_concept(self, concept_id: str) -> Concept:
        """
        :param concept_id: concept_id ex. labor_disruption, mining_disruption...
        :return: returns specified Concepts object
        """
        try:
            return self.concepts[concept_id]
        except KeyError:
            raise KeyError(f'Unknown concept_id: {concept_id}')



    def get_query_templates(self, source_id: str, entity_type: str) -> list[str]:
        """
            returns hard coded templates with specified source[ex. GDLET, OpenAlex...] &
            entity_type[ex. Company, country...]
        """

        source_templates = self.query_templates.get(source_id, {})
        return (
                source_templates.get(entity_type)
                or source_templates.get("all")
                or []
                )

def build_identifiers(data: dict | None) -> Identifiers:
    data = data or {}

    return Identifiers(
        ticker=data.get("ticker"),
        sec_cik=data.get("sec_cik"),
        wikidata_id=data.get("wikidata_id"),
    )


# instantiate a config instance
def instantiate_config(yaml_path: str) -> Config:
    """
    Given a YAML path, it returns a Config object that is a OOP representation of the YAML file
    :param yaml_path:
    :return:
    """
    path = Path(yaml_path)

    with path.open('r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)

        if raw is None:
            raise ValueError(f"YAML file is empty: {path}")

    # very basic validation
    required = ["version", "project", "settings", "sources", "entities", "concepts", "scoring", "query_templates"]
    missing = [key for key in required if key not in raw]

    if missing:
        raise ValueError(f"Missing config groups: {missing}")

    # instantiation

    # {'openalex': {'enabled': True, 'purpose': 'research_trend_monitoring'}, 'gdelt': {'enabled': T...
    sources_dict = {k:v for k,v in raw['sources'].items()}

    # [{'id': 'chile', 'name': 'Chile', 'type': 'country', 'priority': 'high', 'manual_aliases':...
    entities = [v for v in raw['entities']]

    # {'labor_disruption': {'id': 'labor_disruption', 'description': 'Workers, unions, strik...
    concepts = {k:v for k,v in raw['concepts'].items()}


    return Config(      version=raw["version"],

                        project=ConfigProject(name=raw['project']["name"], description=raw['project']["description"]),

                        settings=Settings(max_results_per_query=raw["settings"]["max_results_per_query"],
                                          require_entity_match=raw["settings"]["require_entity_match"],
                                          min_relevance_score=raw["settings"]["min_relevance_score"],
                                          high_relevance_score=raw["settings"]["high_relevance_score"],
                                          medium_relevance_score=raw["settings"]["medium_relevance_score"]),

                        sources={source_name: ConfigSources(
                            enabled= source_data['enabled'],
                            purpose= source_data['purpose']
                        )
                            for source_name, source_data in sources_dict.items()},

                        entities={entity['id']: WatchlistEntity(
                            id=entity['id'],
                            name=entity['name'],
                            entity_type=entity['type'],
                            priority=entity['priority'],
                            identifiers= build_identifiers(entity.get("identifiers")),
                            manual_aliases=entity.get("manual_aliases", []),
                            related_entities=entity.get("related_entities", []),
                            priority_concepts=entity.get("priority_concepts", []),
                            negative_terms=entity.get("negative_terms", []),
                            source_filters=entity.get("source_filters", {})
                        )
                            for entity in entities},

                        concepts={concept_id:Concept(
                            id=concept_id,
                            name= concept_data['name'],
                            description= concept_data['description'],
                            score= concept_data['score'],
                            terms= concept_data['terms'],
                            gdelt= concept_data.get('gdelt', {})
                        )
                        for concept_id, concept_data in concepts.items()},

                        scoring=ScoringConfig(
                            relevance=raw['scoring']['relevance'],
                            severity=raw['scoring']['severity'],
                            confidence=raw['scoring']['confidence'],
                            recency=raw['scoring']['recency'],
                            novelty=raw['scoring']['novelty'],
                            penalties=raw['scoring']['penalties'],
                            labels=raw['scoring']['labels'],
                            routing=raw['scoring']['routing'],
                        ),

                        query_templates=raw['query_templates']
                        )
