import math

import pymongo

from src.cleanup.DuplicatesRemover import DuplicatesRemover
from src.crawler.UserManager import UserManager
from src.database.neo4j_binding import Neo4jBinding
from src.geonames.GeonamesApi import GeonamesApi
from src.geonames.GeonamesException import GeonamesException
from src.geonames.GeonamesRateLimitException import GeonamesRateLimitException
from src.geonames.OfflineDataInserter import OfflineDataInserter
from src.knowledgegraph.KnowledgeGraph import KnowledgeGraph
from src.localization.metamodels.FeatureCombination1 import FeatureCombination1
from src.localization.metamodels.FeatureCombination2 import FeatureCombination2
from src.localization.metamodels.FeatureCombination3 import FeatureCombination3
from src.localization.metamodels.FeatureCombination4 import FeatureCombination4
from src.localization.metamodels.FeatureCombination5 import FeatureCombination5
from src.localization.metamodels.SimpleSwissFriendRatio import SimpleSwissFriendRatio
from src.localization.metamodels.SimpleTweetInteractionBehavior import SimpleTweetInteractionBehavior
from src.model import constants
from src.twitter.TwitterApiBinding import TwitterApiBinding
from src.util import context
from src.localization.metamodels.SimpleInfluencerFollowedRatio import SimpleInfluencerFollowedRatio
from src.localization.metamodels.SimpleHashtagSimilarity import SimpleHashtagSimilarity
from src.localization.metamodels.SimpleSwissTweetInteraction import SimpleSwissTweetInteraction
from src.localization import LocalizationConstants
from src.testing.MetamodelTest import MetamodelTest
from src.localization import TrainValidateTestProvider
from src.localization.featureextractors.SwissFriendsRatio import SwissFriendsRatio
from src.localization.Database import Database
from src.localization.metamodels.SimpleSwissNamedPlaces import SimpleSwissNamedPlacesCount

def try_fetching_multiple_users(twitter_api_binding):
    user_ids = [239376971, 966142454, 9920562, 455049462, 42851245]
    bulk_users = twitter_api_binding.find_multiple_users(user_ids=user_ids)
    print()


def fix_outdated_crawl_status():
    host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
    database_connection = host_connection[context.get_config("influencers_db")]
    influencers_mongodb = database_connection[context.get_config("influencers_collection")]
    users_mongodb = database_connection[context.get_config("users_collection")]
    for u in users_mongodb.find({"followerIds": {"$exists": True}}):
        inf = influencers_mongodb.find_one({"id": u["id"]})
        inf["crawl_status"] = constants.CrawlStatus.FOLLOWER_IDS_COLLECTED
        influencers_mongodb.save(inf)


def fetch_influencer_follower_ids():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.fetch_influencer_follower_ids(perform_update=False)


def fetch_influencer_followes_to_db():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.fetch_influencer_followers_to_db()


def collect_test_users():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.collect_test_users()
    print()


def try_geonames_request():
    context.load_credentials()
    context.load_config()
    geonames = GeonamesApi()
    geonames.search("Bern, Schweiz")


def remove_duplicate_users_mongo():
    context.load_credentials()
    context.load_config()
    remover = DuplicatesRemover()
    remover.remove_duplicate_users()


def collect_test_users():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.collect_test_users()


def ex_test():
    try:
        raise GeonamesException(18)
    except GeonamesRateLimitException as ex:
        print(ex.is_daily())
    except GeonamesException as ex:
        print(ex)


def ch_users():
    context.load_credentials()
    context.load_config()
    host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
    database_connection = host_connection[context.get_config("influencers_db")]
    users_mongodb = database_connection[context.get_config("users_collection")]
    users_test_set_mongodb = database_connection[context.get_config("users_test_set_collection")]
    geonames_places_mongodb = database_connection[context.get_config("geonames_places_collection")]
    swiss_places = geonames_places_mongodb.find({"country_code": "CH"})
    swiss_place_ids = [sp["geonames_id"] for sp in swiss_places]
    swiss_users = [su for su in users_test_set_mongodb.find({"user_place.geonames_id": {"$in": swiss_place_ids}})]
    num_users_total = users_test_set_mongodb.find({}).count()
    swiss_percentage = math.floor(100 * len(swiss_users) / num_users_total)
    print("{}% ({}/{}) of users are swiss".format(swiss_percentage, len(swiss_users), num_users_total))
    swiss_user_ids = [str(su["_id"]) for su in swiss_users]
    swiss_sheep = [su for su in users_mongodb.find({"_id": {"$in": swiss_user_ids}})]
    swiss_available_percentage = math.floor(100 * len(swiss_sheep) / len(swiss_users))
    print("{}% ({}/{}) of swiss test users are in DB".format(swiss_available_percentage, len(swiss_sheep),
                                                             len(swiss_users)))


