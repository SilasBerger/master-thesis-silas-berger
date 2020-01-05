class MetamodelNotReadyError(Exception):
    def __init__(self, model_id):
        super().__init__("Model {} not ready, call build() first".format(model_id))
