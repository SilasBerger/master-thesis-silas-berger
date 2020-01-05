class GeonamesException(Exception):

    rate_limit_error_codes = {
        18: "daily",
        19: "hourly",
        20: "weekly"
    }

    _error_codes = {
        10: "Authorization Exception",
        11: "record does not exist",
        12: "other error",
        13: "database timeout",
        14: "invalid parameter",
        15: "no result found",
        16: "duplicate exception",
        17: "postal code not found",
        18: "daily limit of credits exceeded",
        19: "hourly limit of credits exceeded",
        20: "weekly limit of credits exceeded",
        21: "invalid input",
        22: "server overloaded exception",
        23: "service not implemented",
        24: "radius too large",
        25: "maxRows too large"
    }

    def __init__(self, error_code):
        message = "Geonames Exception: undefined error code {}".format(error_code)
        if error_code in GeonamesException._error_codes:
            message = "Geonames Exception: {} (code {})".format(GeonamesException._error_codes[error_code], error_code)
        super().__init__(message)

    @staticmethod
    def is_rate_limit_error_code(error_code):
        return error_code in GeonamesException.rate_limit_error_codes
