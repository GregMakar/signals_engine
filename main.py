from pathlib import Path
import yaml
import json
from datetime import datetime, timezone
from pprint import pprint
from dataclasses import asdict
from src.config_loader import Config
from src.models.evidence_hit import EvidenceHit
from src.services.query_planner import QueryPlanner
from src.services.concept_matcher import ConceptMatcher
from src.services.relevance_scorer import RelevanceScorer
from src.config_loader import instantiate_config
from src.storage.parquet_store import ParquetStore
from src.services.report_builder import ReportBuilder

"""path = Path('config/watchlist.yaml')

with path.open('r', encoding='utf-8') as f:
    raw = yaml.safe_load(f)

    print(json.dumps(raw, indent=4))

sources= {k: v for k,v in raw['sources'].items()}
entities= [v for v in raw['entities']]
concepts= {k: v for k,v in raw['concepts'].items()}


print(sources)
print(entities)
# print(json.dumps(concepts, indent=4))
print(concepts)"""

config = instantiate_config("config/watchlist.yaml")

entity = config.get_entity(entity_id='codelco')
concepts = config.concepts

planner = QueryPlanner(config)
matcher = ConceptMatcher(config)
scorer = RelevanceScorer(config)


queries = planner.get_query("gdelt", entity.id)

print("Generated queries:")
print(queries)

fake_hit = EvidenceHit(
    entity_id=entity.id,
    entity_name=entity.name,
    source="gdelt",
    title="Codelco workers walk off the job as wage talks fail at major copper mine",
    description="The disruption could affect copper production in Chile.",
    url="https://example.com",
    published_at=datetime.now(timezone.utc),
)

fake_hit.freeze()
fake_hit.matched_concepts = matcher.match_all(text=fake_hit.matching_text)

# this 'mazda' fails because it is trying to modify a field that is not part
# of the _mutable_when_frozen set
# fake_hit.entity_name = 'mazda'

scored_hit = scorer.score(fake_hit, entity)
# pprint(asdict(scored_hit), sort_dicts=False, width=100)
print(scored_hit)

store = ParquetStore()
store.save_records([scored_hit], 'test_fake_hit')

df = store.load("test_fake_hit")

report_builder = ReportBuilder()
report_path = report_builder.build_markdown(df)

print(f"Report saved to {report_path}")