def not_in_list():
    context.load_credentials()
    context.load_config()
    host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
    database_connection = host_connection[context.get_config("influencers_db")]
    users_mongodb = database_connection[context.get_config("users_collection")]

    print("getting follower IDs")
    my_influencer = users_mongodb.find_one({"id": 239376971})
    follower_ids_list = my_influencer["followerIds"]

    print("getting existing users within follower ids")
    existing_users_cursor = users_mongodb.find({"id": {"$in": follower_ids_list}}, {"_id": 1, "id": 1})

    print("extracting existing IDs into set")
    existing_users_list = []
    for user in existing_users_cursor:
        existing_users_list.append(user["id"])
    existing_ids_set = set(existing_users_list)

    print("converting follower_ids_list to set")
    follower_ids_set = set(follower_ids_list)

    print("calculating set difference")
    new_ids_set = follower_ids_set.difference(existing_ids_set)
    print()


def add_local_geonames():
    context.load_credentials()
    context.load_config()
    odi = OfflineDataInserter()
    odi.insert_from_file("CH.txt", "Switzerland", "CH", "2658434")
    # odi.convert_strings_to_int()


def add_users():
    context.load_credentials()
    context.load_config()
    graph = KnowledgeGraph()
    graph.insert_static_users()


def add_influencer_follows_relations():
    context.load_credentials()
    context.load_config()
    graph = KnowledgeGraph()
    graph.add_follows_rel_for_influencers()


def add_local_geonames_to_users():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.add_local_swiss_geonames_info()


def add_is_swiss_attribute():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.set_is_swiss_property()


def try_fetching_tweets():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    id = 239376971
    count = 100
    results = twitter_api_binding.fetch_tweets_by_user(id, count)
    print()


def fetch_tweets_for_influencers():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.collect_tweets_for_influencers()


def fetch_tweets_for_test_users():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.collect_tweets_for_test_users(ch_only=False)


def fix_stupid_mistake():
    context.load_credentials()
    context.load_config()
    host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
    database_connection = host_connection[context.get_config("influencers_db")]
    users_mongodb = database_connection[context.get_config("users_collection")]
    users_test_set = database_connection[context.get_config("users_test_set_collection")]

    test_users_cursor = users_test_set.find({"is_swiss": True})
    num_test_users = test_users_cursor.count()
    print("found {} CH users in test set".format(num_test_users))

    i = 0
    for test_user in test_users_cursor:
        i += 1
        print("checking test user {}/{}".format(i, num_test_users))
        result = users_mongodb.find_one({"id": test_user["id"]})
        test_user["exists_in_main_collection"] = result is not None
        users_test_set.save(test_user)

    num_issues = users_test_set.find({"exists_in_main_collection": True}).count()
    print("found {} possible issues".format(num_issues))


def try_adding_localizations():
    context.load_credentials()
    context.load_config()
    neo = Neo4jBinding()
    model = SimpleInfluencerFollowedRatio()
    neo.add_localization_relation(model, 1745505896, 2658434)


def remove_localizations():
    context.load_credentials()
    context.load_config()
    neo = Neo4jBinding()
    neo.remove_all_localizations()


def collect_tweets_for_influencers():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.collect_tweets_for_influencers()

def collect_tweets_for_tvt_users():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.collect_tweets_for_test_users()

def foo():
    context.load_credentials()
    context.load_config()
    graph = KnowledgeGraph()
    loc_bin = graph.fetch_localizations_for_user(1101807458887090176, "simple_influencer_followed_ratio_1562915212981", binary_result=True)
    loc_id = graph.fetch_localizations_for_user(1101807458887090176, "simple_influencer_followed_ratio_1562915212981", binary_result=False)
    print()


def export_test_set():
    context.load_credentials()
    context.load_config()
    filename = "large-training-1000-100-100"
    train, validate, test = TrainValidateTestProvider.get_data()
    TrainValidateTestProvider.export_sets_to_file(filename)


def try_simple_hashtag_sim():
    context.load_credentials()
    context.load_config()
    metamodel = SimpleHashtagSimilarity()
    train_scores = metamodel.build()
    print(train_scores)


def try_swiss_friend_ratio():
    context.load_credentials()
    context.load_config()
    user = Database.instance().users_test_set_mongodb.find_one({"id": 123362849})
    sf = SwissFriendsRatio()
    ratio = sf.extract_for(user)
    print("ratio = %s" % ratio)


def fetch_friend_ids_for_tvt_set():
    context.load_credentials()
    context.load_config()
    twitter_api_binding = TwitterApiBinding()
    user_manager = UserManager(twitter_api_binding)
    user_manager.fetch_friend_ids_for_tvt_set("large-training-1000-100-100")


def try_model():
    context.load_credentials()
    context.load_config()
    metamodel = FeatureCombination4(use_cache=True, allow_cache_updates=True)
    train_scores = metamodel.build()
    print(train_scores)


def run_evaluation():
    context.load_credentials()
    context.load_config()
    mmodel = FeatureCombination5()
    test = MetamodelTest(mmodel)
    score = test.test(remove_graph_traces=False)
    print(score)


if __name__ == "__main__":
    run_evaluation()
