import pymongo

from src.util import context


class GeonamesLocalDatabase:

    def __init__(self):
        self._host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
        self._database_connection = self._host_connection[context.get_config("influencers_db")]
        self._geonames_places_mongodb = self._database_connection[context.get_config("geonames_places_collection")]

    def search(self, query, first_match=False):
        if (query is None) or (query == ""):
            return None
        results = self._match_name(query)
        if self._not_empty(results):
            return self._limit_result(results, first_match)
        results = self._match_name_or_alternate_name(query)
        if self._not_empty(results):
            return self._limit_result(results, first_match)
        query_parts = [qp.strip() for qp in query.split(",")]
        for part in query_parts:
            results = self._match_name(part)
            if self._not_empty(results):
                return self._limit_result(results, first_match)
            results = self._match_name_or_alternate_name(part)
            if self._not_empty(results):
                return self._limit_result(results, first_match)
        return None

    def _match_name(self, query_string):
        return self._geonames_places_mongodb.find({"name": query_string})

    def _match_name_or_alternate_name(self, query_string):
        return self._geonames_places_mongodb.find({
            "$or": [
                {"name": query_string},
                {"alternate_names": {"$elemMatch": {"$eq": query_string}}}
            ]
        })

    def _not_empty(self, result_cursor):
        return (result_cursor is not None) and (result_cursor.count() > 0)

    def _limit_result(self, results, first_match):
        if first_match:
            return results[0]
        return results
