import numpy as np
from sklearn.neighbors import KNeighborsClassifier

from src.localization import TrainValidateTestProvider
from src.localization.Metamodel import Metamodel
from src.localization.classifiers.SKLearn import SKLearn
from src.localization.featureextractors.TweetInteractionBehavior import TweetInteractionBehavior
from src.localization.featureextractors.HashtagSimilarity import HashtagSimilarity
from tqdm import tqdm


class FeatureCombination5(Metamodel):
    def __init__(self, use_cache=True, allow_cache_updates=True):
        super().__init__("Simple Tweet Interaction Behavior", use_cache, allow_cache_updates)
        self._train, self._validate, self._test = TrainValidateTestProvider.get_data()
        self._tweet_interaction_behavior = TweetInteractionBehavior(allow_cache_updates=self._allow_cache_updates)
        self._hashtag_similarity = HashtagSimilarity(self._train, 100, self._use_cache,
                                                     self._allow_cache_updates)
        self._clf = SKLearn(KNeighborsClassifier(5))

    def _build(self):
        train_matrix = self._extract_feature_matrix(self._train)
        validate_matrix = self._extract_feature_matrix(self._validate)
        score = self._clf.train(train_matrix, validate_matrix)
        self._training_scores.append({self._clf.get_name(): score})

    def _classify(self, twitter_user):
        feature_vector = np.array([self._tweet_interaction_behavior.extract_for(twitter_user, self._use_cache)])
        hashtag_similarity = self._hashtag_similarity.extract_for(twitter_user, self._use_cache)
        np.append(feature_vector, hashtag_similarity)
        return self._clf.classify(feature_vector)

    def _extract_feature_matrix(self, sample_set):
        feature_vectors = []
        for sample in tqdm(sample_set):
            feature_vec = np.array([self._tweet_interaction_behavior.extract_for(sample, self._use_cache)])
            hashtag_similarity = self._hashtag_similarity.extract_for(sample, self._use_cache)
            np.append(feature_vec, hashtag_similarity)
            feature_vec = np.append(feature_vec, (1 if sample["is_swiss"] else 0))
            feature_vectors.append(feature_vec)
        return np.array(feature_vectors)
