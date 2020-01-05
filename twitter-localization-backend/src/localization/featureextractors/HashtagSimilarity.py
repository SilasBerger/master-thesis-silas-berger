import operator

from src.localization import LocalizationConstants
from src.localization.Database import Database
from src.localization.featureextractors.TopHashtags import TopHashtags
from src.util import timing


class HashtagSimilarity(TopHashtags):

    def __init__(self, train_set, vector_length, use_cached_vector, allow_cache_updates=False):
        super().__init__(vector_length, allow_cache_updates=allow_cache_updates, fe_name="hashtag_similarity")
        self._average_swiss_vector = None
        self._init_reference_vector(train_set, use_cached_vector, allow_cache_updates)
        self._average_swiss_vector = set(self._average_swiss_vector)

    def _init_reference_vector(self, train_set, use_cached_vector, allow_cache_updates):
        if use_cached_vector:
            self._average_swiss_vector = self._fetch_cached_average_swiss_vector()
        if self._average_swiss_vector is None:
            self._average_swiss_vector = self._calculate_average_swiss_hashtag_vector(train_set)
            if allow_cache_updates:
                self._cache_average_swiss_vector()

    def _extract_for(self, twitter_user):
        user_tweets = TopHashtags._collect_tweets_for_user(twitter_user["id"])
        user_top_hashtags = set(self._calculate_top_hashtags(user_tweets, include_counts=False))
        return self._calculate_similarity(user_top_hashtags)

    def _calculate_similarity(self, user_top_hashtags):
        common_hashtags = user_top_hashtags.intersection(self._average_swiss_vector)
        return len(common_hashtags) / self._vector_length

    def _cache_average_swiss_vector(self):
        obj = {
            LocalizationConstants.INTERMEDIATE_RESULT: "top_swiss_hashtags",
            "vector": self._average_swiss_vector,
            "vector_length": self._vector_length
        }
        Database.instance().feature_cache.save(obj)

    def _fetch_cached_average_swiss_vector(self):
        obj = Database.instance().feature_cache.find_one({
            LocalizationConstants.INTERMEDIATE_RESULT: "top_swiss_hashtags",
            "vector_length": self._vector_length
        })
        if obj is None:
            return None
        return obj["vector"]

    def _calculate_average_swiss_hashtag_vector(self, train_set):
        print(timing.get_timestamp() + ": HashtagSimilarity: extracting average swiss hashtag vector")
        swiss_ids = [user["id"] for user in train_set]
        swiss_tweets = [t for t in Database.instance().tweets_mongodb.find({"author_id": {"$in": swiss_ids}})]
        return self._calculate_top_hashtags(swiss_tweets, include_counts=False)


