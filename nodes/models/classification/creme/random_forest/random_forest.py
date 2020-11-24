from utils.utils import myprint as print
from creme import tree
from nodes.models.classification.creme.creme_model import CremeModel

class RandomForest(CremeModel):
    
    def __init__(self, *args):
        super().__init__(*args, model=tree.RandomForestClassifier())
