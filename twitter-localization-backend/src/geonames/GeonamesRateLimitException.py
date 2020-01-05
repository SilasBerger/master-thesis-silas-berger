from src.geonames.GeonamesException import GeonamesException


class GeonamesRateLimitException(GeonamesException):
    def __init__(self, error_code):
        super(GeonamesRateLimitException, self).__init__(error_code)
        assert error_code in GeonamesException.rate_limit_error_codes
        self._scope = GeonamesException.rate_limit_error_codes[error_code]

    def is_daily(self):
        return self._scope == "daily"

    def is_hourly(self):
        return self._scope == "hourly"

    def is_weekly(self):
        return self._scope == "weekly"
