from river import naive_bayes
from nodes.models.classification.creme.creme_model import CremeModel

class GaussianNaiveBayes(CremeModel):
    
    def __init__(self, *args):
        super().__init__(*args, model=naive_bayes.GaussianNB())
