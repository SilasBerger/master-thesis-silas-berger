from src.localization.metamodels.FeatureCombination4 import FeatureCombination4
from src.util import context
from src.localization.metamodels.SimpleInfluencerFollowedRatio import SimpleInfluencerFollowedRatio
from src.localization.metamodels.SimpleSwissTweetInteraction import SimpleSwissTweetInteraction
from src.localization import TrainValidateTestProvider
from src.localization.Database import Database


def run():
    context.load_credentials()
    context.load_config()
    model = FeatureCombination4()
    scores = model.build()
    print("\nModel complete")
    print("Classifier validation scores:")
    print(scores)
    # _localize_new_users(model)
    _localize_all_test_users(model)


def _localize_new_users(model):
    print("\n\n=== Ready to localize new users ===")
    done = False
    while not done:
        value = input("Enter a Twitter screen name to localize the user ('exit' to exit): ")
        if value.lower() == "exit":
            done = True
            continue
        p_class, conf = model.classify(value)
        print("-> user {} is {}, confidence = {}".format(value, "swiss" if p_class == 1 else "not swiss", conf))
    print("Goodbye!")


def _localize_all_test_users(model):
    train, val, test = TrainValidateTestProvider.get_data()
    for user in test:
        screen_name = user["screen_name"]
        p_class, conf = model.classify(screen_name)
        print("-> user {} is {}, confidence = {}".format(screen_name, "swiss" if p_class == 1 else "not swiss", conf))
    pass


if __name__ == "__main__":
    run()
