import pymongo
import requests
import json
import time
import os

import src.util.paths
from src.model import constants
from src.util import context


class InfluencerListManager:
    """
    Handles synchronization between the influencer lists on GitHub and their representation in MongoDB
    """

    _crawl_delay_seconds = 2

    def __init__(self, use_local_list_files=False):
        self._use_local_files = use_local_list_files
        self._init_master_list()
        self._init_db_connection()
        self._connect()

    def _init_master_list(self):
        self._list_base_url = context.get_config("influencer_list_url")
        if self._use_local_files:
            # convert relative local path to normalized absolute path
            self._list_base_url = src.util.paths.convert_project_relative_path(self._list_base_url)
        self._available_list_names = context.get_config("influencer_list_names")

    def _init_db_connection(self):
        self._mongo_host = context.get_config("mongodb_host")
        self._db_name = context.get_config("influencers_db")
        self._collection_name = context.get_config("influencers_collection")

    def _connect(self):
        self._mongodb_connection = pymongo.MongoClient(self._mongo_host)
        self._db_influencers = self._mongodb_connection[self._db_name]
        self._coll_influencers = self._db_influencers[self._collection_name]

    def sync_all_lists(self):
        """
        Synchronizes influencers collection in MongoDB with influencers lists on GitHub.
        """
        print("Started syncing influencer master lists with DB")
        screen_names_on_lists = []
        self._add_or_update(screen_names_on_lists)
        print("Removing entries which are no longer on any list")
        self._delete_entries_not_in_list(screen_names_on_lists)  # remove entries from DB if they are on no list
        print("Sync complete")

    def _add_or_update(self, screen_names_on_lists):
        for list_name in self._available_list_names:
            print("Syncing list '{}'".format(list_name))
            list_json = self._fetch_list_json(list_name)  # load list JSON document
            self._sync_list(list_json, list_name, screen_names_on_lists)  # sync this master list with DB
            time.sleep(InfluencerListManager._crawl_delay_seconds)  # wait to avoid spamming the server

    def _fetch_list_json(self, list_name):
        if self._use_local_files:
            with open(os.path.join(self._list_base_url, list_name + ".json")) as f:
                return json.load(f)["accounts"]
        else:
            return json.loads(requests.get(self._list_base_url + list_name + ".json").content)["accounts"]

    def _sync_list(self, list_json, list_name, screen_names_on_lists):
        for list_entry in list_json:
            screen_names_on_lists.append(list_entry["screen_name"])  # save screen name as present on a list
            list_entry["category"] = list_name
            existing_entry = self._fetch_by_screen_name(list_entry)
            if existing_entry is None:
                self._insert_new_entry(list_entry)
            else:
                self._update_existing_entry(list_entry, existing_entry)

    def _fetch_by_screen_name(self, target):
        return self._coll_influencers.find_one({"screen_name": target["screen_name"]})

    def _insert_new_entry(self, entry):
        entry["crawl_status"] = constants.CrawlStatus.NEW.value
        self._coll_influencers.save(entry)

    def _update_existing_entry(self, list_entry, existing_entry):
        list_entry["_id"] = existing_entry["_id"]  # needed so MongoDB can identify it as the same document
        list_entry["crawl_status"] = existing_entry["crawl_status"]  # keep crawl status information
        self._coll_influencers.save(list_entry)  # overwrite remaining information with list entry

    def _delete_entries_not_in_list(self, screen_names_on_lists):
        self._coll_influencers.delete_one({"screen_name": {"$nin": screen_names_on_lists}})
