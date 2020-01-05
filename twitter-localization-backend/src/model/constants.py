from enum import Enum


class CrawlStatus(Enum):
    NEW = "new"
    COLLECTED = "collected"
    IN_GRAPH = "in_graph"
    FOLLOWER_IDS_COLLECTED = "follower_ids_collected"
    FOLLOWERS_COLLECTED = "followers_collected"
    FOLLOWERS_IN_GRAPH = "followers_in_graph"
    NOT_FOUND = "userSuspendedOrNotFound"


class UserType(Enum):
    STANDARD = "standard"
    INFLUENCER = "influencer"