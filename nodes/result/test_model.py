import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config

from sklearn import metrics

class TestModel(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.model = None
        self.config = Config()
        

    def function(self, data, accuracy, precision, recall, f1):
        
        if data.type != Node.Type.DATA and data.type != Node.Type.MODEL:
            raise ValueError(f"Input needs to be a 'data' or a 'model' bu got '{data.type.name.lower()}'")
        
        if data.type == Node.Type.MODEL:
            self.model = data.output
            self.status(f'Model: {self.model.name}')
        elif self.model is not None:
            X, y = data.output
            if y is None:
                raise ValueError("To test the model, input data has to have a target")
            print('Testing model', f'X.shape: {X.shape}', f'y_true.shape: {y.shape}')
            y_pred = self.model.predict(X.to_numpy())
            
            msg = {'predictions': self.config.names(y_pred),
                   'ground_truth': self.config.names(y)}                # TODO: nodered'de dene hata var mı bak, ground truth'u göster dashboard'da.
            if accuracy:                                                # TODO: Burda datayı biraz biriktir et sonra tahmin yap, ne kadar birikeceğini de sor.
                msg['accuracy'] = metrics.accuracy_score(y, y_pred)
            if precision:
                msg['precision'] = metrics.precision_score(y, y_pred, average=None)
            if recall:
                msg['recall'] = metrics.recall_score(y, y_pred, average=None)
            if f1:
                msg['f1_score'] = metrics.f1_score(y, y_pred, average=None)
        
            self.send_nodered(msg)
        else:
            self.status('Model: None')
    