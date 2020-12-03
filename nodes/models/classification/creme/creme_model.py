from utils.utils import myprint as print
from utils.node import Model
from river import metrics
from river import stream
from utils.io import InputType
from utils.config import Config
import numpy as np
import pandas as pd
from copy import deepcopy


# TODO: Ses kaydını dinle, orada dediklerini yap
# TODO: Buraya biraz daha model ekle (river'ın documentation'unundan bak)

class CremeModel(Model):
    
    def __init__(self, *args, model):
        super().__init__(*args)
        # TODO: Model loading'i test et
        if 'loadFrom' in self.node_config:
            self.load(self.node_config['loadFrom'])
        else:
            self.model = model
        self.metric = metrics.Accuracy()
        self.count = 0
        self.status(f'Trained with {self.count} data')
        self.next_propagate = 1
        
    def function(self, data, propagateMode, propagateAfter, loadFrom=None):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        assert isinstance(X, pd.DataFrame) and isinstance(y, pd.Series)
        
        acc_values = []
        y_preds = []
        for _X, _y in stream.iter_pandas(X, y, shuffle=True):
            y_pred = self.model.predict_one(_X)
            if y_pred is not None:
                y_preds.append(y_pred)
            acc_values.append(self.metric.update(_y, y_pred).get())
            self.model.learn_one(_X, _y)
            
        self.count += X.shape[0]
        
        self.send_nodered(None, {'accuracy': acc_values, 'num_data': self.count})
        if propagateMode == 'always' or self.count // propagateAfter >= self.next_propagate:
            self.send_next_node((self, False))
            self.done()
            self.next_propagate = (self.count // propagateAfter) + 1
        self.status(f'Trained with {self.count} data')
        
    def predict(self, X):
        y_pred = np.array([
            self.model.predict_one(_X)
            for _X, _ in stream.iter_pandas(X, shuffle=True)
        ])
        return y_pred
    
    def save(self, folder, prefix, obj=None):
        obj = {
            'model': deepcopy(self.model)
        }
        super().save(folder, prefix, obj)
        
    def load(self, path):
        obj = super().load(path)
        self.model = obj['model']
        self.send_next_node((self, True))
