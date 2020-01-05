import datetime
import time


def get_timestamp():
    """
    Get current time as formatted string
    :return: current time string in the format YYYY-mm-dd HH:MM
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def get_millis_timestamp():
    return str(int(round(time.time() * 1000)))


def get_seconds_to_start_of_next_hour(added_margin=0):
    delta = datetime.timedelta(hours=1)
    now = datetime.datetime.now()
    next_hour = (now + delta).replace(microsecond=0, second=0, minute=2)
    return (next_hour - now).seconds + added_margin
