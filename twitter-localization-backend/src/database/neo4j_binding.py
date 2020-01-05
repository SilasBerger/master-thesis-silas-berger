from neo4j import GraphDatabase
from src.model import User
from src.util import context
from src.localization import LocalizationConstants


class Neo4jBinding:
    """
    Wrapper for connection to and transactions with Neo4j graph database
    """

    def __init__(self):
        self.user = context.get_credentials("neo4j_user")
        self.password = context.get_credentials("neo4j_password")
        self.uri = context.get_config("neo4j_host")
        # TODO: wrap connection in a method, give clear feedback if connection fails
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def _run_transaction(self, method, query):
        with self.driver.session() as session:
            return session.read_transaction(method, query)

    @staticmethod
    def _execute_query(tx, query):
        return tx.run(query)

    # ======== Statistics ========

    # TODO add optional min confidence wherever useful

    def count_all_users(self):
        """
        Returns total number of User nodes in graph
        :return: total number of user nodes
        """
        res = self._run_transaction(Neo4jBinding._execute_query, "MATCH (a:User) RETURN count(a)")
        return res.single()["count(a)"]

    def count_all_swiss_users(self):
        """
        Returns total number of User nodes marked as `is:swiss: true`
        :return: number of Swiss users
        """
        res = self._run_transaction(Neo4jBinding._execute_query, "MATCH (a:User {isSwiss: true}) RETURN count(a)")
        return res.single()["count(a)"]

    def count_standard_swiss_users(self):
        """
        Returns number of User nodes with type `standard` and `isSwiss: true`
        :return: number of Swiss standard users (non-influencers)
        """
        res = self._run_transaction(Neo4jBinding._execute_query,
                                    "MATCH (a:User {isSwiss: true, type: 'standard'}) RETURN count(a)")
        return res.single()["count(a)"]

    def count_swiss_influencers(self):
        """
        Returns number of User nodes with type `influencer` and `isSwiss: true`
        :return: number of Swiss influencers
        """
        res = self._run_transaction(Neo4jBinding._execute_query,
                                    "MATCH (a:User {isSwiss: true, type: 'influencer'}) RETURN count(a)")
        return res.single()["count(a)"]

    def count_all_tweets(self):
        """
        Returns total number of Tweet nodes in the graph
        :return: total number of tweets in the graph
        """
        res = self._run_transaction(Neo4jBinding._execute_query, "MATCH (a:Tweet) RETURN count(a)")
        return res.single()["count(a)"]

    def count_swiss_tweets(self):
        """
        Returns number of Tweet nodes in the graph with `isSwiss: true`
        :return: number of Swiss tweets in the graph
        """
        res = self._run_transaction(Neo4jBinding._execute_query, "MATCH (a:Tweet {isSwiss: true}) RETURN count(a)")
        return res.single()["count(a)"]

    def delete_all_relationships(self):
        self._run_transaction(Neo4jBinding._execute_query, "MATCH (a)-[r]->(b) DELETE r")

    # ======== Get Users and Tweets ========
    def get_all_users(self):
        """
        Returns all User nodes
        :return: all User nodes
        """
        res = self._run_transaction(Neo4jBinding._execute_query, "MATCH (a:User) RETURN a")
        return [User.User.parseFromGraphNode(rec["a"]) for rec in res]

    def get_user_by_screen_name(self, screen_name):
        """
        Returns first User node with matching `screen_name`
        :param screen_name: target screen name
        :return: first User node with matching screen name
        """
        query = "MATCH (a:User {screen_name: '%s'}) RETURN a" % (screen_name,)
        res = self._run_transaction(Neo4jBinding._execute_query, query)
        res_list = [User.User.parseFromGraphNode(rec["a"]) for rec in res]
        if len(res_list) == 0:
            return None
        return res_list[0]

    def get_user_by_id(self, twitter_id):
        """
        Returns User node with matching `twitter_id`
        :param twitter_id: target twitter ID
        :return: first User node with matching twitter ID
        """
        query = "MATCH (a:User {id: %s}) RETURN a" % (twitter_id,)
        res = self._run_transaction(Neo4jBinding._execute_query, query)
        res_list = [User.User.parseFromGraphNode(rec["a"]) for rec in res]
        if len(res_list) == 0:
            return None
        return res_list[0]

    def user_exists(self, screen_name):
        """
        Checks whether a user with the given screen name exists in the graph
        :param screen_name: target screen name
        :return: True if user with matching screen name was found, False else
        """
        return self.get_user_by_screen_name(screen_name) is not None

    # ======== Insert Users and Tweets ========
    def insert_user(self, user):
        """
        Inserts given user object into graph
        :param user: user object to be inserted
        """
        query = "CREATE (a:User "
        query += self._parse_dict_for_query_string(user)
        query += ")"
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def add_follows_relationship(self, follower_id, followed_user_id):
        query = "MATCH (a:User), (b:User)"
        query += " WHERE a.twitter_id=" + str(follower_id) + " and b.twitter_id=" + str(followed_user_id)
        query += " MERGE (a)-[:FOLLOWS]->(b)"
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def add_localization_relation(self, metamodel, twitter_user_id, geonames_id, confidence, sequence_number=0,
                                  type="final"):
        assert type in [LocalizationConstants.PARTIAL, LocalizationConstants.FINAL]
        query = "MATCH (a:User {twitter_id: %s}), (b:Place {geonames_id: %s})" % (twitter_user_id, geonames_id,)
        query += " MERGE (a)-[r:LOCALIZED_TO {model_id: '%s', model_instance_id: '%s', seq: '%s', type: '%s', " \
                 "confidence: %s}]->(b)" % (
                     metamodel.get_model_id(), metamodel.get_model_instance_id(), sequence_number, type, confidence
                 )
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def remove_localizations_by_model(self, model_id):
        query = "MATCH (a:User)-[r:LOCALIZED_TO]->(b:Place)"
        query += " WHERE r.model_id='" + model_id + "'"
        query += " DELETE r"
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def remove_localizations_by_model_instance(self, model_instance_id, keep_final=False):
        query = "MATCH (a:User)-[r:LOCALIZED_TO]->(b:Place)"
        query += " WHERE r.model_instance_id='%s'" % (model_instance_id,)
        if keep_final:
            query += " and r.type<>'%s'" % (LocalizationConstants.FINAL,)
        query += " DELETE r"
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def remove_all_localizations(self):
        query = "MATCH (a:User)-[r:LOCALIZED_TO]->(b:Place) DELETE r"
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def remove_non_final_localizations(self):
        query = "MATCH (a:User)-[r:LOCALIZED_TO]->(b:Place) "
        query += " WHERE r.type<>'%s'" % (LocalizationConstants.FINAL,)
        query += " DELETE r"
        res = self._run_transaction(Neo4jBinding._execute_query, query)

    def fetch_localizations_for_user(self, twitter_user_id, model_instance_id, localization_type):
        query = "MATCH (a:User)-[r:LOCALIZED_TO]->(b:Place)"
        query += " WHERE r.model_instance_id='%s' and r.type='%s' and a.twitter_id=%s" \
                 % (model_instance_id, localization_type, twitter_user_id)
        query += " RETURN a, r, b"
        res = self._run_transaction(Neo4jBinding._execute_query, query)
        return res

    def fetch_localizations_by_model_instance(self, model_instance_id, localization_type):
        query = "MATCH (a:User)-[r:LOCALIZED_TO]->(b:Place)"
        query += " WHERE r.model_instance_id='%s' and r.type='%s'" % (model_instance_id, localization_type)
        query += " RETURN a, r, b"
        res = self._run_transaction(Neo4jBinding._execute_query, query)
        return res

    # ======== Helpers ===========
    def _parse_dict_for_query_string(self, dictionary):
        items = []
        for key, value in dictionary.items():
            item = (key + ": ")
            if type(value) == str:
                item += "'" + value.replace("'", "\\'") + "'"
            else:
                item += str(value)
            items.append(item)
        return "{" + (", ".join(items)) + "}"
