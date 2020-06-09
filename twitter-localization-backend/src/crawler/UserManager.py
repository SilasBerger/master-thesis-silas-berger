import json
import math
import os
import time

import pymongo
from tqdm import tqdm

from src.database.neo4j_binding import Neo4jBinding
from src.geonames.GeonamesApi import GeonamesApi
from src.geonames.GeonamesException import GeonamesException
from src.geonames.GeonamesLocalDatabase import GeonamesLocalDatabase
from src.geonames.GeonamesRateLimitException import GeonamesRateLimitException
from src.model import constants
from src.util import collections
from src.util import context, timing, paths
from src.knowledgegraph.KnowledgeGraph import KnowledgeGraph


class UserManager:
    """
    Handles the synchronization of Twitter user objects among the Twitter API, MongoDB, and the graph
    """

    _CRAWL_DELAY_SECONDS = 0.2

    def __init__(self, twitter_api_binding):
        self.neo4j = Neo4jBinding()
        self._twitter = twitter_api_binding
        self._connect()
        self._graph = KnowledgeGraph()

    def _connect(self):
        self._host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
        self._database_connection = self._host_connection[context.get_config("influencers_db")]
        self._influencers_mongodb = self._database_connection[context.get_config("influencers_collection")]
        self._users_mongodb = self._database_connection[context.get_config("users_collection")]
        self._users_test_set_mongodb = self._database_connection[context.get_config("users_test_set_collection")]
        self._geonames_places_mongodb = self._database_connection[context.get_config("geonames_places_collection")]
        self._tweets_mongodb = self._database_connection[context.get_config("tweets_collection")]
        self._geonames_api = GeonamesApi()
        self._geonames_local_api = GeonamesLocalDatabase()

    def update_influencers_in_database(self, update_existing_users=False):
        """
        Iterate through influencer list, fetch Twitter user for every influencer based on screen name, reduce
        user to predefined set of field and set type=influencer ("normalize"); add user to users collection in DB,
        or update existing user.

        :param update_existing_users: if False, users influencers will be skipped if they already exist in the users
                collection. If True, existing users will be updated with the latest information from the Twitter API.
        :return: None
        """
        print("Updating influencers in database")
        progress = 0
        influencers_cursor = self._influencers_mongodb.find()
        for influencer_entry in influencers_cursor:
            if (not update_existing_users) and self._user_exists_in_db(influencer_entry):
                continue
            influencer_user = self._twitter.find_user(influencer_entry["screen_name"])
            if influencer_user is None:
                self._handle_user_not_found(influencer_entry)
                continue
            self._update_user_in_mongo(influencer_user, influencer_entry["category"])
            progress += 1
            self._set_crawl_status(influencer_entry, constants.CrawlStatus.COLLECTED.value)
            print("{} users fetched/updated".format(progress))
            time.sleep(UserManager._CRAWL_DELAY_SECONDS)
        print("done")

    def sync_graph_influencers(self):
        """
        Filters database for users marked as influencers and adds them to the graph, or updates them if they
        aready exist in the graph

        :return: None
        """
        influencers_cursor = self._users_mongodb.find({"type": constants.UserType.INFLUENCER.value})
        for influencer_user in influencers_cursor:
            if self.neo4j.user_exists(influencer_user["screen_name"]):
                # TODO handle updating existing users
                continue
            n_user = self._normalize_user_for_graph(influencer_user)
            self._set_crawl_status(influencer_user, constants.CrawlStatus.IN_GRAPH.value)
            self.neo4j.insert_user(n_user)

    def fetch_influencer_follower_ids(self, perform_update=False):
        """
        Fetches follower IDs from Twitter API for each follower in the DB, adds them as ab array in the respective
        user document in the DB, as field `follower_ids`. If not `perform_update`, skips users where this field
        already exists. Else, overwrites this field.

        :param perform_update: if False, skips users where the `followerIds` field already exists. If True, includes
                               these users as well, and replaces the field with the latest data
        :return: None
        """
        print("fetching follower ids for influencers")
        influencers_cursor = self._users_mongodb.find({"type": constants.UserType.INFLUENCER.value})
        for influencer_user in influencers_cursor:
            if (not perform_update) and ("followerIds" in influencer_user):
                # not performing updates + user already has influencer field: skip
                print("skipping user with id", influencer_user["id"], "(not updating)")
                continue
            print("fetching followerIds for user with id", influencer_user["id"])
            follower_ids = self._twitter.get_follower_ids(influencer_user["id"])
            influencer_user["followerIds"] = follower_ids
            self._set_crawl_status(self._influencers_mongodb.find_one({"id": influencer_user["id"]}),
                                   constants.CrawlStatus.FOLLOWER_IDS_COLLECTED.value)
            self._users_mongodb.save(influencer_user)

    def fetch_influencer_followers_to_db(self, handle_no_users_found=False):
        """
        Iterates through each influencer's follower IDs, fetches each user from Twitter API and adds each user to
        DB, skipping users that already exist.
        :param handle_no_users_found:   whether the function should manually iterate over user IDs in a chunk, if API
                                        returned 404 or that chunk. Generally not advised to do so, since API only
                                        returns user objects for users that were found. If entire chunks fail, this
                                        is likely due to them only being the remaining users, that weren't found in
                                        a previous use of this function. Defaults to False.
        :return: None
        """
        print(timing.get_timestamp() + ":", "started fetching influencer followers to DB, getting current IDs")
        influencers_cursor = self._users_mongodb.find({"type": constants.UserType.INFLUENCER.value},
                                                      no_cursor_timeout=True)

        for influencer_user in influencers_cursor:
            new_ids = self._fetch_uncrawled_follower_ids_for_influencer(influencer_user)
            chunks = collections.split_list_into_chunks(new_ids, chunk_size=100)
            num_chunks = len(chunks)
            print("{}: created {} chunks".format(timing.get_timestamp(), num_chunks))
            for chunk_id, chunk in enumerate(chunks):
                print("{}: fetching bulk {}/{}".format(timing.get_timestamp(), chunk_id, num_chunks))
                bulk = self._twitter.find_multiple_users(chunk)
                if bulk is None:
                    print("{}: bulk returned 404, skipping".format(timing.get_timestamp()))
                    continue
                print("{}: inserting bulk".format(timing.get_timestamp()))
                for user in bulk:
                    n_user = self._normalize_user_for_mongo(user)
                    self._users_mongodb.save(n_user)
            time.sleep(UserManager._CRAWL_DELAY_SECONDS)
        influencers_cursor.close()

    def _fetch_uncrawled_follower_ids_for_influencer(self, influencer_user):
        print("{}: fetching uncrawled follower IDs for influencer {} ({})".format(timing.get_timestamp(),
                                                                                  influencer_user["screen_name"],
                                                                                  influencer_user["id"]))
        follower_ids_list = influencer_user["followerIds"]
        existing_users_cursor = self._users_mongodb.find({"id": {"$in": follower_ids_list}}, {"_id": 1, "id": 1})

        existing_users_list = []
        for user in existing_users_cursor:
            existing_users_list.append(user["id"])
        existing_ids_set = set(existing_users_list)

        follower_ids_set = set(follower_ids_list)
        return list(follower_ids_set.difference(existing_ids_set))

    def add_local_swiss_geonames_info(self):
        """
        Iterates through all users in the DB, adds GeoNames ID if user's user_place doesn't yet have
        a GeoNames ID, and if user's location field yields a match in GeonamesLocalDatabase#search. Such
        a match is found if either the entire location field or one of its individual words exactly matches
        a GeoNames place's name or alternate name, for GeoNames places in the local DB. If this function adds a
        "geonames_id" field to the user's "user_place", it also adds a field "is_local_geonames_match: true",
        to indicate that this match was achieved locally, rather than through the GeoNames API.
        :return: None
        """
        print("started adding local GeoNames information to users")
        i = 0
        users_cursor = self._users_mongodb.find({
            "user_place.tried_local_match": {"$exists": False},
            "user_place.geonames_id": {"$exists": False},
            "user_place.location": {"$ne": ""}
        }, no_cursor_timeout=True)
        num_users = users_cursor.count()
        for user in users_cursor:
            i += 1
            print("looking up user {}/{}".format(i, num_users))
            user["user_place"]["tried_local_match"] = True
            if "geonames_id" in user["user_place"]:
                # user already has a geonames ID
                continue
            match = self._geonames_local_api.search(user["user_place"]["location"], first_match=True)
            if match is not None:
                user["user_place"]["geonames_id"] = match["geonames_id"]
                user["user_place"]["is_local_geonames_match"] = True
                print("user '{}' with location field '{}' matched to place {}, {}".format(
                    user["screen_name"],
                    user["user_place"]["location"],
                    match["name"],
                    match["state_code"]))
            else:
                print("no match for location field {}".format(user["user_place"]["location"]))
            self._users_mongodb.save(user)
        users_cursor.close()
        print("done adding local GeoNames information to users")


    def collect_test_users(self):
        queries_file_path = os.path.join(paths.get_project_root(), "configs/tweet_queries.json")
        with open(queries_file_path, "r", encoding="utf-8") as infile:
            queries = json.load(infile)
        for query in queries:
            if query.get("completed", False):
                # skip query if it has already been completed
                print("{} UserManager: skipping completed query {}".format(timing.get_timestamp(), query))
                continue
            print("{} UserManager: fetching tweets for query {}".format(timing.get_timestamp(), query))
            tweets = self._twitter.search_tweets(query, max_pages=10)
            print("{} UserManager: tweets fetched for query {}, collecting users".format(timing.get_timestamp(), query))
            for tweet in tweets:
                normalized_user = self._normalize_user_for_mongo(tweet.user)
                if not self._is_viable_test_user(normalized_user, query):
                    # exists in DB or test set, or query string found in user's name/description - skip
                    continue
                success, error = self._add_geonames_information(normalized_user)
                if success:
                    # geonames information added, can add user to database
                    self._users_test_set_mongodb.save(normalized_user)
                elif error is None:
                    # no geonames exception, but invalid user location field - skip
                    continue
                elif (type(error) is GeonamesRateLimitException) and (not error.is_hourly()):
                    print(timing.get_timestamp() + " Daily or weekly Geonames rate limit reached, shutting down")
                    print(error)
                    exit(0)
                else:
                    print(timing.get_timestamp() + " UserManager: Geonames exception occurred, unable to recover")
                    print(error)
            query["completed"] = True
            with open(queries_file_path, "w", encoding="utf-8") as outfile:
                json.dump(queries, outfile, ensure_ascii=False, indent=4)
            time.sleep(UserManager._CRAWL_DELAY_SECONDS)

    def set_is_swiss_property(self):
        print("UserManager: setting is_swiss attribute for users collection")
        users_cursor = self._users_mongodb.find({"user_place.geonames_id": {"$exists": True},
                                                 "is_swiss": {"$exists": False}})
        self._set_is_swiss_for_cursor(users_cursor, self._users_mongodb)
        print("UserManager: setting is_swiss attribute for users_test_set collection")
        users_test_set_cursor = self._users_test_set_mongodb.find({"user_place.geonames_id": {"$exists": True},
                                                                   "is_swiss": {"$exists": False}})
        self._set_is_swiss_for_cursor(users_test_set_cursor, self._users_test_set_mongodb)

    # TODO: move this to a new module
    def collect_tweets_for_influencers(self):
        print("started fetching tweets for influencers")
        influencer_cursor = self._users_mongodb.find({
            "type": "influencer",
            "$or": [
                {"tweets_fetched": False},
                {"tweets_fetched": {"$exists": False}}
            ]
        })
        self._collect_tweets_for_users(influencer_cursor, self._users_mongodb)

    # TODO: move this to a new module
    def collect_tweets_for_test_users(self, ch_only=False):
        print("started fetching tweets for test users")
        if ch_only:
            user_cursor = self._users_test_set_mongodb.find({
                "is_swiss": True,
                "$or": [
                    {"tweets_fetched": False},
                    {"tweets_fetched": {"$exists": False}}
                ]
            })
        else:
            user_cursor = self._users_test_set_mongodb.find({
                "$or": [
                    {"tweets_fetched": False},
                    {"tweets_fetched": {"$exists": False}}
                ]
            })
        self._collect_tweets_for_users(user_cursor, self._users_test_set_mongodb, skip_if_tweets_found=True)

    def ensure_fetch_twitter_user(self, screen_name):
        existing_user = self._users_mongodb.find_one({"screen_name": screen_name})
        if existing_user is None:
            existing_user = self._users_test_set_mongodb.find_one({"screen_name": screen_name})
        if existing_user is not None:
            if not self.neo4j.user_exists(existing_user["screen_name"]):
                self._graph.insert_user(existing_user)
            return existing_user
        print(timing.get_timestamp() + ": @{} not found locally - querying Twitter API".format(screen_name))
        new_user = self._twitter.find_user(screen_name)
        if new_user is None:
            # User not found in Twitter API.
            return None
        print(timing.get_timestamp() + ": @{} found on Twitter - fetching associated data".format(screen_name))
        new_user = self._normalize_user_for_mongo(new_user)
        new_user["friend_ids"] = self._twitter.get_friend_ids(id)
        self._users_mongodb.save(new_user)
        user_cursor = self._users_mongodb.find({"id": new_user["id"]})
        self._collect_tweets_for_users(user_cursor, self._users_mongodb, skip_if_tweets_found=True)
        return new_user

    def fetch_friend_ids_for_tvt_set(self, fname):
        with open(paths.convert_project_relative_path(os.path.join("configs", str(fname) + ".json")), "r") as infile:
            data = json.load(infile)
            ids = set(data["train"]).union(set(data["validate"])).union(set(data["test"]))
            for id in tqdm(ids):
                existing_user = self._users_test_set_mongodb.find_one({"id": id})
                if (existing_user is None) or ("friend_ids" in existing_user):
                    continue  # user doesn't exist or already has friend ids
                friend_ids = self._twitter.get_friend_ids(id)
                existing_user["friend_ids"] = friend_ids
                self._users_test_set_mongodb.save(existing_user)

    def _collect_tweets_for_users(self, cursor, user_collection, skip_if_tweets_found=False):
        total_users = cursor.count()
        index = 0
        for user in cursor:
            index += 1
            n_tweets = []
            if user.get("tweets_fetched", False):
                # already fetched tweets for that user, skip
                continue
            if skip_if_tweets_found:
                if self._tweets_mongodb.find({"author_id": user["id"]}).count() > 0:
                    user["tweets_fetched"] = True
                    user_collection.save(user)
                    continue
            print(timing.get_timestamp() + ": fetched tweets for @{} (user {}/{})".format(user["screen_name"],
                                                                                        index,
                                                                                        total_users))
            tweets = self._twitter.fetch_tweets_by_user(user["id"], 100)
            for tweet in tweets:
                n_tweets.append(self._normalize_tweet_for_db(tweet))
            if len(n_tweets) > 0:
                self._tweets_mongodb.insert_many(n_tweets)
            user["tweets_fetched"] = True
            user_collection.save(user)

    def _normalize_tweet_for_db(self, tweet):
        n_tweet = {
            "status_id": tweet.id,
            "text": tweet.text,
            "author_id": tweet.author.id,
            "created_at": tweet.created_at,
            "lang": tweet.lang,
            "place": tweet.place,
            "coordinates": tweet.coordinates,
            "geo": tweet.geo,
            "entities": tweet.entities,
            "in_reply_to_status_id": tweet.in_reply_to_status_id,
            "in_reply_to_user_id": tweet.in_reply_to_user_id,
        }
        if hasattr(tweet, "retweeted_status"):
            n_tweet["retweeted_status_id"] = tweet.retweeted_status.id
            n_tweet["retweeted_status_author_id"] = tweet.retweeted_status.author.id
        if hasattr(tweet, "place") and (tweet.place is not None):
            n_tweet["place"] = {
                "full_name": tweet.place.full_name,
                "country_code": tweet.place.country_code,
                "country": tweet.place.country
            }
        return n_tweet

    def _set_is_swiss_for_cursor(self, cursor, users_collection):
        num_users = cursor.count()
        i = 0
        for user in cursor:
            i += 1
            print("setting is_swiss for user {}/{}".format(i, num_users))
            geo_place = self._geonames_places_mongodb.find_one({"geonames_id": user["user_place"]["geonames_id"]})
            if geo_place is None:
                print("error: geonames_id {} not found for user with id {}".format(user["user_place"]["geonames_id"],
                                                                                   user["id"]))
                continue
            if geo_place["country_code"] == "CH":
                user["is_swiss"] = True
            else:
                user["is_swiss"] = False
            users_collection.save(user)


    def _is_viable_test_user(self, user, query):
        """
        Determines whether this user is viable/interesting as part of the test set. Rejects user if already in
        test set. Does not check validity or availability of other information, such as a valid user location field.
        This function may change in the future.
        :param user:    user to be tested
        :param query:   query set ({query, lang}) that resulted in finding a tweet by this user
        :return:        True if the user is viable, False else
        """
        if self._user_exists_in_test_set(user):
            return False
        return True

    def _add_geonames_information(self, user):
        """
        Checks user's "location" field against the Geonames full-text search API, if field exists. If a place is found,
        the result object is normalized and stored on MongoDB if it doesn't already exist, and the Geonames place's
        geonames_id is stored in the user object's "user_place" object. If the user already has a "geonames_id" field,
        ensures that the corresponding Geonames place is in the geonames_places_collection.
        :param user: Twitter user to add Geonames information for, must have a "user_place" field
        :return:    (True, None) if Geonames location was added
                    (False, None) in case of invalid location field
                    (False, GeonamesException) in case of an exception that can't be handled by this function
        """
        assert "user_place" in user
        user_location = user["user_place"]["location"]
        if user_location is None or user_location == "":
            # user does not specify a location, can't fetch geonames information, skip
            return False, None
        if ("geonames_id" in user["user_place"]) and self._geonames_place_exists(user["user_place"]["geonames_id"]):
            # user already has a valid geonames_id, done
            return True, None
        try:
            print("UserManager: fetching Geonames info for user {}".format(user["screen_name"]))
            geonames_info = self._parse_geonames_information(self._geonames_api.search(user_location))
            if geonames_info is None:
                # no result from Geonames, invalid location field
                return False, None
            user["user_place"]["geonames_id"] = geonames_info["geonames_id"]
            self._store_geonames_place(geonames_info)
            return True, None
        except GeonamesRateLimitException as ex:
            if not ex.is_hourly:
                return False, ex
            sleep_duration = timing.get_seconds_to_start_of_next_hour(60)
            print("{} UserManager: awaiting Geonames hourly limit, {} minutes"
                  .format(timing.get_timestamp(), math.ceil(sleep_duration / 60)))
            time.sleep(sleep_duration)
            return self._add_geonames_information(user)
        except GeonamesException as ex:
            return False, ex

    def _geonames_place_exists(self, geonamesId):
        return self._geonames_places_mongodb.find_one({"geonames_id": geonamesId}) is not None

    def _parse_geonames_information(self, geonames_result):
        if geonames_result is None:
            return None
        required_fields = ["geonameId", "countryId", "toponymName", "population", "adminName1",
                           "adminCode1", "countryName", "countryCode", "lng", "lat"]
        for rf in required_fields:
            if (rf not in geonames_result) or (geonames_result[rf] is None) or (geonames_result[rf] == ""):
                print("UserManager: rejected geonames result {}, missing/invalid field {}".format(geonames_result, rf))
                return None
        return {
            "geonames_id": geonames_result["geonameId"],
            "country_id": geonames_result["countryId"],
            "name": geonames_result["toponymName"],
            "population": geonames_result["population"],
            "state": geonames_result["adminName1"],
            "state_code": geonames_result["adminCode1"],
            "country_name": geonames_result["countryName"],
            "country_code": geonames_result["countryCode"],
            "lng": geonames_result["lng"],
            "lat": geonames_result["lat"]
        }

    def _store_geonames_place(self, place):
        if not self._geonames_place_exists(place["geonames_id"]):
            self._geonames_places_mongodb.save(place)

    def _handle_user_not_found(self, influencer_entry):
        print("user '{}' suspended or not found, skipping".format(influencer_entry["screen_name"]))
        influencer_entry["crawl_status"] = constants.CrawlStatus.NOT_FOUND.value
        self._influencers_mongodb.save(influencer_entry)

    def _update_user_in_mongo(self, user, influencer_category):
        n_user = UserManager._normalize_user_for_mongo(user, influencer_category)
        existing_user = self._users_mongodb.find_one({"screen_name": n_user["screen_name"]})
        if existing_user is not None:
            # user with that screen name already exists in the collection, preserve static information
            n_user["_id"] = existing_user["_id"]
        self._users_mongodb.save(n_user)

    def _user_exists_in_db(self, user):
        return self._users_mongodb.find_one({"screen_name": user["screen_name"]}) is not None

    def _user_id_exists_in_db(self, user_id):
        return self._users_mongodb.find_one({"id": user_id}) is not None

    def _user_exists_in_test_set(self, user):
        return self._users_test_set_mongodb.find_one({"id": user["id"]}) is not None

    @staticmethod
    def _normalize_user_for_mongo(user, influencer_category=None):
        """
        Reduces, adds and aggregates fields to the schema used on the DB, for a user fetched from Twitter API.

        :param user: Twitter user from Twitter API
        :param influencer_category: user's influencer category, treated as standard user, defaults to None
        :return: normalized user
        """
        normalized_user = {}
        for field in context.get_config("collect_user_fields"):
            normalized_user[field] = getattr(user, field)
        normalized_user["user_place"] = {
            "time_zone": user.time_zone,
            "utc_offset": user.utc_offset,
            "location": user.location
        }
        normalized_user["type"] = constants.UserType.STANDARD.value
        if influencer_category is not None:
            normalized_user["type"] = constants.UserType.INFLUENCER.value
            normalized_user["influencer_category"] = influencer_category
        return normalized_user

    @staticmethod
    def _normalize_user_for_graph(user):
        normalized_user = {}
        for field in context.get_config("user_fields_in_graph"):
            normalized_user[field] = user[field]
        normalized_user["influencer_category"] = user["influencer_category"]
        return normalized_user

    def _set_crawl_status(self, influencer_entry, crawl_status):
        influencer_entry["crawl_status"] = crawl_status
        self._influencers_mongodb.save(influencer_entry)

    def _filter_ids_existing_in_db(self, follower_ids):
        return [f_id for f_id in follower_ids if self._users_mongodb.find_one({"id": f_id}) is not None]

    def _get_next_ids_chunk(self, ids_cursor, chunk_size, include_existing_ids=False):
        pass

    def _init_countries_list(self):
        with open(os.path.join(paths.get_project_root(), "data/countries.txt")) as infile:
            countries = infile.readlines()
        self._countries_list = [line.lower().strip() for line in countries]

    def _manually_iterate_failed_chunk(self, chunk):
        bulk = []
        for user_id in chunk:
            user = self._twitter.find_user(user_id)
            if user is None:
                print("user with ID {} not found or suspended, skipping".format(user_id))
                continue
            else:
                bulk.append(user)
                print("manually added user with id {}".format(user_id))
        return bulk
