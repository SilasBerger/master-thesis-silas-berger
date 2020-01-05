import time
import tweepy
from src.twitter import twitter_api_util
from src.util import context, timing


class TwitterApiBinding:
    """
    Wrapper around the Tweepy binding, facilitates fetching data, iterating through cursors, handling rate limits, etc.
    """

    # wait this many seconds before asking for the next cursor page
    _PAGE_FETCH_DELAY_SECONDS = 0.5

    def __init__(self):
        TwitterApiBinding._instance_created = True
        self._setup_twitter_api()

    def _setup_twitter_api(self):
        self._auth = tweepy.OAuthHandler(context.get_credentials("twitter_api_key"),
                                         context.get_credentials("twitter_api_key_secret"))
        self._auth.set_access_token(context.get_credentials("twitter_access_token"),
                                    context.get_credentials("twitter_access_token_secret"))
        self._twitter_api = tweepy.API(self._auth,
                                       wait_on_rate_limit=True,
                                       wait_on_rate_limit_notify=True,
                                       retry_count=0)

    def _await_rate_limit(self, endpoint_path):
        wait_time = twitter_api_util.get_rate_limit_reset(self._twitter_api, endpoint_path) + 1
        print(timing.get_timestamp() + ":", "rate limit reached, waiting " + str(wait_time) + " minutes")
        time.sleep(wait_time * 60)

    def _handle_tweep_error_generic(self, tweep_error, endpoint_path):

        if tweep_error.response.status_code == 429:
            # rate limit, wasn't caught as RateLimitError
            self._await_rate_limit(endpoint_path)
            return True
        elif tweep_error.api_code in [63, 64]:
            # suspended user account
            return True
        else:
            # general tweep error, graceful shutdown
            print("TweepError encountered, shutting down")
            print("Error:", tweep_error)
            exit(1)

    def _iterate_cursor(self, cursor, endpoint_path):
        """
        Cursor page generator, prints current rate limit status at set interval, excepts rate limit error, waits
        for specified interval until rate limit is lifted
        :param cursor: tweepy.Cursor to crawl
        :return: next page from Cursor
        """
        while True:
            try:
                yield cursor.next()
            except tweepy.RateLimitError:
                self._await_rate_limit(endpoint_path)
            except tweepy.TweepError as err:
                self._handle_tweep_error_generic(err, endpoint_path)

    def _execute_api_call(self, endpoint_path, call, *args, **kwargs):
        try:
            return call(*args, **kwargs)
        except tweepy.RateLimitError:
            self._await_rate_limit(endpoint_path)
            self._execute_api_call(call, *args)
        except tweepy.TweepError as err:
            if err.response.status_code == 429:
                # rate limit, wasn't caught as RateLimitError
                self._await_rate_limit(endpoint_path)
                return call(*args)
            elif err.api_code in [63, 64]:
                # suspended user account
                return None
            elif err.api_code == 50:
                # user not found
                return None
            else:
                # general tweep error, graceful shutdown
                print("TweepError encountered, shutting down")
                print("Error:", err)
                exit(1)

    # === Public API Calls === #

    def find_user(self, screen_name):
        return self._execute_api_call("/users/show/:id", self._twitter_api.get_user, screen_name)

    def find_user_by_id(self, user_id):
        try:
            return self._twitter_api.get_user(user_id=user_id)
        except tweepy.RateLimitError:
            print("TwitterApiBinding#find_user_by_id: rate limit error wasn't caught by API wrapper, shutting down")
            exit(1)
        except tweepy.TweepError as err:
            if err.response.status_code == 429:
                print("TwitterApiBinding#find_user_by_id: rate limit error wasn't caught by API wrapper, shutting down")
                exit(1)
            elif err.api_code in [63, 64]:
                # suspended user account
                return None
            elif err.api_code == 50:
                # user not found
                return None
            else:
                # general tweep error, graceful shutdown
                print("TweepError encountered, shutting down")
                print("Error:", err)
                exit(1)

    def find_multiple_users(self, user_ids):
        assert type(user_ids) == list
        assert len(user_ids) <= 100
        try:
            return self._twitter_api.lookup_users(user_ids=user_ids)
        except tweepy.RateLimitError as err:
            print("TwitterApiBinding#find_multiple_users: unexpected rate limit error - shutting down")
            exit(1)
        except tweepy.TweepError as err:
            if err.response.status_code == 429:
                print("TwitterApiBinding#find_multiple_users: unexpected code 492 (rate limit) - shutting down")
                exit(1)
            if err.response.status_code == 404:
                return None
            print("TwitterApiBinding#find_multiple_users: uncaught TweepError - shutting down")
            print(err)
            exit(1)

    def get_follower_ids(self, user_id):
        # return self._execute_api_call(self._twitter_api.followers_ids, user_id)
        follower_ids_list = []
        cursor_settings = {
            "id": user_id,
            "monitor_rate_limit": True,
            "wait_on_rate_limit": True,
            "wait_on_rate_limit_notify": True,
            "retry_count": 5,  # retry 5 times
            "retry_delay": 5,  # seconds to wait for retry
        }
        cursor = tweepy.Cursor(self._twitter_api.followers_ids, **cursor_settings)
        page_index = 0
        for follower_ids_page in cursor.pages():
            page_index += 1
            print("fetching page {} of follower ids for user with id {}".format(page_index, user_id))
            follower_ids_list.extend(follower_ids_page)
            time.sleep(TwitterApiBinding._PAGE_FETCH_DELAY_SECONDS)
        return follower_ids_list

    def get_friend_ids(self, user_id):
        friend_ids_list = []
        cursor_settings = {
            "id": user_id,
            "monitor_rate_limit": True,
            "wait_on_rate_limit": True,
            "wait_on_rate_limit_notify": True,
            "retry_count": 5,  # retry 5 times
            "retry_delay": 5,  # seconds to wait for retry
        }
        cursor = tweepy.Cursor(self._twitter_api.friends_ids, **cursor_settings)
        page_index = 0
        try:
            for follower_ids_page in cursor.pages():
                page_index += 1
                friend_ids_list.extend(follower_ids_page)
                time.sleep(TwitterApiBinding._PAGE_FETCH_DELAY_SECONDS)
        except tweepy.TweepError:
            return friend_ids_list
        return friend_ids_list

    def search_tweets(self, query_dict, max_pages=10):
        print("searching tweets with query {}, fetching {} pages".format(query_dict, max_pages))
        cursor_settings = {
            "q": query_dict["query"],
            "lang": query_dict["lang"],
            "count": 100,
            "monitor_rate_limit": True,
            "wait_on_rate_limit": True,
            "wait_on_rate_limit_notify": True,
            "retry_count": 5,  # retry 5 times
            "retry_delay": 5,  # seconds to wait for retry
            "result_type": "recent"
        }
        cursor = tweepy.Cursor(self._twitter_api.search, **cursor_settings)
        tweets = []
        page_index = 0
        for page in cursor.pages(max_pages):
            page_index += 1
            print("fetched page " + str(page_index))
            tweets.extend(page)
        print("done - fetched all results for query " + str(query_dict))
        return tweets

    def fetch_tweets_by_user(self, user_id, count):
        try:
            return self._twitter_api.user_timeline(user_id=user_id, count=count)
        except tweepy.TweepError as err:
            if err.response.status_code == 401:
                print("status code 401 for user with ID " + str(user_id))
                return []
            if err.response.status_code == 404:
                print("status code 404 for user with ID " + str(user_id))
                return []
            else:
                print("Error, unable to recover. Status code: " + str(err.response.status_code))
                print(err)
                exit(1)


        # TODO: duplications, insconsitstencies with errors, etc. => needs rework
