import json

import spacy
import unidecode

from src.localization import LocalizationConstants
from src.localization.Database import Database
from src.localization.FeatureExtractor import FeatureExtractor
from src.util import paths


class SwissNamedPlaces(FeatureExtractor):

    def __init__(self, allow_cache_updates=False, count_only=True):
        super().__init__(("swiss_named_places_count" if count_only else "swiss_named_places"), allow_cache_updates)
        self._get_count = count_only
        self._nlp = {
            "de": spacy.load('de_core_news_sm'),
            "fr": spacy.load('fr_core_news_sm'),
            "it": spacy.load('it_core_news_sm'),
            "en": spacy.load('en_core_web_sm')
        }
        with open(paths.convert_project_relative_path("data/ner_place_stopwords.json"), "r", encoding="utf-8") as fp:
            self._stopwords = json.load(fp)["stopwords"]
        self._reference_set = self._build_geo_reference_set()

    def _extract_for(self, twitter_user):
        ne_set = self._perform_ner(twitter_user["id"])
        if self._get_count:
            return len(ne_set)
        return ne_set

    @staticmethod
    def _build_geo_reference_set():
        geo_names = set([])
        swiss_places_cursor = Database.instance().geonames_places_mongodb.find({
            "country_id": str(LocalizationConstants.GEOID_SWITZERLAND),
            "feature_code": {"$in": ["PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"]}
        })
        for place in swiss_places_cursor:
            name = unidecode.unidecode(place["name"]).lower()
            geo_names.add(name)
        return geo_names

    def _perform_ner(self, user_id):
        tweets_cursor = Database.instance().tweets_mongodb.find({"author_id": user_id})
        tokens = self._tokenize_user_tweets(tweets_cursor)
        return tokens.intersection(self._reference_set)

    def _tokenize_user_tweets(self, tweets):
        tokens = set([])
        for tweet in tweets:
            tokens = tokens.union(self._extract_places(tweet))
        return tokens

    def _extract_places(self, tweet):
        proper_nouns = set([])
        nlp = self._nlp.get(tweet["lang"], None)
        if nlp is None:
            return proper_nouns
        tokens = nlp(tweet["text"].replace("#", ""))
        for token in tokens:
            if token.ent_type_ in ["LOC", "GPE"]:
                n_place = unidecode.unidecode(token.text).strip().lower()
                if n_place not in self._stopwords:
                    proper_nouns.add(n_place)
        return proper_nouns
