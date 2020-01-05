from src.util import paths
import json

with open(paths.convert_project_relative_path("configs/large-training-1000-100-100.json")) as infile:
    data = json.load(infile)

train_list = data["train"]
validate_list = data["validate"]
test_list = data["test"]

print("train: {}, validate: {}, test: {}, exp. total: {}".format(len(train_list), len(validate_list), len(test_list),
                                                                 len(train_list)+len(validate_list)+len(test_list)))
union_of_lists = set(train_list).union(set(validate_list)).union(set(test_list))
print("size of union: {}".format(len(union_of_lists)))