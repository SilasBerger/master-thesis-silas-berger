from src.localization.metamodels.FeatureCombination4 import FeatureCombination4
from src.localization.metamodels.FeatureCombination5 import FeatureCombination5
from src.util import context
from src.testing.MetamodelTest import MetamodelTest


def try_model():
    context.load_credentials()
    context.load_config()
    metamodel = FeatureCombination4(use_cache=True, allow_cache_updates=True)
    train_scores = metamodel.build()
    print(train_scores)


def run_evaluation():
    context.load_credentials()
    context.load_config()
    mmodel = FeatureCombination4()
    test = MetamodelTest(mmodel)
    score = test.test(remove_graph_traces=False)
    print(score)


if __name__ == "__main__":
    run_evaluation()
