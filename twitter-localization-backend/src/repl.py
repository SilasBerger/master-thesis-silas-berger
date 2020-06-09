from src.localization.metamodels.FeatureCombination4 import FeatureCombination4
from src.localization.metamodels.FeatureCombination5 import FeatureCombination5
from src.util import context, timing


def main():
    # Load all relevant contexts.
    context.load_credentials()
    context.load_config()

    # Specify which metamodel to use, and build it.
    metamodel = FeatureCombination4(use_cache=True, allow_cache_updates=True)
    metamodel.build()

    # Use the metamodel in a REPL loop.
    repl(metamodel)


def repl(metamodel):
    while True:
        screen_name = input("\nLocalize by screen name ('q' to quit): @")
        if screen_name.lower() == "q":
            print("Bye.")
            break
        (is_swiss, confidence) = metamodel.classify(screen_name)
        if is_swiss is None:
            print("{}: @{} not found on Twitter".format(timing.get_timestamp(), screen_name))
            continue
        print("{}: @{} is swiss: {} (confidence: {})".format(timing.get_timestamp(),
                                                             screen_name,
                                                             "true" if is_swiss else "false",
                                                             confidence))


if __name__ == "__main__":
    main()
