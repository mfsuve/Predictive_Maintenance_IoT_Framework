from utils.utils import myprint as print
from river import linear_model
from nodes.models.classification.creme.creme_model import CremeModel

class LogisticRegression(CremeModel):
    
    def __init__(self, *args):
        super().__init__(*args, model=linear_model.LogisticRegression())
