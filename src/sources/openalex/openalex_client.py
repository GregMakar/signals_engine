import requests
import time
import os
from dotenv import load_dotenv
from typing import Any, Self, Literal
from datetime import date, datetime

from src.config_loader import Config, instantiate_config
from src.models.evidence_hit import EvidenceHit
from src.models.match_reason import MatchReason
from src.models.source_ref import SourceRecordRef
from src.models.types import HitScope
from src.models.watchlist import WatchlistEntity

"""
The OpenAlex client is solely responsible for fetching RAW API data from OpenAlex in json format.
"""
load_dotenv('.env')

OA_Entities = Literal['works', 'authors', 'sources', 'institutions', 'topics',
                    'domains','fields', 'sub_fields', 'sdgs', 'countries',
                    'continents', 'languages', 'keywords', 'publishers',
                    'funders', 'awards']

class OpenAlexClient:
    allowed_entities = {'works', 'authors', 'sources', 'institutions', 'topics',
                    'domains','fields', 'sub_fields', 'sdgs', 'countries',
                    'continents', 'languages', 'keywords', 'publishers',
                    'funders', 'awards'}

    def __init__(self,
                 api_key: str = os.getenv("OPEN_ALEX_API_KEY"),
                 timeout: int =os.getenv("REQ_TIMEOUT_SEC"),
                 base_url:str = os.getenv("OPEN_ALEX_BASE_URL"),
                 ):
        """
        :param api_key: OpenAlex API key
        :param timeout: default is 10 seconds
        :param base_url: OpenAlex Base API URL
        """
        self.api_key = api_key
        self.timeout = int(timeout)
        self.base_url = base_url


    def get_json_single(self, entity: OA_Entities, _id: str, return_params: list[str] = None) -> dict:
        """
        Function is responsible for returning a single instance of specified entity, for bulk calls see "get_json_list".


        :param entity: has to be one of OA_entities, ex. authors would fetch an instance of OpenAlex authors
        :param _id: OpenAlex ID (e.g., W2741809807) or external ID (DOI, PMID, PMCID, MAG) - IMPORTANT - must be just the
            open alex W1234...
                or
            non-OpenAlex id, it needs to be in the following format: pmid%1234...

        :param return_params: list of response fields to return. Reduces response size. make sure the fields are valid.
        :return: json response from OpenAlex API
        """

        if entity not in self.allowed_entities:
            raise ValueError(f'invalid entity, entity mut be one of {self.allowed_entities}')


        if return_params is None:
            id_url = self.base_url + entity + '/' + _id + '?' + 'api_key=' + self.api_key
        else:
            params = '%2C'.join(return_params)
            id_url = self.base_url + entity + '/' + _id + '?' + 'api_key=' + self.api_key + '&' + 'select=' + params

        response = requests.get(id_url, timeout=self.timeout)
        response.raise_for_status()

        return response.json()


    def get_json_list(self, entity: str, _filter: dict[str, int | str | bool] | None = None,
                      _sort: str = None, group_by: list[str] = None,
                      search: str = None, per_page:int = None, page:int = None, select:list[str] = None) -> dict :
        """

        :param entity: has to be one of OA_entities, ex. authors would fetch instances of OpenAlex authors

        :param _filter: filter by the expected return values ex. for entity works... publication_year:2023,
                type:article, open_access.is_oa:true, author.id:A5023888391, institutions.id:I27837315.

                this parameter expects a dictionary.

        :param _sort: sort by one of the expected return values ex. for entity works ... cited_by_count,
                publication_date, relevance_score. prefix with a '-' for descending.

                this parameter expects a string.

        :param group_by: group by one or more expected return values. can be multidimensional, but will naturally
                fail if it does not make sense.

        :param search: Full-text search in case of entity works... searches across titles, abstracts,
                and other text fields.

        :param per_page: Number of results per page (1-100, default 25)

        :param page: Page number for pagination. Use cursor for deep pagination beyond 10,000 results.

        :param select: Comma-separated list of fields to return. Reduces response size.
                Example for entity works... : ['id','display_name','cited_by_count']

        :return: json response from OpenAlex API
        """

        if entity not in self.allowed_entities:
            raise ValueError(f"Invalid entity: {entity}. Must be one of {self.allowed_entities}")

        url = self.base_url.rstrip("/") + f"/{entity}"

        params: dict[str, str | int] = {}

        if self.api_key:
            params["api_key"] = self.api_key

        if per_page is not None:
            if not 1 <= per_page <= 100:
                raise ValueError("per_page must be between 1 and 100")
            params["per_page"] = per_page

        if page is not None:
            if page < 1:
                raise ValueError("page must be >= 1")
            params["page"] = page

        if search is not None:
            params["search"] = search

        if _filter is not None:
            params["filter"] = ",".join(
                f"{key}:{str(value).lower() if isinstance(value, bool) else value}"
                for key, value in _filter.items()
            )

        if _sort is not None:
            params["sort"] = _sort

        if group_by is not None:
            params["group_by"] = ",".join(group_by)

        if select is not None:
            params["select"] = ",".join(select)

        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()

        return response.json()


    def search_works(self, query: str, per_page: int = 25) -> dict:
        """
        IMPORTANT - There is so much more that can be extracted here that will probably prove to be useful,
        this is only v1.

        :param query:
        :param per_page:
        :return:
        """

        return self.get_json_list(
            entity='works',
            search=query,
            _filter= {
                "from_publication_date": "2016-01-01",
                "to_publication_date": str(date.today()),
            },
            per_page=per_page,
            select=[
                'id',
                'display_name',
                'publication_date',
                'language',
                'primary_location',
                'type',
                'abstract_inverted_index',
                'authorships',
                'institutions',
                'primary_topic',
                'topics'
            ]
        )

    def search_author(self, author_id: str) -> dict:
        """
        https://developers.openalex.org/api-reference/authors/get-a-single-author?playground=open

        :param author_id: OpenAlex auther id, it needs to be in A1234 format, without the prefix link.
        :return:one dictionary containing data on one author
        """
        if author_id is None:
            raise ValueError('author_id NA at OpenAlex DB')

        author = self.get_json_single(entity='authors', _id=author_id,
                                      return_params=['display_name', 'raw_author_names',
                                                     'full_name', 'affiliations',
                                                     'last_known_institutions',
                                                     'topics'])

        affiliations = author.get('affiliations')
        topics = author.get('topics')

        return_author = {
            'full_name': author.get('full_name'),
            'known_names': author.get('raw_author_names'),
            'affiliations': [affiliation['institution']['display_name'] for affiliation in affiliations],
            'last_known_inst': author.get('last_known_institutions'),
            'topics': [topic['display_name'] for topic in topics]
        }

        return return_author

    def get_queries(self, entity: WatchlistEntity) -> set[str]:
        queries = []

        if entity.entity_type in ['company', 'theme']:
            queries.append(entity.name.lower())

        for alias in entity.manual_aliases:
            for related_entity in entity.related_entities:
                query = f'{alias.lower()} {related_entity.replace("_", " ")}'
                queries.append(query)
            for prio_concept in entity.priority_concepts:
                query = f'{alias.lower()} {prio_concept.replace("_", " ")}'
                queries.append(query)

        return set(queries)





