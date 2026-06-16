from src.models.watchlist import WatchlistEntity
from src.config_loader import Config

class QueryPlanner:
    def __init__(self, config: Config):
        self.config = config

    def get_query(self, source_id: str, entity_id: str) -> list[str]:
        """
         Only returns YAML file Queries

        :param source_id: takes source name
        :param entity_id: takes entity name
        :return: returns a list of all possible queries in the YAML file

        TO-DO LATER:
            deduplicate queries
            include aliases
            limit query count
            apply source-specific query rules
            skip unsupported entity/source combinations
            add concept terms selectively
            quote phrases differently per API
            clean unsafe characters
            log why each query was created
        """

        entity = self.config.get_entity(entity_id)
        source = self.config.sources.get(source_id)
        source_templates = self.config.query_templates.get(source_id, {})

        # light validation
        if source is None:
            raise KeyError(f"Unknown source_id: {source_id}")

        if not source.enabled:
            raise ValueError(f"Source is disabled: {source_id}")

        templates = (
                source_templates.get(entity.entity_type)
                or source_templates.get("all")
                or []
        )

        queries = [
            t.format(entity=entity.name)
            for t in templates
        ]

        return list(dict.fromkeys(queries))
