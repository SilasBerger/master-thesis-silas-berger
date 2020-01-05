import numpy as np

from src.localization import TrainValidateTestProvider
from src.localization.Metamodel import Metamodel
from src.localization.classifiers.SingleFeatureBinaryThreshold import SingleFeatureBinaryThreshold
from src.localization.featureextractors.SwissInfluencersFollowedRatio import SwissInfluencersFollowedRatio
from src.util import timing
from tqdm import tqdm


class SimpleInfluencerFollowedRatio(Metamodel):
    def __init__(self, use_cache=True, allow_cache_updates=True):
        super().__init__("Simple Influencer Followed Ratio", use_cache, allow_cache_updates)
        self._inf_ratio_extractor = SwissInfluencersFollowedRatio(self._allow_cache_updates)
        self._clf = SingleFeatureBinaryThreshold()

    def _build(self):
        train, validate, test = TrainValidateTestProvider.get_data()
        print(timing.get_timestamp() + ": SimpleInfluencerFollowedRatio: building feature matrix for train set")
        train_matrix = self._extract_feature_matrix(train)
        print(timing.get_timestamp() + ": SimpleInfluencerFollowedRatio: building feature matrix for validation set")
        validate_matrix = self._extract_feature_matrix(validate)
        print(timing.get_timestamp() + ": SimpleInfluencerFollowedRatio: training classifier")
        score = self._clf.train(train_matrix, validate_matrix)
        self._training_scores.append({self._clf.get_name(): score})

    def _classify(self, twitter_user):
        feature_vector = np.array([self._inf_ratio_extractor.extract_for(twitter_user, self._use_cache)])
        return self._clf.classify(feature_vector)

    def _extract_feature_matrix(self, sample_set):
        feature_vectors = []
        for sample in tqdm(sample_set):
            feature_vec = np.array([self._inf_ratio_extractor.extract_for(sample, self._use_cache),
                                    1 if sample["is_swiss"] else 0])
            feature_vectors.append(feature_vec)
        return np.array(feature_vectors)
