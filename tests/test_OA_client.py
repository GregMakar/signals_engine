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
from src.clients.openalex_client import OpenAlexClient,OpenAlexNormalizer

# Instantiate config... Basically read the rules from yaml into python
config = instantiate_config('../config/watchlist.yaml')

# Instantiate the OpenAlex client and normalizer service class
oa_client = OpenAlexClient()
oa_client_normalizer = OpenAlexNormalizer()

# get WatchlistEntity obj from config (basically from yaml).
# you're going to execute research on this entity in this instance
entity = config.get_entity('codelco')

# load the hard coded concepts from config/yaml
concepts = config.concepts

# instantiate service classes
planner = QueryPlanner(config) # service class that has a method that extracts queries from config/yaml based on entity and source provided.
matcher = ConceptMatcher(config) # has a method that matches concepts (from config/yaml) based on title + description of hit.
scorer = RelevanceScorer(config) # has a method that scores relevance based on rules for scoring in config/yaml


queries = planner.get_query("openalex", entity.id)

print("Generated queries:")
print(queries)

all_hits = []
for query in queries:
    works = oa_client.search_works(query=query) # -> json/dict response for one query
    normalized_hits = oa_client_normalizer.to_evidence_hits(response=works, entity=entity, author_enrich=True) # -> turns all json/dicts to evidence hits in a list
    for hit in normalized_hits:
        hit.matched_concepts = matcher.match_all(text=hit.matching_text) # -> enrich matched_concepts
        scored_hit = scorer.score(hit, entity) # -> enrich scores
        all_hits.append(hit)

print('Storing...')

store = ParquetStore()
store.save_records(all_hits, 'openalex_first_test')

df = store.load("openalex_first_test")

report_builder = ReportBuilder()
report_path = report_builder.build_markdown(df)

print(f"Report saved to {report_path}")




