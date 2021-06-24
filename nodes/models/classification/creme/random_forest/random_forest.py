from utils.utils import myprint as print
from river import ensemble
from nodes.models.classification.creme.creme_model import CremeModel

class RandomForest(CremeModel):
    
    def __init__(self, *args):
        super().__init__(*args, model=ensemble.AdaptiveRandomForestClassifier(split_criterion='gini', max_depth=16))
