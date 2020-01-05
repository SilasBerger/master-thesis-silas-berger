from src.localization.Classifier import Classifier
from sklearn.neighbors import KNeighborsClassifier


class SKLearn(Classifier):
    """
    add doc
    """

    def __init__(self, sklearn_clf=None):
        super().__init__("SKLearn")
        if sklearn_clf is None:
            self._clf = KNeighborsClassifier(3)
        else:
            self._clf = sklearn_clf

    def _train(self, training_set, validation_set):
        train_x = training_set[:, :-1]
        train_y = training_set[:, -1:].flatten()
        val_x = validation_set[:, :-1]
        val_y = validation_set[:, -1:].flatten()
        self._clf.fit(train_x, train_y)
        return self._clf.score(val_x, val_y)

    def _classify(self, sample):
        n_sample = sample.reshape(1, -1)
        prediction = self._clf.predict_proba(n_sample)
        predicted_class = prediction.argmax()
        confidence = prediction[0][predicted_class]
        return predicted_class, confidence

    def set_classifier(self, sklearn_classifier_instance):
        """
        Set the SKLearn classifier to be used. After this function is called, the classifier needs to be retrained
        (train()) before classify() can be called again.
        :param sklearn_classifier_instance: an instance of an SKLearn classifier
        :return: None
        """
        self._clf = sklearn_classifier_instance
        self._is_trained = False
