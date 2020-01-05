import urllib
from urllib.parse import urlencode

import pymongo
import requests

from src.geonames.GeonamesException import GeonamesException
from src.geonames.GeonamesRateLimitException import GeonamesRateLimitException
from src.util import context


class GeonamesApi:

    def __init__(self):
        self._search_url = "http://api.geonames.org/searchJSON?"
        self._username = context.get_credentials("geonames_username")

    def search(self, query):
        urlencoded_query = urllib.parse.quote(str(query), safe='')
        request_url = self._search_url + "q={}&username={}".format(urlencoded_query, self._username)
        result = requests.get(request_url).json()

        if "status" in result:
            # error message, something went wrong
            error_code = result["status"]["value"]
            if GeonamesException.is_rate_limit_error_code(error_code):
                raise GeonamesRateLimitException(error_code)
            raise GeonamesException(error_code)

        if result["totalResultsCount"] <= 0:
            # no matches found
            return None

        # taking first match
        return result["geonames"][0]
