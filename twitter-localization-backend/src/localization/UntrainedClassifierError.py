class UntrainedClassifierError(Exception):
    def __init__(self, classifier_name):
        super().__init__("Classification request on untrained classifier {}".format(classifier_name))
