from src.models.evidence_hit import EvidenceHit
from src.models.types import RoutingDecision
from src.models.watchlist import WatchlistEntity
from src.models.scored_evidence_hit import ScoredEvidenceHit, ScoreComponent
from src.config_loader import Config, ScoringConfig
from datetime import datetime, timezone, date
import requests

class RelevanceScorer:
    """
    answers: “Given this evidence record, how important/relevant is it to the watchlist entity?”
    """

    def __init__(self, config: Config):
        self.config = config
        self.rules: ScoringConfig = config.scoring

    def score(self, hit: EvidenceHit, entity: WatchlistEntity) -> ScoredEvidenceHit:
        """
        rules should eventually be dynamically generated using (back prop?, neural net?, backtesting?)

        scoring is divided into 4 buckets:
        relevance_score  = how related is this to my watchlist?
        severity_score   = how serious is the event?
        confidence_score = how trustworthy/strong is the evidence?
        novelty_score    = is this new or duplicate?

        :param hit: a single instance of EvidenceHit object
        :param entity: a single instead of the relevant entity that the scoring is being based on
        :return: ScoredEvidenceHit
        """
        total_score = 0.0
        score_components: list[ScoreComponent]= []

        relevance = self._relevance_scorer(hit, entity)
        total_score += relevance[0]
        score_components.extend(relevance[1])

        recency = self._recency_score(hit)
        total_score += recency[0]
        score_components.extend(recency[1])

        severity = self._severity_score(hit)
        total_score += severity[0]
        score_components.extend(severity[1])

        confidence = self._confidence_score(hit)
        total_score += confidence[0]
        score_components.extend(confidence[1])

        return ScoredEvidenceHit(
            evidence_hit=hit,
            total_score=total_score,
            relevance_score=relevance[0],
            severity_score=severity[0],
            confidence_score=confidence[0],
            novelty_score=0.0,
            relevance_label=self._label(total_score),
            score_components=score_components,
            routing_decision=self.routing_decision(total_score)

        )


    def routing_decision(self, score) -> RoutingDecision:
        if score <= 2:
            return 'ignore'
        elif score <= 5:
            return 'store_only'
        elif score <= 7:
            return 'manual_review'
        else:
            return 'alert'

    def _relevance_scorer(self, hit: EvidenceHit, entity: WatchlistEntity) -> tuple[float, list[ScoreComponent]]:
        """
        Relevance has 4 parts:
        - HitsScope: summary/classification derived from MatchReasons list. they are ranked in the following order.
        ["direct", "related", "context", "unknown"]
        - entity match: in what way was the entity matched, was it an allias match?, a cameo code realtive
        to entity? a concept keyword with entity?
        - entity priority: assigned prio to specific entity relative to the rest of the YAML.
        - context_keys: sector context, commodity context ,country/region context, risk theme context.
        they are not exact entity matches. they generally refer to the whole YAML file content, not just
        the specific program run.

        :param hit: a verified hit instance
        :param entity: the entity to score relative to
        :return: relevance score float
        """
        rel_score_val: float = 0.0
        score_comp: list[ScoreComponent] = []

        # HitScope
        if hit.hit_scope:
            rel_score_val += self.rules.relevance['hit_scope'].get(hit.hit_scope)
            score_comp.append(ScoreComponent(
                name=hit.hit_scope,
                value=self.rules.relevance['hit_scope'].get(hit.hit_scope),
                reason= hit.hit_scope
            ))

        # MatchReason match types scored
        for match in hit.match_reasons:
            value = self.rules.relevance['entity_match'].get(match.matcher)
            rel_score_val += value
            score_comp.append(ScoreComponent(
                name=match.matched_id,
                value=value,
                reason=match.reason
            ))

        # entity importance scoring
        entity_prio = self.config.entities.get(entity.id).priority
        value = self.rules.relevance['entity_priority'].get(entity_prio)
        rel_score_val += value
        score_comp.append(ScoreComponent(
            name='entity_priority',
            value=value,
            reason=f'entity priority: {entity_prio} | bonus weight: {value}'
        ))

        # context_keys: Commodity Matching
        all_commodities = [[commodity.id].extend(commodity.manual_aliases)
                           for commodity in self.config.entities.values()
                           if commodity.entity_type == 'commodity']
        if not hit.commodities:
            count = 0.0
            for key in hit.context_keys:
                if key in all_commodities:
                    count += 1
            value = self.rules.relevance['context_keys'].get('commodity_match') * count
            rel_score_val += value
            score_comp.append(ScoreComponent(
                name= 'commodity match',
                value= value,
                reason= f'Context Key: commodities | match count: {count} | bonus: {value}'
            ))
        else:
            count = 0.0
            for commodity in hit.commodities:
                if commodity in all_commodities:
                    count += 1
            value = self.rules.relevance['context_keys'].get('commodity_match') * count
            rel_score_val += value
            score_comp.append(ScoreComponent(
                name='commodity match',
                value=value,
                reason=f'Self.commodities match count: {count} | bonus: {value}'
            ))

        # context_keys: Sector Matching
        # INCOMPLETE
        # possible enrichment route -> WikiData

        # context_keys Geography (country):
        # INCOMPLETE, too broad/specific
        # possible enrichment route -> WikiData
        all_countries = [[country.id].extend(country.manual_aliases)
                           for country in self.config.entities.values()
                           if country.entity_type == 'country']
        if hit.geography:
            count = 0.0
            for country in hit.geography:
                if country in all_countries:
                    count += 1
            value = self.rules.relevance.get('context_keys').get('geography_match') * count
            rel_score_val += value
            score_comp.append(ScoreComponent(
                name='geography match',
                value=value,
                reason=f'Self.geography match count: {count} | bonus: {value}'
            ))

        else:
            count = 0.0
            for key in hit.context_keys:
                if key in all_countries:
                    count += 1
            value = self.rules.relevance['context_keys'].get('geography_match') * count
            rel_score_val += value
            score_comp.append(ScoreComponent(
                name='geography match',
                value=value,
                reason=f'Context keys: geography | match count: {count} | bonus: {value}'
            ))

        # context_keys: risk_theme_match
        # INCOMPLETE
        # only viable for GDELT, until NLP processing

        return rel_score_val, score_comp

    def _recency_score(self, hit: EvidenceHit) -> tuple[float, list[ScoreComponent]]:

        if hit.occurred_at is None and hit.published_at is None:
            pen_value = self.rules.penalties.get('missing_date')
            return pen_value, [ScoreComponent(
                name='PENALTY: Missing Date',
                value=pen_value,
                reason=f'missing date penalty {pen_value}'
            )]

        elif hit.occurred_at:
            published_at = hit.occurred_at
        else:
            published_at = hit.published_at

        now = datetime.now(timezone.utc)

        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at)

        elif isinstance(published_at, date) and not isinstance(published_at, datetime):
            published_at = datetime.combine(published_at, datetime.min.time())

        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        age_days = (now - published_at).days
        recency = self.rules.recency

        if age_days <= 1:
            recency_bonus = recency.get('within_1_days')
            return recency_bonus, [ScoreComponent(
                name = 'less then 24 hours',
                value= recency_bonus,
                reason= f'less than 24 hours bonus {recency_bonus}',
            )]
        elif age_days <= 3:
            recency_bonus = recency.get('within_3_days')
            return recency_bonus, [ScoreComponent(
                name = 'under 3 days old',
                value= recency_bonus,
                reason= f'under 3 days old bonus: {recency_bonus}',
            )]
        elif age_days <= 7:
            recency_bonus = recency.get('within_7_days')
            return recency_bonus, [ScoreComponent(
                name = 'under a week old',
                value= recency_bonus,
                reason= f'under a week old bonus: {recency_bonus}',
            )]
        elif age_days <= 14:
            recency_bonus = recency.get('within_14_days')
            return recency_bonus, [ScoreComponent(
                name = 'under 2 weeks old',
                value= recency_bonus,
                reason= f'under 2 weeks old bonus: {recency_bonus}',
            )]
        else:
            recency_bonus = recency.get('older_than_14_days')
            return recency_bonus, [ScoreComponent(
                name = 'older than 2 weeks',
                value= recency_bonus,
                reason= f'older than 2 weeks bonus: {recency_bonus}',
            )]

    def _label(self, score) -> str:
        labels = self.rules.labels

        if score >= labels['critical']['min_score']:
            return 'critical'
        elif score >= labels['high']['min_score']:
            return 'high'
        elif score >= labels['medium']['min_score']:
            return 'medium'

        return 'low'

    def _severity_score(self, hit: EvidenceHit) -> tuple[float, list[ScoreComponent]]:
        sev_score: float = 0.0
        score_comp: list[ScoreComponent]= []

        for match in hit.match_reasons:
            if match.matcher == 'concept_keyword':
                sev_bonus = self.rules.severity.get('concept_weights').get(match.matched_id, 'default_weight')
                sev_score += sev_bonus
                score_comp.append(ScoreComponent(
                    name='concept match',
                    value=sev_bonus,
                    reason=f'concept keyword match | matching value: {match.value} | match ID: {match.matched_id}'
                ))


        if (self.rules.severity.get('gdelt').get('apply_concept_severity_weight')
                and hit.record_ref.source == 'gdelt'):
            for match in hit.match_reasons:
                if match.matcher == 'cameo_code':
                    cameo_score = self.rules.severity.get('gdelt').get('cameo_exact_weights').get(match.value, 0)
                    if cameo_score == 0:
                        cameo_score = self.rules.severity.get('gdelt').get('cameo_root_weights').get(match.value)
                    sev_score += cameo_score
                    score_comp.append(ScoreComponent(
                        name='cameo match',
                        value=cameo_score,
                        reason=f'CAMEO code match | Code: {match.value} | Bonus: {cameo_score}'
                    ))
                if match.value in self.rules.severity.get('gdelt').get('severe_cameo_codes'):
                    sev_cam_bonus = self.rules.severity.get('gdelt').get('severe_cameo_bonus')
                    sev_score += sev_cam_bonus
                    score_comp.append(ScoreComponent(
                        name='severe cameo match',
                        value= sev_cam_bonus,
                        reason=f'Sever CAMEO match | CAMEO Code: {match.value} | Bonus: {sev_cam_bonus}'
                    ))

        return sev_score, score_comp

    def _confidence_score(self, hit: EvidenceHit) -> tuple[float, list[ScoreComponent]]:
        conf_score = 0.0
        score_comp: list[ScoreComponent] = []

        value = self.rules.confidence.get('source_weight').get(hit.record_ref.source, 0)
        conf_score += value
        score_comp.append(ScoreComponent(
            name='Source Weight Bonus',
            value= value,
            reason=f'source weight bonus: {value}'
        ))

        if hit.record_ref.source == 'gdelt':
            # Uses GDELT NumSources
            num_src = hit.source_fields.get('numsources')
            if num_src >= self.rules.confidence.get('gdelt').get('num_sources').get('high_threshold'):
                value = self.rules.confidence.get('gdelt').get('num_sources').get('high_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='NumSources bonus HIGH',
                    value=value,
                    reason=f'GDELT NumSources Bonus value {value}'
                ))
            elif num_src >= self.rules.confidence.get('gdelt').get('num_sources').get('medium_threshold'):
                value = self.rules.confidence.get('gdelt').get('num_sources').get('medium_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='NumSources bonus Medium',
                    value=value,
                    reason=f'GDELT NumSources Bonus value {value}'
                ))

            # Uses GDELT NumMentions.
            num_men = hit.source_fields.get('nummentions')
            if num_men >= self.rules.confidence.get('gdelt').get('num_mentions').get('high_threshold'):
                value = self.rules.confidence.get('gdelt').get('num_mentions').get('high_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='NumMentions bonus HIGH',
                    value=value,
                    reason=f'GDELT NumMentions Bonus value {value}'
                ))
            elif num_men >= self.rules.confidence.get('gdelt').get('num_mentions').get('medium_threshold'):
                value = self.rules.confidence.get('gdelt').get('num_mentions').get('medium_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='NumMentions bonus Medium',
                    value=value,
                    reason=f'GDELT NumMentions Bonus value {value}'
                ))

            # Uses GDELT NumArticles.
            num_men = hit.source_fields.get('numarticles')
            if num_men >= self.rules.confidence.get('gdelt').get('num_articles').get('high_threshold'):
                value = self.rules.confidence.get('gdelt').get('num_articles').get('high_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='NumArticles bonus HIGH',
                    value=value,
                    reason=f'GDELT NumArticles Bonus value {value}'
                ))
            elif num_men >= self.rules.confidence.get('gdelt').get('num_articles').get('medium_threshold'):
                value = self.rules.confidence.get('gdelt').get('num_articles').get('medium_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='NumArticles bonus Medium',
                    value=value,
                    reason=f'GDELT NumArticles Bonus value {value}'
                ))

            # Uses GDELT Mentions Confidence
            men_conf = hit.source_fields.get('confidence')
            if men_conf >= self.rules.confidence.get('gdelt').get('mention_confidence').get('high_threshold'):
                value = self.rules.confidence.get('gdelt').get('mention_confidence').get('high_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='GDELT Confidence bonus HIGH',
                    value=value,
                    reason=f'GDELT Confidence Bonus value {value}'
                ))

            elif men_conf >= self.rules.confidence.get('gdelt').get('mention_confidence').get('medium_threshold'):
                value = self.rules.confidence.get('gdelt').get('mention_confidence').get('medium_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='GDELT Confidence bonus Medium',
                    value=value,
                    reason=f'GDELT Confidence Bonus value {value}'
                ))

            if hit.url:
                value = self.rules.confidence.get('gdelt').get('has_url_weight')
                conf_score += value
                score_comp.append(ScoreComponent(
                    name='GDELT URL present',
                    value=value,
                    reason=f'GDELT URL present bonus: {value}'
                ))
                response = requests.get(hit.url)
                if response.status_code == 404:
                    value = self.rules.penalties.get('url_404')
                    conf_score += value
                    score_comp.append(ScoreComponent(
                        name='GDELT URL Verification penalty',
                        value= value,
                        reason='URL request status code: 404'
                    ))

            value = (self.rules.confidence.get('gdelt')
                           .get('source_quality')
                           .get(hit.source_fields
                            .get('source_quality')))
            conf_score += value
            score_comp.append(ScoreComponent(
                name='GDELT source quality bonus',
                value=value,
                reason=f'GDELT source quality bonus: {value}'
            ))

        return conf_score, score_comp