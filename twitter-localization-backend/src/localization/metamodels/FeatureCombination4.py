import numpy as np

from src.localization import TrainValidateTestProvider
from src.localization.Metamodel import Metamodel
from src.localization.classifiers.SKLearn import SKLearn
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from src.localization.featureextractors.SwissInfluencersFollowedRatio import SwissInfluencersFollowedRatio
from src.localization.featureextractors.SwissTweetInteraction import SwissTweetInteraction
from src.localization.featureextractors.SwissNamedPlaces import SwissNamedPlaces
from src.util import timing
from tqdm import tqdm


class FeatureCombination4(Metamodel):
    def __init__(self, use_cache=True, allow_cache_updates=True):
        super().__init__("Feature Combination 1", use_cache, allow_cache_updates)
        self._swiss_named_places = SwissNamedPlaces(self._allow_cache_updates)
        self._inf_followed = SwissInfluencersFollowedRatio(self._allow_cache_updates)
        self._swiss_tweet_interaction = SwissTweetInteraction(aggregate_interactions=False,
                                                              allow_cache_updates=self._allow_cache_updates)
        self._clf = SKLearn(KNeighborsClassifier(5))

    def _build(self):
        train, validate, test = TrainValidateTestProvider.get_data()
        print(timing.get_timestamp() + ": FeatureCombination1: building feature matrix for train set")
        train_matrix = self._extract_feature_matrix(train)
        print(timing.get_timestamp() + ": FeatureCombination1: building feature matrix for validation set")
        validate_matrix = self._extract_feature_matrix(validate)
        print(timing.get_timestamp() + ": FeatureCombination1: training classifier")
        score = self._clf.train(train_matrix, validate_matrix)
        self._training_scores.append({self._clf.get_name(): score})

    def _classify(self, twitter_user):
        feature_vec = np.array([self._swiss_named_places.extract_for(twitter_user, self._use_cache),
                                self._inf_followed.extract_for(twitter_user, self._use_cache)])
        swiss_tweet_interactions = np.array(self._swiss_tweet_interaction.extract_for(twitter_user, self._use_cache))
        feature_vec = np.append(feature_vec, swiss_tweet_interactions)
        return self._clf.classify(feature_vec)

    def _extract_feature_matrix(self, sample_set):
        feature_vectors = []
        for sample in tqdm(sample_set):
            feature_vec = np.array([self._swiss_named_places.extract_for(sample, self._use_cache),
                                    self._inf_followed.extract_for(sample, self._use_cache)])
            swiss_tweet_interactions = np.array(self._swiss_tweet_interaction.extract_for(sample, self._use_cache))
            feature_vec = np.append(feature_vec, swiss_tweet_interactions)
            feature_vec = np.append(feature_vec, (1 if sample["is_swiss"] else 0))
            feature_vectors.append(feature_vec)
        return np.array(feature_vectors)
