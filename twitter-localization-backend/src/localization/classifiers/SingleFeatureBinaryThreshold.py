from src.localization.Classifier import Classifier
import numpy as np


class SingleFeatureBinaryThreshold(Classifier):
    """
    add doc
    """

    def __init__(self):
        super().__init__("SingleFeatureBinaryThreshold")
        self._positive_avg = 0
        self._negative_avg = 0
        self._delta_positive_negative = 0
        self._prior_positive = 0
        self._prior_negative = 0
        self._lower_average = 0
        self._upper_average = 0

    def _train(self, training_set, validation_set):
        num_training_samples = training_set.shape[0]
        positives = []
        negatives = []
        for i in range(0, num_training_samples):
            if training_set[i, -1] == 1:
                positives.append(training_set[i, 0])
            else:
                negatives.append(training_set[i, 0])
        self._positive_avg = np.array(positives).sum() / len(positives)
        self._negative_avg = np.array(negatives).sum() / len(negatives)
        self._delta_positive_negative = abs(self._positive_avg - self._negative_avg)
        self._prior_positive = len(positives) / num_training_samples
        self._prior_negative = len(negatives) / num_training_samples
        self._lower_average = min(self._positive_avg, self._negative_avg)
        self._upper_average = max(self._positive_avg, self._negative_avg)
        return self._calculate_score(validation_set)

    def _classify(self, sample):
        delta_positive = abs(sample[0] - self._positive_avg)
        delta_negative = abs(sample[0] - self._negative_avg)
        predicted_class = self._predict_class(delta_positive, delta_negative)
        confidence = self._calculate_confidence(sample, delta_positive, delta_negative)
        return predicted_class, confidence

    def _predict_class(self, delta_positive, delta_negative):
        if delta_positive < delta_negative:
            return 1
        elif delta_negative < delta_positive:
            return 0
        else:
            return self._break_tie()

    def _calculate_confidence(self, sample, delta_positive, delta_negative):
        if self._delta_positive_negative == 0:
            return 0.5  # guard against cases where positive and negative average are equal
        p_delta_pos = delta_positive / self._delta_positive_negative
        p_delta_neg = delta_negative / self._delta_positive_negative
        winning_p_delta = max(p_delta_pos, p_delta_neg)
        return min(winning_p_delta, 1)

    def _break_tie(self):
        if self._prior_positive >= self._prior_negative:
            return 1
        elif self._prior_negative > self._prior_positive:
            return 0

    def _calculate_score(self, validation_set):
        total_samples = validation_set.shape[0]
        num_correct = 0
        for i in range(0, total_samples):
            sample = validation_set[i]
            true_class = sample[-1]
            predicted_class, confidence = self._classify(sample[0:1])
            if true_class == predicted_class:
                num_correct += 1
        return num_correct / total_samples
