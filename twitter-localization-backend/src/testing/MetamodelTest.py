import numpy as np

from src.knowledgegraph.KnowledgeGraph import KnowledgeGraph
from src.localization import TrainValidateTestProvider
from src.util import timing
from tqdm import tqdm


class MetamodelTest:

    def __init__(self, metamodel):
        self._metamodel = metamodel
        self._graph = KnowledgeGraph()
        train, validate, test = TrainValidateTestProvider.get_data()
        self._test_set = test

    def test(self, remove_graph_traces=True):
        """
        Builds the meta-model passed to this instance, and evaluates its performance on the test set.
        Returns a dictionary containing the meta-model's performance in terms its confusion matrix,precision,
        recall, and F-measure. The confusion matrix is given in the following form:
        -----------
        | TP | FN |
        -----------
        | FP | TN |
        -----------
        Columns represent the predicted class (swiss, non-swiss), rows represent the state-of-nature. The
        F-measure is defined as (2 * precision * recall)/(precision + recall).
        :remove_graph_traces:   if true, all nodes and edges created in the grap during this model run will be
                                removed before this function returns. Defaults to True.
        :return:                dictionary with measurements of the meta-model's performance
        """
        print(timing.get_timestamp() + ": MetamodelTest: testing metamodel " + self._metamodel.get_model_instance_id())
        self._metamodel.build()
        self._run_metamodel_on_test_set()
        user_results = self._collect_user_results()
        c_matrix = self._calculate_confusion_matrix(user_results)
        accuracy = MetamodelTest._calculate_accuracy(c_matrix)
        precision = MetamodelTest._calculate_precision(c_matrix)
        recall = MetamodelTest._calculate_recall(c_matrix)
        f_measure = MetamodelTest._calculate_f_measure(precision, recall)
        confidence_performance = MetamodelTest._evaluate_confidence(user_results)
        if remove_graph_traces:
            self._metamodel.cleanup(keep_final=False)
        return {
            "model_performance": {
                "confusion": c_matrix, "accuracy": accuracy, "precision": precision, "recall": recall, "F": f_measure
            },
            "confidence_performance": confidence_performance
        }

    def _collect_user_results(self):
        results = []
        for test_user in self._test_set:
            res = self._graph.fetch_final_decision_for_user(test_user["id"], self._metamodel.get_model_instance_id())
            localized_swiss, confidence = res
            user_result = {
                "user_id": test_user["id"],
                "is_swiss": test_user["is_swiss"],
                "correctly_classified": MetamodelTest._is_correctly_classified(test_user, localized_swiss),
                "confidence": confidence
            }
            results.append(user_result)
        return results

    @staticmethod
    def _is_correctly_classified(user, localized_swiss):
        return (user["is_swiss"] and localized_swiss) or (not user["is_swiss"] and not localized_swiss)

    def _run_metamodel_on_test_set(self):
        for test_user in tqdm(self._test_set):
            self._metamodel.classify(test_user["screen_name"])

    @staticmethod
    def _calculate_confusion_matrix(user_results):
        c_mat = np.array([[0, 0], [0, 0]])
        for user_result in user_results:
            is_swiss = user_result["is_swiss"]
            correctly_classified = user_result["correctly_classified"]
            if is_swiss and correctly_classified:
                c_mat[0, 0] += 1  # true positive
            elif is_swiss and not correctly_classified:
                c_mat[0, 1] += 1  # false negative
            elif not is_swiss and not correctly_classified:
                c_mat[1, 0] += 1  # false positive
            else:  # not is swiss and correctly_classified
                c_mat[1, 1] += 1  # true negative
        return c_mat

    @staticmethod
    def _calculate_accuracy(confusion_matrix):
        total_samples = confusion_matrix[0, 0] + confusion_matrix[0, 1] + \
                        confusion_matrix[1, 0] + confusion_matrix[1, 1]
        correct_samples = confusion_matrix[0, 0] + confusion_matrix[1, 1]
        if total_samples == 0:
            return 0
        return correct_samples / total_samples

    @staticmethod
    def _calculate_precision(confusion_matrix):
        divisor = (confusion_matrix[0, 0] + confusion_matrix[1, 0])
        if divisor == 0:
            return 0
        return confusion_matrix[0, 0] / divisor

    @staticmethod
    def _calculate_recall(confusion_matrix):
        divisor = (confusion_matrix[0, 0] + confusion_matrix[0, 1])
        if divisor == 0:
            return 0
        return confusion_matrix[0, 0] / divisor

    @staticmethod
    def _calculate_f_measure(precision, recall):
        divisor = (precision+recall)
        if divisor == 0:
            return 0
        return (2.0*precision*recall) / divisor

    @staticmethod
    def _evaluate_confidence(user_results):
        correct_confidences = [res["confidence"] for res in user_results if res["correctly_classified"]]
        incorrect_confidences = [res["confidence"] for res in user_results if not res["correctly_classified"]]
        result = {
            "correctly_classified": {
                "min": min(correct_confidences),
                "max": max(correct_confidences),
                "mean": (sum(correct_confidences) / len(correct_confidences))
            },
            "incorrectly_classified": {
                "min": min(incorrect_confidences),
                "max": max(incorrect_confidences),
                "mean": (sum(incorrect_confidences) / len(incorrect_confidences))
            },
            "confidence_performance_index": MetamodelTest._calculate_cpi(user_results)
        }
        return result

    @staticmethod
    def _calculate_cpi(user_results):
        n = len(user_results)
        sum_cpi = 0
        for res in user_results:
            mapped_confidence = MetamodelTest._map_to_0_1(res["confidence"])
            if res["correctly_classified"]:
                sum_cpi += mapped_confidence
            else:
                sum_cpi += (1-mapped_confidence)
        return sum_cpi / n

    @staticmethod
    def _map_to_0_1(value):
        return 2 * (value - 0.5)
