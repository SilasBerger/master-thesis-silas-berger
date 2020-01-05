import math
import time
import tweepy
from src.util import timing


def get_rate_limit_status(twitter_api):
    """
    Get full rate limit status from API (warning: rate limiting applies to this endpoint as well)
    :param twitter_api: reference to the Tweepy API object
    :return: JSON object containing full rate limit status
    """
    return twitter_api.rate_limit_status()


def get_relevant_rate_limits(twitter_api):
    """
    Get rate limits of relevant endpoints. Currently includes '/search/tweets' and '/application/rate_limit_status'.
    Each status contains
        - limit (max. available calls per 15-minute window
        - remaining (remaining calls within current window)
        - reset (remaining minutes until window resets, always rounded up)
    :param twitter_api: reference to the Tweepy API object
    :return: aggregated rate limits status report, JSON object
    """
    current_status = twitter_api.rate_limit_status()
    search = _parse_rate_limit(current_status["resources"]["search"]["/search/tweets"])
    show_user = _parse_rate_limit(current_status["resources"]["users"]["/users/show/:id"])
    rate_limit_status = _parse_rate_limit(current_status["resources"]["application"]["/application/rate_limit_status"])
    return {
        "search": search,
        "show_user": show_user,
        "rate_limit_status": rate_limit_status
    }


def print_relevant_rate_limits(twitter_api):
    """
    Fetch and print aggregated rate limit report from get_relevant_rate_limits()
    :param twitter_api: reference to the Tweepy API object
    :return:
    """
    status = get_relevant_rate_limits(twitter_api)
    print(timing.get_timestamp() + ": rate limit '/search/tweets': " + str(status["search"])),
    print(timing.get_timestamp() + ": rate limit '/users/show/:id': " + str(status["show_user"]))
    print(timing.get_timestamp() + ": rate limit '/application/rate_limit_status': " + str(status["rate_limit_status"]))


def _parse_rate_limit(rl_node):
    """
    Extract limit/remaining/reset from a rate limit status report dict node corresponding to exactly one endpoint.
    Extract 'reset' field (UTC epoch seconds), convert to minutes, rounded up
    :param rl_node:
    :return:
    """
    limit = rl_node["limit"]
    remaining = rl_node["remaining"]
    reset = math.ceil((rl_node["reset"] - int(time.time())) / 60)
    return {
        "limit": limit,
        "remaining": remaining,
        "reset_in_minutes": reset
    }


def get_rate_limit_info(twitter_api, endpoint_path):
    """
    Get current rate limit information for specified endpoint. Throws TweepyError if rate limit endpoint itself
    is being rate-limited.

    :param twitter_api: Tweepy object
    :param endpoint_path: path in the format `/path/to/endpoint`, e.g. `/users/lookup`, `/users/show/:id`. Must
           be a valid Twitter API endpoint.
    :return: dictionary containing current rate limit info (`limit`, `remaining`, `reset_in_minutes`)
    """
    # TODO: identification over path string works but isn't ideal - better way to do this?
    # TODO: could keep track of rate limits on rate limit endpoint itself, so we can catch its limits
    endpoint_path = endpoint_path.strip()
    assert(endpoint_path[0] == '/')
    endpoint_package = endpoint_path.split("/")[1]
    current_status = twitter_api.rate_limit_status()
    return _parse_rate_limit(current_status["resources"][endpoint_package][endpoint_path])


def get_rate_limit_reset(twitter_api, endpoint_path):
    """
    Returns remaining minutes of rate limitation for given endpoint.

    :param twitter_api: Tweepy object
    :param endpoint_path: path in the format `/path/to/endpoint`, e.g. `/users/lookup`, `/users/show/:id`. Must
           be a valid Twitter API endpoint.
    :return: remaining minutes until the rate limitation resets for this endpoint
    """
    return get_rate_limit_info(twitter_api, endpoint_path)["reset_in_minutes"]


