import pymongo

from src.database.neo4j_binding import Neo4jBinding
from src.knowledgegraph.Layers import Layers
from src.util import context, timing
from src.localization import LocalizationConstants


class KnowledgeGraph:

    def __init__(self):
        self._neo4j = Neo4jBinding()
        self._host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
        self._database_connection = self._host_connection[context.get_config("influencers_db")]
        self._influencers_mongodb = self._database_connection[context.get_config("influencers_collection")]
        self._users_mongodb = self._database_connection[context.get_config("users_collection")]
        self._users_test_set_mongodb = self._database_connection[context.get_config("users_test_set_collection")]
        self._geonames_places_mongodb = self._database_connection[context.get_config("geonames_places_collection")]

    def cleanup(self, remove_static_data=False):
        """
        Return graph to its initial state by removing all static and/or dynamic nodes and edges.
        :param remove_static_data: also remove static nodes and edges (i.e. clear graph), defaults to False
        :return: None
        """
        pass

    def prepare(self):
        """
        Insert all static data into the graph (influencers, followers, etc.). Does not produce duplicates. Does not
        remove any nodes or edges.
        :return: None
        """
        pass

    def reset(self):
        """
        Clear entire graph, insert all static data (influencers, followers, etc.).
        :return: None
        """
        pass

    def insert_localization(self, model, classifier, user, decision, confidence):
        """
        Insert a new localization into the graph. Create a new "localization" node with attribute "decision". Create
        a new edge from user to localization node, with attributes "model_id", "model_instance_id", "classifier_id",
        "classifier_instance_id", and "confidence".
        :param model:       reference to the model that created this localization
        :param classifier:  reference to the classifier used by the model to create this localization. If None,
                            classification is considered the model's meta-decision. Only one meta-decision can exist
                            per model instance. Overwrites existing meta-decision in graph.
        :param decision:    the predicted class: either True/False for swiss/non-swiss, or a swiss canton
        :param confidence:  the confidence for this localization, [0, 1]
        :return:            None
        """
        # TODO maybe add a notion of "epoch"? Also for master decisions. Allows metamodels to learn from each other, but
        # not in the same epoch, so they don't disturb each other (i.e. execution order doesn't matter)
        pass

    def fetch_localizations_for_user(self, twitter_user_id, model_instance_id, binary_result=False):
        """
        Gets the final localization for a given Twitter user and model instance. By default, the result
        is the GeoNames ID of the exact place (i.e. not just the country) where this user was localized to by the model
        instance's final decision. Optionally, this result can be converted into True (= swiss) or False (= not swiss)
        :param twitter_user_id:     Twitter ID of the user for which to get the localization, int
        :param model_instance_id:   ID of the model instance to consider, string
        :param binary_result:       if True, the result is given as True (= swiss) or False (not Swiss), instead
                                    of as a GeoNames ID
        :return:                    GeoNames ID (int) or True/False
        """
        result = self._neo4j.fetch_localizations_for_user(twitter_user_id,
                                                          model_instance_id,
                                                          LocalizationConstants.FINAL)
        # TODO maybe guard against multiple records (single() triggers warning) or no records (single() returns None)
        record = result.single()
        loc_node = record[2]
        # TODO maybe guard against loc_node.get(..) == None
        if binary_result:
            return loc_node.get("country_id") == LocalizationConstants.GEOID_SWITZERLAND
        return loc_node.get("geonames_id")

    def fetch_localization_results_for_model(self, model_instance_id):
        """
        Gets the final localization for a given Twitter user and model instance. By default, the result
        is the GeoNames ID of the exact place (i.e. not just the country) where this user was localized to by the model
        instance's final decision. Optionally, this result can be converted into True (= swiss) or False (= not swiss)
        :param model_instance_id:   ID of the model instance to consider, string

        :return:                    GeoNames ID (int) or True/False
        """
        result = self._neo4j.fetch_localizations_by_model_instance(model_instance_id, LocalizationConstants.FINAL)
        # TODO maybe guard against multiple records (single() triggers warning) or no records (single() returns None)
        record = result.single()
        user_id = record[0].get("twitter_id")
        confidence = record[1].get("confidence")
        located_swiss = (record[2].get("country_id") == LocalizationConstants.GEOID_SWITZERLAND)
        return user_id, confidence, located_swiss

    def fetch_final_decision_for_user(self, twitter_user_id, model_instance_id):
        result = self._neo4j.fetch_localizations_for_user(twitter_user_id,
                                                          model_instance_id,
                                                          LocalizationConstants.FINAL)
        record = result.single()
        edge = record[1]
        loc_node = record[2]
        confidence = edge.get("confidence")
        localized_swiss = (loc_node.get("country_id") == LocalizationConstants.GEOID_SWITZERLAND)
        return localized_swiss, confidence


    def insert_static_users(self):
        print(timing.get_timestamp() + ": KnowledgeGraph: fetching users to insert")
        user_cursor = self._users_mongodb.find({"$or": [{"in_graph": False}, {"in_graph": {"$exists": False}}]})
        total_user_count = user_cursor.count()
        print(timing.get_timestamp() + ": KnowledgeGraph: inserting {} static users".format(total_user_count))
        count = 1
        for user in user_cursor:
            self._neo4j.insert_user(KnowledgeGraph._normalize_user_for_graph(user, Layers.STATIC))
            user["in_graph"] = True
            self._users_mongodb.save(user)
            count += 1
            if (count % 100) == 0:
                print(timing.get_timestamp() + ": KnowledgeGraph: inserted user {}/{}".format(count, total_user_count))
        print(timing.get_timestamp() + ": KnowledgeGraph: DONE inserting static users")

    def add_follows_rel_for_influencers(self):
        print(timing.get_timestamp() + ": KnowledgeGraph: fetching influencers")
        influencer_cursor = self._users_mongodb.find({"type": "influencer",
                                                      "$or": [
                                                          {"f_rel_added": False}, {"f_rel_added": {"$exists": False}}
                                                      ]})
        total_num_influencers = influencer_cursor.count()
        print(timing.get_timestamp() + ": KnowledgeGraph: inserting followers for {} influencers".format(total_num_influencers))
        influencer_count = 1
        for influencer in influencer_cursor:
            follower_count = 1
            total_num_followers = len(influencer["followerIds"])
            for follower_id in influencer["followerIds"]:
                self._neo4j.add_follows_relationship(follower_id, influencer["id"])
                print(timing.get_timestamp() + ": KnowledgeGraph: inserted FOLLOWS relationship for follower {}/{} of "
                                               "influencer {}/{}".format(follower_count, total_num_followers,
                                                                         influencer_count, total_num_influencers))
                follower_count += 1
            influencer["f_rel_added"] = True
            self._users_mongodb.save(influencer)
            influencer_count += 1
        print(timing.get_timestamp() + ": KnowledgeGraph: DONE inserting FOLLOWS relationships for influencers")

    def insert_user(self, twitter_user):
        self._neo4j.insert_user(self._normalize_user_for_graph(twitter_user, Layers.TRAINING))

    @staticmethod
    def _normalize_user_for_graph(user, layer):
        return {"mongo_id": str(user["_id"]),
                "twitter_id": user["id"],
                "name": user["name"].replace("\\", "\\\\"),
                "screen_name": user["screen_name"].replace("\\", "\\\\"),
                "layer": layer.value,
                "type": user["type"]}
