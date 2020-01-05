from src.localization.FeatureExtractor import FeatureExtractor
from src.localization.Database import Database


class TweetInteractionBehavior(FeatureExtractor):

    def __init__(self, allow_cache_updates=False, fe_name="tweet_interaction_behavior"):
        super().__init__(fe_name, allow_cache_updates)

    def _extract_for(self, twitter_user):
        user_tweets_cursor = Database.instance().tweets_mongodb.find({
            "author_id": twitter_user["id"]
        })
        num_tweets = user_tweets_cursor.count()
        if num_tweets == 0:
            return [0, 0, 0]
        mention_ids, retweet_ids, reply_ids = TweetInteractionBehavior._find_interactions(user_tweets_cursor)
        return [len(mention_ids)/num_tweets, len(retweet_ids)/num_tweets, len(reply_ids)/num_tweets]

    @staticmethod
    def _find_interactions(tweets_cursor):
        mention_ids = []
        retweet_ids = []
        reply_ids = []
        for tweet in tweets_cursor:
            TweetInteractionBehavior._extract_mention_ids(tweet, mention_ids)
            TweetInteractionBehavior._extract_retweet_id(tweet, retweet_ids)
            TweetInteractionBehavior._extract_reply_id(tweet, reply_ids)
        return set(mention_ids), set(retweet_ids), set(reply_ids)

    @staticmethod
    def _extract_mention_ids(tweet, mention_ids):
        entities = tweet.get("entities", None)
        if entities is None:
            return
        mentions = entities.get("user_mentions", None)
        if mentions is None:
            return
        for mention in mentions:
            mention_ids.append(mention["id"])

    @staticmethod
    def _extract_retweet_id(tweet, retweet_ids):
        if tweet.get("retweeted_status_author_id", None) is not None:
            retweet_ids.append(tweet["retweeted_status_author_id"])

    @staticmethod
    def _extract_reply_id(tweet, reply_ids):
        if tweet.get("in_reply_to_user_id", None) is not None:
            reply_ids.append(tweet["in_reply_to_user_id"])
