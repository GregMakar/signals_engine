from src.config_loader import Config
from src.models.concept import Concept
import re
from collections import defaultdict

class ConceptMatcher:
    """
    Reusable service for detecting configured concepts inside raw text.

    ConceptMatcher receives the concept definitions loaded from the YAML config
    and scans input text for any terms associated with those concepts. It returns
    a dictionary mapping each matched concept ID to the exact terms that triggered
    the match.

    Its only responsibility is concept detection.

    Example:
        Input text:
            "Codelco workers walk off the job after failed wage talks."

        Output:
            {
                "labor_disruption": ["walk off", "failed wage talks"]
            }

    Future versions may replace or extend exact phrase matching with more advanced
    NLP techniques such as text normalization, stemming, lemmatization, embeddings,
    semantic similarity, or classifier-based concept detection.
    """

    def __init__(self, config: Config):
        self.concepts = config.concepts


    def match_one(self, text: str, category: str) -> dict[str, list[str]]:
        """

        :param text: line of text to carry out operations on
        :param category: one concept to match
        :return: {'labor_disruption': ['strike', 'union dispute']} a key | concept: value list[matched terms]
        """

        words_ = [word for word in re.split(r"[,\s]+", text.strip().lower()) if word]
        terms_by_len = defaultdict(set)
        terms = self.concepts[category].terms

        for term in terms:
            parts = tuple(term.lower().split())
            terms_by_len[len(parts)].add(parts)

        valid_lengths = sorted(terms_by_len)

        matches = []

        for i in range(len(words_)):
            for length in valid_lengths:
                if i + length > len(words_):
                    break

                window = tuple(words_[i:i + length])

                if window in terms_by_len[length]:
                    matches.append(' '.join(window))

        return {category: matches} if matches else {}



    def match_all(self, text: str) -> dict[str, list[str]]:
        """
        This func will clean the input text, and match concepts present in the Config.concepts
        it was passed.
        :param text: headline or text that is returned after making an API call.
        :return: matched concepts' dict, where ex. Key: labour_disruption, Value: list[matched terms...
        ex. strike, walkout, work stoppage]
        """
        matched = {}

        for concept_id in self.concepts:
            result = self.match_one(text=text, category=concept_id)
            matched.update(result)

        return matched