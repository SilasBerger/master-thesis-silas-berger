from src.localization.FeatureExtractor import FeatureExtractor


class SwissFriendsRatio(FeatureExtractor):

    def __init__(self, allow_cache_updates=False):
        super().__init__("swiss_friends_ratio", allow_cache_updates)

    def _extract_for(self, twitter_user):
        num_total_friends = twitter_user["friends_count"]
        if num_total_friends == 0:
            return 0
        num_swiss_friends = self._count_swiss_influencers_followed(twitter_user)
        return num_swiss_friends/num_total_friends

    def _count_swiss_influencers_followed(self, twitter_user):
        friend_ids = twitter_user.get("friend_ids", [])
        if len(friend_ids) == 0:
            return 0
        ch_friend_ids_cursor = self._db.users_mongodb.find({
            "is_swiss": True,
            "id": {"$in": friend_ids}
        }, {"id": 1})
        ch_test_friend_ids_cursor = self._db.users_test_set_mongodb.find({
            "is_swiss": True,
            "id": {"$in": friend_ids}
        }, {"id": 1})
        ch_friend_ids = set([u["id"] for u in ch_friend_ids_cursor])
        ch_test_friend_ids = set([u["id"] for u in ch_test_friend_ids_cursor])
        return len(ch_friend_ids.union(ch_test_friend_ids))
