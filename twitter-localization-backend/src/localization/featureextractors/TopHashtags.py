import operator
import unidecode

from src.localization.FeatureExtractor import FeatureExtractor
from src.localization.Database import Database


class TopHashtags(FeatureExtractor):

    def __init__(self, vector_length,  allow_cache_updates=False, fe_name="top_hashtags"):
        super().__init__(fe_name, allow_cache_updates)
        self._vector_length = vector_length

    def _extract_for(self, twitter_user):
        user_tweets = TopHashtags._collect_tweets_for_user(twitter_user["id"])
        return self._calculate_top_hashtags(user_tweets, include_counts=False)

    @staticmethod
    def _collect_tweets_for_user(user_id):
        tweets_cursor = Database.instance().tweets_mongodb.find({"author_id": user_id})
        return [tweet for tweet in tweets_cursor]

    def _calculate_top_hashtags(self, tweets, include_counts=False):
        hashtags = {}
        for tweet in tweets:
            tweet_hashtags = [ht["text"] for ht in tweet["entities"]["hashtags"]]
            for hashtag in tweet_hashtags:
                n_hashtag = TopHashtags._normalize_hashtag(hashtag)
                hashtags[n_hashtag] = hashtags.get(n_hashtag, 0) + 1
        hashtag_ranking = sorted(hashtags.items(), key=operator.itemgetter(1), reverse=True)
        top_n = hashtag_ranking[0:self._vector_length]
        if include_counts:
            return top_n
        return [ht[0] for ht in top_n]

    @staticmethod
    def _normalize_hashtag(hashtag):
        return unidecode.unidecode(hashtag).lower()
