from src.localization.UntrainedClassifierError import UntrainedClassifierError


class Classifier:
    """
    add doc
    """

    def __init__(self, classifier_name):
        self._is_trained = False
        self._classifier_name = classifier_name

    def train(self, training_set, validation_set):
        """
        Train this classifier on a given training set, retrieve a performance score on the validation set.
        :param training_set:    2-dimensional numpy-array with samples as row vectors, true class in the last column
        :param validation_set:  2-dimensional numpy-array with samples as row vectors, true class in the last column
        :return:                validation performance score (int, float); currently arbitrary depending on the
                                classifier, can be negative
        """
        score = self._train(training_set, validation_set)
        assert isinstance(score, int) or isinstance(score, float)  # TODO normalize score, to work with SKLearn's definition
        self._is_trained = True
        return score

    def classify(self, sample):
        """
        Classifies a given sample into 1 (positive) and 0 (negative)
        :param sample:  1-dimensional numpy array
        :return:        class (1 (positive) or 0 (negative)), confidence ([0.5, 1])
        :raises UntrainedClassifierError: if this function is called before the classifier has been trained
        """
        if not self._is_trained:
            raise UntrainedClassifierError(self._classifier_name)
        predicted_class, confidence = self._classify(sample)
        return predicted_class, confidence

    def get_name(self):
        return self._classifier_name

    def _classify(self, sample):
        raise NotImplementedError("function _classify() is abstract in Classifier")

    def _train(self, training_set, validation_set):
        raise NotImplementedError("function _train() is abstract in Classifier")
