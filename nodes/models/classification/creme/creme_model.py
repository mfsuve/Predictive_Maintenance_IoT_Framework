import threading
from utils.utils import myprint as print
from utils.node import Model
from river import metrics
from river import stream
from utils.io import Input, InputType
from utils.config import Config
import numpy as np
import pandas as pd
from copy import deepcopy


# TODO: Modellere parametre verilebilmesini sağla
# TODO: Model parametrelerinin disk'ten model load edildiğinde de tutmasını kontrol et
# TODO: Tutmuyorsa da override edilecek de (force=False, check={var_name, description} şeklinde kullanabilirsin load ve save node'unda)

class CremeModel(Model):
    
    lock = threading.Lock()
    
    def __init__(self, *args):
        super().__init__(*args)
        self.metric = metrics.Accuracy()
        self.count = 0
        self.status(f'Trained with {self.count} data')
        self.next_propagate = 1
        
    def set_model(self, model):
        # TODO: Model loading'i test et
        if 'loadFrom' in self.node_config:
            self.load(self.node_config['loadFrom'])
        else:
            self.model = model
        
    def function(self, data:Input, propagateMode, propagateAfter, *args, **kwargs):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y, _, config = data.get()
        assert isinstance(X, pd.DataFrame) and isinstance(y, pd.Series)
        
        if X.empty:
            print(f"Empty data in {self.name}")
            return
        
        with CremeModel.lock:
            acc_values = []
            for _X, _y in stream.iter_pandas(X, y, shuffle=True):
                try:
                    y_pred = self.model.predict_one(_X)
                except TypeError:
                    print(f"{self.name} | TypeError:", '_X', _X, 'X', X)
                    raise
                acc_values.append(self.metric.update(_y, y_pred).get())
                self.model.learn_one(_X, _y)
            
        self.count += X.shape[0]
        
        self.send_nodered(None, {'accuracy': acc_values, 'train_title': f"Trained with {self.count} data"})
        if propagateMode == 'always' or self.count // propagateAfter >= self.next_propagate:
            self.send_next_node((self, False))
            self.done()
            self.next_propagate = (self.count // propagateAfter) + 1
        self.status(f'Trained with {self.count} data')
        
    def predict(self, X:pd.DataFrame):
        with CremeModel.lock:
            y_pred = np.array([
                self.model.predict_one(_X)
                for _X, _ in stream.iter_pandas(X.copy())
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
