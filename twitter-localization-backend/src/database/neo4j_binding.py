from neo4j import GraphDatabase
from src.model import User
from src.util import context
from src.localization import LocalizationConstants


class Neo4jBinding:
    """
    Wrapper for connection to and transactions with Neo4j graph database
    """

    def __init__(self):
        pass

    def _run_transaction(self, method, query):
        pass

    @staticmethod
    def _execute_query(tx, query):
        pass

    # ======== Statistics ========

    # TODO add optional min confidence wherever useful

    def count_all_users(self):
        pass

    def count_all_swiss_users(self):
        pass

    def count_standard_swiss_users(self):
        pass

    def count_swiss_influencers(self):
        pass

    def count_all_tweets(self):
        pass

    def count_swiss_tweets(self):
        pass

    def delete_all_relationships(self):
        pass

    # ======== Get Users and Tweets ========
    def get_all_users(self):
        pass

    def get_user_by_screen_name(self, screen_name):
        pass

    def get_user_by_id(self, twitter_id):
        pass

    def user_exists(self, screen_name):
        pass

    # ======== Insert Users and Tweets ========
    def insert_user(self, user):
        pass

    def add_follows_relationship(self, follower_id, followed_user_id):
        pass

    def add_localization_relation(self, metamodel, twitter_user_id, geonames_id, confidence, sequence_number=0,
                                  type="final"):
        pass

    def remove_localizations_by_model(self, model_id):
        pass

    def remove_localizations_by_model_instance(self, model_instance_id, keep_final=False):
        pass

    def remove_all_localizations(self):
        pass

    def remove_non_final_localizations(self):
        pass

    def fetch_localizations_for_user(self, twitter_user_id, model_instance_id, localization_type):
        pass

    def fetch_localizations_by_model_instance(self, model_instance_id, localization_type):
        pass

    # ======== Helpers ===========
    def _parse_dict_for_query_string(self, dictionary):
        pass
