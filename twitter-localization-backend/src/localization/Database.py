import pymongo

from src.util import context
from src.database.neo4j_binding import Neo4jBinding


class Database:

    _instance = None

    def __init__(self):
        self._host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
        self._database_connection = self._host_connection[context.get_config("influencers_db")]
        self.users_mongodb = self._database_connection[context.get_config("users_collection")]
        self.influencers_mongodb = self._database_connection[context.get_config("influencers_collection")]
        self.users_test_set_mongodb = self._database_connection[context.get_config("users_test_set_collection")]
        self.geonames_places_mongodb = self._database_connection[context.get_config("geonames_places_collection")]
        self.tweets_mongodb = self._database_connection[context.get_config("tweets_collection")]
        self.feature_cache = self._database_connection[context.get_config("feature_cache_collection")]
        self.neo4j = Neo4jBinding()

    @staticmethod
    def instance():
        if Database._instance is None:
            Database._instance = Database()
        return Database._instance

