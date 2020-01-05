from src.localization.FeatureExtractor import FeatureExtractor


class SwissInfluencersFollowedRatio(FeatureExtractor):

    def __init__(self, allow_cache_updates=False):
        super().__init__("swiss_influencers_followed_ratio", allow_cache_updates)

    def _extract_for(self, twitter_user):
        num_total_friends = twitter_user["friends_count"]
        if num_total_friends == 0:
            return 0
        num_ch_influencers_followed = self._count_swiss_influencers_followed(twitter_user)
        return num_ch_influencers_followed/num_total_friends

    def _count_swiss_influencers_followed(self, twitter_user):
        result = self._db.users_mongodb.find({
            "type": "influencer",
            "followerIds": {"$elemMatch": {"$eq": twitter_user["id"]}}
        })
        return result.count()
