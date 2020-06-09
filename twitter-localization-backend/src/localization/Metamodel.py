from src.util import timing
from src.localization.MetamodelNotReadyError import MetamodelNotReadyError
from src.localization.Database import Database
from src.twitter.TwitterApiBinding import TwitterApiBinding
from src.crawler.UserManager import UserManager
from src.localization import LocalizationConstants


class Metamodel:
    """
    add doc
    """

    def __init__(self, model_name, use_cache=True, allow_cache_updates=True):
        self._use_cache = use_cache
        self._allow_cache_updates = allow_cache_updates
        self._is_ready = False
        self._model_name = model_name
        self._model_id = model_name.replace(" ", "_").lower()
        self._model_instance_id = self._model_id + "_" + timing.get_millis_timestamp()
        self._training_scores = []
        self._db = Database.instance()
        self._twitter = TwitterApiBinding()
        self._user_manager = UserManager(self._twitter)

    def build(self):
        """
        Assembles the model, trains all classifiers, gets model ready for classification
        :return:    list of dictionaries of the form {classifier_name: training_score}
        """
        print(timing.get_timestamp() + ": building model " + self._model_instance_id)
        self._build()
        self._is_ready = True
        print(timing.get_timestamp() + ": finished building model " + self._model_instance_id)
        return self._training_scores

    def classify(self, screen_name):
        if not self._is_ready:
            raise MetamodelNotReadyError(self._model_id)
        twitter_user = self._user_manager.ensure_fetch_twitter_user(screen_name)
        if twitter_user is None:
            print(timing.get_timestamp() + ": model {} can't localize user with screen_name {}: not found"
                  .format(self._model_instance_id, screen_name))
            return None, None
        print(timing.get_timestamp() + ": localizing @{}".format(screen_name))
        predicted_class, confidence = self._classify(twitter_user)
        return predicted_class, confidence

    def get_model_name(self):
        return self._model_name

    def get_model_id(self):
        return self._model_id

    def get_model_instance_id(self):
        return self._model_instance_id

    def get_training_scores(self):
        return self._training_scores

    def cleanup(self, keep_final_decisions=False):
        self._db.neo4j.remove_localizations_by_model_instance(self._model_instance_id, keep_final=keep_final_decisions)

    def _build(self):
        raise NotImplementedError("function _build() is abstract in Model")

    def _classify(self, twitter_user):
        raise NotImplementedError("function _classify() is abstract in Model")