class OpenAlexNormalizer:
    def __init__(self, config: Config):
        self.meta = None
        self.config = config

    def _rec_ref_builder(self, work: dict) -> SourceRecordRef:
        return SourceRecordRef(
            source='OpenAlex',
            dataset='works',
            source_record_id=work.get('id', ''),
            batch_id= f"OA/{str(date.today())}", # this needs to have a scheduler specific ID eventually
        )

    def _match_builder(self, work: dict, entity: WatchlistEntity) -> list[MatchReason]:
        filter_rows = self.meta.get('x_query', {}).get('oqo', {}).get('filter_rows', [])


        query_used: list[str] = (
            (filter_rows[0].get('value') or '').split()
            if filter_rows
            else []
        )
        match_reasons_objs = []

        if query_used[0] in [entity.lower() for entity in entity.manual_aliases]:
            _ = MatchReason(
                matcher='entity_alias',
                field='title',
                value=work.get('display_name', ''),
                matched_id=entity.name,
                matched_label=entity.name,
                weight= 1.0,
                reason= 'Exact Name match -- ',
                metadata={'match_weight': 'Manual'}
            )
            match_reasons_objs.append(_)

        for word in query_used:
            if word.lower() in entity.related_entities:
                _ = MatchReason(
                    matcher='related_entity',
                    field='title',
                    value=work.get('display_name', ''),
                    matched_id=word,
                    weight=0.3,
                    reason='related entity match',
                    metadata={'match_weight': 'Manual'}
                )
                match_reasons_objs.append(_)

        word = '_'.join(query_used[1:])
        if word.lower() in entity.priority_concepts:
            _ = MatchReason(
                matcher= 'concept_keyword',
                field= 'title',
                value= work.get('display_name', ''),
                matched_id=word,
                weight= self.config.get_concept(concept_id=word).gdelt.get('severity_weight', 1.0),
                reason= f'matched priority concept {word}',
                metadata={'match_weight': 'dynamic',}
            )
            match_reasons_objs.append(_)

        if not match_reasons_objs:
            _ = MatchReason(
                matcher= 'unknown',
                field= 'title',
                value=work.get('display_name', ''),
                matched_id= ' '.join(query_used),
                weight=0.1,
                reason='Unknown',
                metadata={'match_weight': 'Manual'}
            )

        return match_reasons_objs

    def to_evidence_hit(self, work:dict, entity:WatchlistEntity, author_enrich: bool = False) -> EvidenceHit:
        """
        converts a single works entity OA json response into an internal EvidenceHit instance
        :param author_enrich: if True, it will run a API call in order to enrich author field deeply.
            see search_author at OpenAlexClient for more info.
        :param work: json response produced by OpenAlexClient
        :param entity: the entity that was used to produce the json response
        :return: EvidenceHit Object
        """

        # gets authors variable in EvidenceHit
        authors = []
        if author_enrich is True:
            client = OpenAlexClient()
            for author in work['authorships']:
                _id = author['author'].get('id', None)
                clean_id = _id.lstrip('https://openalex.org/') if _id is not None else None
                if clean_id:
                    authors.append(client.search_author(clean_id))
                else:
                    authors.append({'Unkown_id_author': author['author'].get('display_name', None)})
        else:
            authors = [author['author']['display_name'] for author in work['authorships']]

        # Build rec_ref
        record_ref= self._rec_ref_builder(work)

        # Build list of MatchReason objs
        matches = self._match_builder(work, entity)

        # Build list of context keys
        main_topics = [topic for topic in work.get('primary_topic', {}).get('display_name', '')]
        sec_topics = work.get('topics', [])

        for topic in sec_topics:
            main_topics.append(topic.get('display_name'))

        cleaned_topics = []
        for topic in main_topics:
            topic = topic.lower().replace(' ', '_')
            cleaned_topics.append(topic)

        if any(match.matcher == 'entity_alias' for match in matches):
            hit_scope: HitScope = 'direct'
        elif any(match.matcher == 'related_entity' for match in matches):
            hit_scope: HitScope = 'related'
        elif any(match.matcher == 'concept_keyword' for match in matches):
            hit_scope: HitScope = 'context'
        else:
            hit_scope = 'unknown'


        ev_hit = EvidenceHit(
            evidence_id= f'OpenAlex:{work.get("id", "").lstrip("https://openalex.org/")}',
            record_ref=record_ref,
            hit_scope= hit_scope, # "oql": "works where full text has (natural language processing)",
            subject_entity_id= entity.id,
            subject_entity_name=entity.name,
            related_entity_ids= entity.related_entities,
            context_keys= cleaned_topics,
            title= work.get('display_name'),
            language= work.get('language'),
            content_type= work.get('type'),
            url= work.get('primary_location').get('landing_page_url', work.get('id')),
            published_at= work.get('publication_date'),
            collected_at=datetime.now(),
            geography= work.get('countries'),
            authors=authors,
            publishers= work['authorships']['institutions'].get('display_name'),
            source_fields={'oa_id': work.get('id'), 'funders': work.get('funders'),
                           'institutions': work['authorships']['institutions'].get('display_name')},
            match_reasons=matches
        )

        return ev_hit

    def to_evidence_hits(self, response:dict, entity: WatchlistEntity, author_enrich: bool = False) -> list[EvidenceHit]:
        """

        :param response: full /work response from OpenAlexClient
        :param entity: the entity with which the OpenAlexClient search works method executed the API request
        :param author_enrich: deeply enriches the authors in list[dict of author] format. see search_authors
            for more detailed information.
        :return:  all the /works that were given to it in json/dict format are returned in EvidenceHit format as a list
        """
        self.meta = response.get('meta', {})
        results = response.get('results', [])

        ev_hit_list = []
        for result in results:
            if author_enrich is True:
                ev_hit_list.append(self.to_evidence_hit(result, entity, author_enrich=True))
            else:
                ev_hit_list.append(self.to_evidence_hit(result, entity))

        return ev_hit_list









