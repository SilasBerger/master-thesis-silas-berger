import random
import json
import os

from src.localization.Database import Database
from src.util import timing
from src.util import context
from src.util import paths


_train = []
_validate = []
_test = []


def get_data():
    if len(_train) == 0:
        print(timing.get_timestamp() + ": TrainTestSupplier: fetching train/validate/test data")
        _load_data()
    return _train, _validate, _test


def export_sets_to_file(filename):
    data_dict = {"train": [user["id"] for user in _train],
                 "validate": [user["id"] for user in _validate],
                 "test": [user["id"] for user in _test]}
    with open(paths.convert_project_relative_path(os.path.join("configs", str(filename) + ".json")), "w") as outfile:
        json.dump(data_dict, outfile, ensure_ascii=False, indent=4)


def _load_data():
    use_file = context.get_config("tvt").get("use_file", None)
    if (use_file is None) or (use_file == ""):
        _load_random_data()
    else:
        _load_sets_from_file()


def _load_random_data():
    print(timing.get_timestamp() + ": TrainTestSupplier: creating randomized sets")
    global _train, _validate, _test
    size_train = context.get_config("tvt")["size_train_set"]
    size_validate = context.get_config("tvt")["size_validation_set"]
    size_test = context.get_config("tvt")["size_test_set"]
    total_users_needed = size_train + size_validate + size_test
    num_user_per_class = int(total_users_needed / 2)
    ch_users = [user for user
                in Database.instance().users_test_set_mongodb.find({"is_swiss": True}).limit(num_user_per_class)]
    foreign_users = [user for user
                     in Database.instance().users_test_set_mongodb.find({"is_swiss": False}).limit(num_user_per_class)]
    users = ch_users + foreign_users
    random.shuffle(users)  # a shuffled set of 50% CH- and 50% foreign users, to be split up into the three sets
    _train = [users.pop(0) for i in range(0, size_train)]
    _validate = [users.pop(0) for i in range(0, size_validate)]
    _test = [users.pop(0) for i in range(0, size_test)]
    assert len(users) == 0


def _load_sets_from_file():
    filename = context.get_config("tvt")["use_file"]
    print(timing.get_timestamp() + ": TrainTestSupplier: loading existing set {}.json".format(filename))
    global _train, _validate, _test
    with open(paths.convert_project_relative_path(os.path.join("configs", str(filename) + ".json")), "r") as infile:
        data_dict = json.load(infile)
        train_users_cursor = Database.instance().users_test_set_mongodb.find({"id": {"$in": data_dict["train"]}})
        validate_users_cursor = Database.instance().users_test_set_mongodb.find({"id": {"$in": data_dict["validate"]}})
        test_users_cursor = Database.instance().users_test_set_mongodb.find({"id": {"$in": data_dict["test"]}})
        _train = [user for user in train_users_cursor]
        _validate = [user for user in validate_users_cursor]
        _test = [user for user in test_users_cursor]
        if context.get_config("tvt").get("shuffle_loaded_set", False):
            random.shuffle(_train)
            random.shuffle(_test)
            random.shuffle(_validate)
