import numpy as np

from src.localization.Database import Database
from src.localization.featureextractors.TweetInteractionBehavior import TweetInteractionBehavior


class SwissTweetInteraction(TweetInteractionBehavior):

    def __init__(self, aggregate_interactions=False, allow_cache_updates=False):
        super().__init__(fe_name=("swiss_tweet_interaction" + ("_agg" if aggregate_interactions else "")),
                         allow_cache_updates=allow_cache_updates)
        self._aggregate_interactions = aggregate_interactions

    def _extract_for(self, twitter_user):
        user_tweets_cursor = Database.instance().tweets_mongodb.find({
            "author_id": twitter_user["id"]
        })
        if user_tweets_cursor.count() == 0:
            if self._aggregate_interactions:
                return 0
            return [0, 0, 0]
        mention_ids, retweet_ids, reply_ids = TweetInteractionBehavior._find_interactions(user_tweets_cursor)
        if self._aggregate_interactions:
            return SwissTweetInteraction._calculate_aggregate_interactions(mention_ids, retweet_ids, reply_ids)
        return SwissTweetInteraction._calculate_individual_interactions(mention_ids, retweet_ids, reply_ids)

    @staticmethod
    def _filter_for_swiss_ids(user_ids_list):
        ch_ids_cursor = Database.instance().users_mongodb.find({
            "is_swiss": True,
            "id": {"$in": user_ids_list}
        }, {"id": 1})
        ch_test_ids_cursor = Database.instance().users_test_set_mongodb.find({
            "is_swiss": True,
            "id": {"$in": user_ids_list}
        }, {"id": 1})
        return set([u["id"] for u in ch_ids_cursor]).union(set([u["id"] for u in ch_test_ids_cursor]))

    def _calculate_interactions_feature(self, mentions, retweets, replies):
        if self._aggregate_interactions:
            return SwissTweetInteraction._calculate_aggregate_interactions(mentions, retweets, replies)
        return SwissTweetInteraction._calculate_individual_interactions(mentions, retweets, replies)

    @staticmethod
    def _calculate_aggregate_interactions(mentions, retweets, replies):
        total_num_interactions = len(mentions) + len(retweets) + len(replies)
        interactions = list(mentions.union(retweets).union(replies))
        interactions_ch_filtered = SwissTweetInteraction._filter_for_swiss_ids(interactions)
        return len(interactions_ch_filtered) / total_num_interactions

    @staticmethod
    def _calculate_individual_interactions(mentions, retweets, replies):
        interactions = list(mentions.union(retweets).union(replies))
        interactions_ch_filtered = SwissTweetInteraction._filter_for_swiss_ids(interactions)
        filtered_mentions = [uid for uid in interactions_ch_filtered if uid in mentions]
        filtered_retweets = [uid for uid in interactions_ch_filtered if uid in retweets]
        filtered_replies = [uid for uid in interactions_ch_filtered if uid in replies]
        return [len(filtered_mentions)/max(len(mentions), 1), len(filtered_retweets)/max(len(retweets), 1),
                len(filtered_replies)/max(len(replies), 1)]
