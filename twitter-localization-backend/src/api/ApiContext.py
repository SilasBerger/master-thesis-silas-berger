import os
from src.util import paths
from threading import Lock


class ApiContext:

    def __init__(self):
        available_meta_models = self.list_meta_models()
        self._metamodels = {}
        self._metamodel_status = {}
        self.metamodel_locks = {}
        self._localizations = {"complete": [], "pending": [], "failed": []}
        self.localization_worker_lock = Lock()
        self._localizations_lock = Lock()
        for metamodel_name in available_meta_models:
            self._metamodels[metamodel_name] = None
            self.metamodel_locks[metamodel_name] = Lock()
            self._metamodel_status[metamodel_name] = {
                "metamodel": metamodel_name,
                "status": "offline",
                "error": None
            }

    @staticmethod
    def list_meta_models():
        files = os.listdir(paths.convert_project_relative_path("src/localization/metamodels"))
        exclude = ["__init__.py", "__pycache__"]
        return [file.split(".")[0] for file in files if file not in exclude]

    def metamodel_status(self):
        return self._metamodel_status

    def metamodel(self, metamodel_name):
        return self._metamodels[metamodel_name]

    def set_metamodel_status(self, metamodel_name, status, error=None):
        self._metamodel_status[metamodel_name] = {
            "metamodel": metamodel_name,
            "status": status,
            "error": error
        }

    def set_metamodel(self, metamodel_name, instance):
        self._metamodels[metamodel_name] = instance

    def add_pending_localization(self, screen_name, metamodel_name):
        self._localizations_lock.acquire(blocking=True)
        try:
            result = {
                "screenName": screen_name,
                "metamodelName": metamodel_name,
            }
            self._localizations["pending"].append(result)
            return result
        finally:
            self._localizations_lock.release()

    def add_complete_localization(self, pending_localization, result_tuple):
        self._localizations_lock.acquire(blocking=True)
        try:
            if result_tuple[0] is None:
                result = {
                    "screenName": pending_localization["screenName"],
                    "metamodelName": pending_localization["metamodelName"],
                    "isSwiss": False,
                    "confidence": 0,
                    "index": len(self._localizations["failed"])
                }
                self._localizations["failed"].append(result)
            else:
                result = {
                    "screenName": pending_localization["screenName"],
                    "metamodelName": pending_localization["metamodelName"],
                    "isSwiss": "true" if (result_tuple[0] == 1) else "false",
                    "confidence": result_tuple[1],
                    "index": len(self._localizations["complete"])
                }
                self._localizations["complete"].append(result)
            del self._localizations["pending"][self._localizations["pending"].index(pending_localization)]
        finally:
            self._localizations_lock.release()

    def _complete_localizations(self, after_index=0):
        return self._localizations["complete"][after_index:]

    def _pending_localizations(self):
        return self._localizations["pending"]

    def localizations_update(self, after_index=0):
        self._localizations_lock.acquire(blocking=True)
        localizations = {"complete": [], "pending": [], "failed": []}
        try:
            localizations["pending"] = self._localizations["pending"]
            localizations["complete"] = self._complete_localizations(after_index)
            localizations["failed"] = self._localizations["failed"]
        finally:
            self._localizations_lock.release()
            return localizations
