from utils.utils import myprint as print
from river import ensemble
from nodes.models.classification.creme.creme_model import CremeModel

class RandomForest(CremeModel):
    
    def __init__(self, *args):
        super().__init__(*args)
        max_features = self.node_config['maxFeatures']
        if max_features == "None":
            max_features = None
        if self.node_config['unlimitedDepth']:
            max_depth = None
        else:
            max_depth = self.node_config['maxDepth']
        self.set_model(
            ensemble.AdaptiveRandomForestClassifier(
                split_criterion='gini',
                max_depth=max_depth,
                max_features=max_features,
                n_models=self.node_config['numModels']
            )
        )
