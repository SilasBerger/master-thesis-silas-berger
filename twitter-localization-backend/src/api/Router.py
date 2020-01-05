import traceback

from threading import Thread
from flask import request, Response
from flask import jsonify

from src.api.ApiContext import ApiContext
from src.localization.Database import Database
from src.localization.metamodels.FeatureCombination4 import FeatureCombination4
from src.localization.metamodels.SimpleHashtagSimilarity import SimpleHashtagSimilarity
from src.localization.metamodels.SimpleInfluencerFollowedRatio import SimpleInfluencerFollowedRatio
from src.localization.metamodels.SimpleSwissFriendRatio import SimpleSwissFriendRatio
from src.localization.metamodels.SimpleSwissNamedPlaces import SimpleSwissNamedPlacesCount
from src.localization.metamodels.SimpleSwissTweetInteraction import SimpleSwissTweetInteraction
from src.localization.metamodels.SimpleTweetInteractionBehavior import SimpleTweetInteractionBehavior


api_context = ApiContext()


def route(app):
    # =================== Demo Routes =================== #
    @app.route('/')
    def hello_world():
        return 'Hello, World!'

    @app.route("/echoPost", methods=["POST"])
    def echo_post():
        json_data = request.get_json()
        return jsonify({"yourRequestData": json_data})

    @app.route("/echoUser/<user_name>")
    def echo_user(user_name):
        return jsonify({"yourUsername": user_name})

    @app.route("/echoQuery")
    def echo_query():
        query_dict = request.args
        return jsonify({"yourQuery": query_dict})
    # ================= End Demo Routes ================== #

    # ===================== Routes ======================= #
    @app.route("/metamodels")
    def metamodels():
        return jsonify(api_context.metamodel_status())

    @app.route("/buildmetamodel", methods=["POST"])
    def buildmetamodel():
        # TODO: Handle request body is None.
        request_body = request.get_json()
        if "metamodel" not in request_body:
            return Response("No 'metamodel' specified", status=400)
        metamodel_name = request_body["metamodel"]
        if metamodel_name not in api_context.list_meta_models():
            return Response("No metamodel '" + metamodel_name + "'", status=404)
        lock_acquired = api_context.metamodel_locks[metamodel_name].acquire(blocking=True, timeout=2)
        if not lock_acquired:
            return Response("Metamodel '" + metamodel_name + "' is already being built", status=423)
        ModelBuilder(metamodel_name).start()
        return Response(status=204)

    @app.route("/localize", methods=["POST"])
    def localize():
        request_body = request.get_json()
        if "screenName" not in request_body:
            return Response("No 'screenName' specified")
        if "metamodel" not in request_body:
            return Response("No 'metamodel' specified")
        screen_name = request_body["screenName"]
        metamodel_name = request_body["metamodel"]
        if metamodel_name not in api_context.metamodel_status():
            return Response("No metamodel '" + metamodel_name + "'", status=404)
        if api_context.metamodel_status()[metamodel_name]["status"] != "online":
            return Response("Metamodel '" + metamodel_name + "' is offline", status=404)
        if metamodel_name not in api_context.list_meta_models():
            return Response("No metamodel '" + metamodel_name + "'", status=404)
        LocalizationWorker(screen_name, metamodel_name).start()
        return jsonify(api_context.localizations_update())

    @app.route("/localizations")
    def localizations():
        return jsonify(api_context.localizations_update())

    @app.route("/pendinglocalizations")
    def pendinglocalizations():
        return jsonify(api_context.localizations_update())

    @app.route("/statistics")
    def statistics():
        db = Database.instance()
        users_count = db.users_mongodb.find({}).count()
        tvt_count = db.users_test_set_mongodb.find({}).count()
        tvt_swiss_count = db.users_test_set_mongodb.find({"is_swiss": True}).count()
        tweets_count = db.tweets_mongodb.find({}).count()
        influencers_count = db.influencers_mongodb.find({}).count()
        media_count = db.influencers_mongodb.find({"category": {"$in": ["newspapers", "radios", "televisions"]}}).count()
        sports_count = db.influencers_mongodb.find({"category": {"$in": ["sports-teams"]}}).count()
        politics_count = db.influencers_mongodb.find({"category": {"$in": ["political-parties", "politicians"]}}).count()
        other_count = db.influencers_mongodb.find({"category": {"$in": ["personalities"]}}).count()
        stats = {
            "usersCount": users_count,
            "tvtUsersCount": tvt_count,
            "tvtSwissUsersCount": tvt_swiss_count,
            "tweetsCount": tweets_count,
            "influencersCount": influencers_count,
            "mediaInfluencersCount": media_count,
            "sportsInfluencersCount": sports_count,
            "politicsInfluencersCount": politics_count,
            "otherInfluencersCount": other_count,
        }
        return jsonify(stats)
    # =================== End Routes ===================== #

    class ModelBuilder(Thread):

        def __init__(self, metamodel_name):
            super().__init__()
            self._metamodel_name = metamodel_name
            self._metamodel = None

        def _instantiate_metamodel(self):
            metamodel = None
            if self._metamodel_name == "FeatureCombination1":
                metamodel = FeatureCombination4()
            elif self._metamodel_name == "SimpleHashtagSimilarity":
                metamodel = SimpleHashtagSimilarity()
            elif self._metamodel_name == "SimpleInfluencerFollowedRatio":
                metamodel = SimpleInfluencerFollowedRatio()
            elif self._metamodel_name == "SimpleSwissFriendRatio":
                metamodel = SimpleSwissFriendRatio()
            elif self._metamodel_name == "SimpleSwissNamedPlacesCount":
                metamodel = SimpleSwissNamedPlacesCount()
            elif self._metamodel_name == "SimpleSwissTweetInteraction":
                metamodel = SimpleSwissTweetInteraction()
            elif self._metamodel_name == "SimpleTweetInteractionBehavior":
                metamodel = SimpleTweetInteractionBehavior()
            return metamodel

        def run(self):
            api_context.set_metamodel_status(self._metamodel_name, "building")
            self._metamodel = self._instantiate_metamodel()

            if self._metamodel is None:
                api_context.set_metamodel_status(self._metamodel_name,
                                                 "error",
                                                 "Metamodel '" + self._metamodel_name + "' not instantiated.")
                api_context.metamodel_locks[self._metamodel_name].release()
                return

            try:
                self._metamodel.build()
                api_context.set_metamodel(self._metamodel_name, self._metamodel)
            except Exception as ex:
                api_context.set_metamodel_status(self._metamodel_name, "error", str(ex))
                api_context.metamodel_locks[self._metamodel_name].release()
                print(traceback.format_exc())
                return
            api_context.set_metamodel_status(self._metamodel_name, "online")
            api_context.metamodel_locks[self._metamodel_name].release()


class LocalizationWorker(Thread):

    def __init__(self, screen_name, metamodel_name):
        super().__init__()
        self._screen_name = screen_name
        self._metamodel_name = metamodel_name
        self._pending_localization = api_context.add_pending_localization(screen_name, metamodel_name)

    def run(self):
        api_context.localization_worker_lock.acquire(blocking=True)
        try:
            result = api_context.metamodel(self._metamodel_name).classify(self._screen_name)
            api_context.add_complete_localization(self._pending_localization, result)
        finally:
            api_context.localization_worker_lock.release()

