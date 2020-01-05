import pymongo

from src.util import context


class DuplicatesRemover:
    def __init__(self):
        self._host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
        self._database_connection = self._host_connection[context.get_config("influencers_db")]
        self._influencers_mongodb = self._database_connection[context.get_config("influencers_collection")]
        self._users_mongodb = self._database_connection[context.get_config("users_collection")]
        self._users_test_set_mongodb = self._database_connection[context.get_config("users_test_set_collection")]

    def remove_duplicate_users(self):
        """
        Identifies duplicate entries on the "id" field (Twitter User ID) for documents in the users_collection. Removes
        all but one of the entries found for each id, selection is arbitrary.
        :return: None
        """
        cursor = self._users_mongodb.aggregate([
            {"$group": {"_id": "$id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ])
        for duplicate_set in cursor:
            print("removing duplicates for Twitter user ID " + str(duplicate_set["_id"]))
            duplicates = self._users_mongodb.find({"id": duplicate_set["_id"]}, {"_id": 1, "id": 1})
            duplicate_object_ids = [duplicate["_id"] for duplicate in duplicates]
            print("-> {} documents found, removing last {}".format(
                len(duplicate_object_ids),
                len(duplicate_object_ids)-1))
            self._users_mongodb.remove({"_id": {"$in": duplicate_object_ids[1:]}})
        print("done removing duplicate users")
