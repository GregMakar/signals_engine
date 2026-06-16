from src.models.evidence_hit import EvidenceHit
from src.models.watchlist import WatchlistEntity
from src.config_loader import Config, ScoringConfig
from datetime import datetime, timezone
from dataclasses import replace


class RelevanceScorer:
    """
    answers: “Given this evidence record, how important/relevant is it to the watchlist entity?”
    """

    def __init__(self, config: Config):
        self.config = config
        self.rules: ScoringConfig = config.scoring

    def score(self, hit: EvidenceHit, entity: WatchlistEntity) -> EvidenceHit:
        """
        takes an instance of EvidenceHit paired with a specific entity and returns
        the same hit enriched with scoring metadata.

        :param hit: a single instance of EvidenceHit object
        :param entity: a single instance of WatchlistEntity
        :return: same hit, enriched with scoring metadata
        """
        score = 0
        reasons: list[str] = []

        text = hit.matching_text.lower()
        entity_match_names = self.rules.entity_match
        source_weights = self.rules.source_weight
        penalties = self.rules.penalties

        # Did the text match the entity?

        # Name match
        if entity.name.lower() in text:
            score += entity_match_names['exact_name']
            reasons.append(f'exact entity match: {entity.name}')

        # Aliases Match
        matched_aliases = []
        for alias in entity.manual_aliases:
            if alias.lower() in text:
                score += entity_match_names['manual_alias']
                matched_aliases.append(alias)
                reasons.append(f'manual alias match: {alias}')

        # Concept matches
        for concept_id in hit.matched_concepts:
            concept = self.config.get_concept(concept_id)

            if concept_id in entity.priority_concepts:
                score += concept.score
                reasons.append(f'matched priority concept: {concept_id}')
            else:
                score += 1
                reasons.append(f'matched non-priority concept: {concept_id}')

        # Source weight
        source_weight = source_weights.get(hit.source, 0)
        score += source_weight

        if source_weight:
            reasons.append(f'source weight: {hit.source} +{source_weight}')

        # Negative Terms
        matched_negative_terms = []

        for term in entity.negative_terms:
            if term.lower() in text:
                score += penalties.get('negative_term_match', 0)  # += because the number is negative in the yaml
                matched_negative_terms.append(term)
                reasons.append(f'matched negative term: {term}')

        # Recency
        recency_score = self._recency_score(hit)
        score += recency_score

        if recency_score:
            reasons.append(f'recency bonus +{recency_score}')

        # Label
        label = self._label(score)

        # URL
        missing_url_penalty = self.rules.penalties['missing_url']
        if hit.url is None:
            score += missing_url_penalty
            reasons.append(f'missing url penalty applied: {missing_url_penalty}')


        return replace(hit,
                       matched_aliases=matched_aliases,
                       matched_negative_terms=matched_negative_terms,
                       relevance_score=score,
                       relevance_label=label,
                       reason="; ".join(reasons),
                       )

    def _recency_score(self, hit: EvidenceHit) -> int:
        if hit.published_at is None:
            return self.rules.penalties.get('missing_date')

        now = datetime.now(timezone.utc)
        published_at = hit.published_at

        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at)

        elif isinstance(published_at, date) and not isinstance(published_at, datetime):
            published_at = datetime.combine(published_at, datetime.min.time())

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        age_days = (now - published_at).days
        recency = self.rules.recency

        if age_days <= 1:
            return recency['within_1_days']
        elif age_days <= 3:
            return recency['within_3_days']
        elif age_days <= 7:
            return recency['within_7_days']
        elif age_days <= 14:
            return recency['within_14_days']
        else:
            return recency['older_than_14_days']

    def _label(self, score) -> str:
        labels = self.rules.labels

        if score >= labels['high']['min_score']:
            return 'high'
        elif score < labels['medium']['min_score']:
            return 'medium'

        return 'low'
