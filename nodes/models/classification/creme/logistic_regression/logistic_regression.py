from utils.utils import myprint as print
from river import linear_model, multiclass
from nodes.models.classification.creme.creme_model import CremeModel

class LogisticRegression(CremeModel):
    
    def __init__(self, *args):
        super().__init__(*args)
        print(f"LogisticRegression | node_config:", self.node_config)
        if self.node_config.get('multiclass', 'ovo') == 'ovo':
            model = multiclass.OneVsOneClassifier(linear_model.LogisticRegression())
        else:
            model = multiclass.OneVsRestClassifier(linear_model.LogisticRegression())
        self.set_model(model)
