from numpy.core.fromnumeric import shape
from sklearn.utils import shuffle
from utils.utils import myprint as print
from utils.node import Model
from creme import metrics
from creme import stream
# from creme import imblearn # TODO: After pypi release of river (aka. creme)
from utils.io import InputType
from utils.config import Config
import numpy as np
import pandas as pd

class CremeModel(Model):
    
    def __init__(self, *args, model):
        super().__init__(*args)
        # self.hard_sample = self.node_config['hardSample'] # TODO: After pypi release of river (aka. creme)
        if 'loadFrom' in self.node_config:
            self.load(self.node_config['loadFrom'])
        else:
            self.model = model
            # if self.hard_sample: # TODO: After pypi release of river (aka. creme)
                # TODO: DO Hard Sampling here
        self.metric = metrics.Accuracy()
        self.count = 0
        self.status(f'Trained with {self.count} data')
    #     self.is_binary = is_binary
        
    # def first_called(self, *args, **kwargs):
    #     self.config = Config()
    #     self.predictions = self.config.predictions()
        
    # def function(self, data, hardSample, loadFrom=None): # TODO: After pypi release of river (aka. creme)
    def function(self, data, loadFrom=None):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        assert isinstance(X, pd.DataFrame) and isinstance(y, pd.Series)
        
        # if self.is_binary:
        #     if self.config.num_classes != 2:
        #         raise ValueError(f"{self.name} only works with binary classification but got data with {self.config.num_classes} classes")
        #     # LogisticRegression asks for True and False as labels
        #     # I know it is binary, so I take the first possible prediction
        #     # and I convert it to True in y and make the rest False
        #     y = y == self.predictions[0]
            
        # print(f"Creme\nX.columns:", X.columns, f"X.shape: {X.shape}", f"Classes: {y.unique()}", f"type(X): {type(X)}", f"type(y): {type(y)}")
        
        acc_values = []
        y_preds = []
        for i, (_X, _y) in enumerate(stream.iter_pandas(X, y, shuffle=True)):
            # print('Creme', f"{i}. iteration", "_X:", _X, "_y:", _y)
            y_pred = self.model.predict_one(_X)
            if y_pred is not None:
                y_preds.append(y_pred)
            # print('In train | y_pred:', y_pred)
            # if _y != y_pred:
                # print(f'Creme | _y: {_y}, y_pred: {y_pred} at iteration {i}')
            acc_values.append(self.metric.update(_y, y_pred).get())
            self.model.fit_one(_X, _y)
            
        # print(f'Creme | y ones: {y.sum()}, y_pred ones: {sum(y_preds)} with {len(y)} data')
        
        # y_pred = self.model.predict_many(X)
        # self.metric = self.metric.update(y, y_pred)
        # self.model = self.model.fit_many(X, y)
        self.count += X.shape[0]
        
        self.send_nodered(None, {'accuracy': acc_values, 'num_data': self.count})
        self.send_next_node((self, False))
        self.status(f'Trained with {self.count} data')
        
    def predict(self, X):
        y_pred = np.array([
            self.model.predict_one(_X)
            for _X, _ in stream.iter_pandas(X, shuffle=True)
        ])
        # if self.is_binary:
        #     return np.where(y_pred, self.predictions[0], self.predictions[1])
        # else:
        return y_pred
    
    def save(self, folder, prefix, obj=None):
        obj = {
            'model': self.model
            # 'hard_sample': self.hard_sample # TODO: After pypi release of river (aka. creme)
        }
        super().save(folder, prefix, obj)
        
    def load(self, path):
        # check = {
        #     'hard_sample': 'hard sampling'
        # } # TODO: After pypi release of river (aka. creme)
        # obj = super().load(path, check) # TODO: After pypi release of river (aka. creme)
        obj = super().load(path)
        self.model = obj['model']
        # self.hard_sample = obj['hard_sample'] # TODO: After pypi release of river (aka. creme)
        self.send_next_node((self, True))
