import os

import pymongo

from src.util import context, paths


class OfflineDataInserter():
    def __init__(self):
        self._host_connection = pymongo.MongoClient(context.get_config("mongodb_host"))
        self._database_connection = self._host_connection[context.get_config("influencers_db")]
        self._geonames_places_mongodb = self._database_connection[context.get_config("geonames_places_collection")]

    def insert_from_file(self, filename, country_name, country_code, country_id):
        """
        TBA
        :param filename: filename relative to project_root/data
        :return: None
        """
        places = self._parse_populated_places(filename, country_name, country_code, country_id)
        for place in places:
            print("checking/inserting place {} ({})".format(place["name"], place["geonames_id"]))
            existing_entry = self._fetch_existing_entry(place["geonames_id"])
            if existing_entry is not None:
                if "alternate_names" in existing_entry:
                    continue
                existing_entry["alternate_names"] = place["alternate_names"]
                self._geonames_places_mongodb.save(existing_entry)
            else:
                self._geonames_places_mongodb.save(place)

    def _parse_populated_places(self, filename, country_name, country_code, country_id):
        file_path = os.path.join(paths.get_project_root(), "data", filename)
        with open(file_path, "r", encoding="utf-8") as infile:
            lines = infile.readlines()
        places = []
        for line in lines:
            tuple = line.split("\t")
            if not tuple[7].startswith("PPL"):
                # not a populated place (PPL, PPLA, PPLA2, PPLC, etc.), skip
                # see http://www.geonames.org/export/codes.html
                continue
            place = {
                "geonames_id": int(tuple[0]),
                "country_id": country_id,
                "name": tuple[1],
                "population": int(tuple[14]),
                "state": None,
                "state_code": tuple[10],
                "country_name": country_name,
                "country_code": country_code,
                "lng": tuple[5],
                "lat": tuple[4],
                "alternate_names": tuple[3].split(","),
                "feature_code": tuple[7]
            }
            places.append(place)
        return places

    def _fetch_existing_entry(self, geonames_id):
        return self._geonames_places_mongodb.find_one({"geonames_id": geonames_id})

    # !! error fix !!
    def add_geonames_feature(self, filename):
        file_path = os.path.join(paths.get_project_root(), "data", filename)
        with open(file_path, "r", encoding="utf-8") as infile:
            lines = infile.readlines()
        tuples = [line.split("\t") for line in lines]

        cursor = self._geonames_places_mongodb.find({
            "$and": [
                {"country_code": "CH"},
                {"feature_code": {"$exists": False}},
            ]
        })
        for place in cursor:
            self._insert_feature_code(place, tuples)

    # !! error fix !!
    def _insert_feature_code(self, place, tuples):
        place_id = int(place["geonames_id"])
        for tup in tuples:
            tup_id = int(tup[0])
            if place_id == tup_id:
                print("adding feature for place " + place["name"])
                place["feature_code"] = tup[7]
                self._geonames_places_mongodb.save(place)
                return
        print("no match found for place " + str(place))

    # !! error fix !!
    def remove_non_ppl(self):
        for place in self._geonames_places_mongodb.find({"country_code": "CH"}):
            if "feature_code" not in place:
                continue
            if not place["feature_code"].startswith("PPL"):
                print("Removing place " + str(place))
                self._geonames_places_mongodb.delete_one({"_id": place["_id"]})

    # !! error fix !!
    def convert_strings_to_int(self):
        for place in self._geonames_places_mongodb.find({}):
            print(place)
            place["geonames_id"] = int(place["geonames_id"])
            place["population"] = int(place["population"])
            self._geonames_places_mongodb.save(place)
