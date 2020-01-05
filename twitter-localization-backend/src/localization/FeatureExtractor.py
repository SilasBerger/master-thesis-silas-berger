import pymongo

from src.localization.Database import Database


class FeatureExtractor:
    """
    add doc
    """

    def __init__(self, name, allow_cache_updates=False):
        self._db = Database.instance()
        self._name = name
        self._allow_cache_updates = allow_cache_updates

    def extract_for(self, twitter_user, use_cache=False):
        """
        Extracts and returns this feature extractor's feature for a given Twitter user
        :param twitter_user: Twitter user object with user_id, screen_name and graph_id
        :return: extracted feature for this user, format and semantics depend on each implementation
        """
        value = self._fetch_cached_feature_value(twitter_user, use_cache)
        if value is None:
            # feature value was not cached, or cache is disabled for this request - extract feature
            value = self._extract_for(twitter_user)
            if self._allow_cache_updates:
                # extracted the feature value for this user - update the chache if updates are enabled
                self._update_cache(twitter_user, value)
        return value

    def _extract_for(self, twitter_user):
        raise NotImplementedError("function _extract_for() is abstract in FeatureExtractor")

    def _fetch_cached_feature_value(self, twitter_user, use_cache):
        if not use_cache:
            return None
        cached_user = self._db.feature_cache.find_one({"id": twitter_user["id"]})
        if (cached_user is not None) and (self._name in cached_user):
            return cached_user[self._name]
        return None

    def _update_cache(self, twitter_user, feature_value):
        cached_user = self._db.feature_cache.find_one({"id": twitter_user["id"]})
        if cached_user is None:
            cached_user = {"id": twitter_user["id"]}
        cached_user[self._name] = feature_value
        self._db.feature_cache.save(cached_user)
