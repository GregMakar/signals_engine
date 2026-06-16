from src.config_loader import Config, instantiate_config
from src.services.query_planner import QueryPlanner


config = instantiate_config('/Users/work/Documents/Programming/Palantiresque/Signal Engine/config/watchlist.yaml')
query_planner = QueryPlanner(config)

query = query_planner.get_query(source_id='gdelt', entity_id='codelco')
print(query)
