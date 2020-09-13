import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config
from utils.io import InputType

from sklearn import metrics

class TestModel(Node):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.model = None
        self.config = Config()
        self.all_possible_names = self.config.names()
        self.all_possible_predictions = self.config.predictions()
        

    def function(self, data, accuracy, precision, recall, f1):
        
        if data.type != InputType.DATA and data.type != InputType.MODEL:
            raise ValueError(f"Input needs to be a 'data' or a 'model' bu got '{data.type.name.lower()}'")
        
        if data.type == InputType.MODEL:
            self.model, _ = data.output
            self.status(f'Model: {self.model.name}')
        elif self.model is not None:
            X, y = data.output
            print('Testing model', f'X.shape: {X.shape}', f'y_true.shape: {y.shape}')
            y_pred = self.model.predict(X.to_numpy())
            
            msg = {'predictions': self.config.convert_to_names(y_pred),
                   'ground_truth': self.config.convert_to_names(y),
                   'classes': self.all_possible_names}
            
            # ? Burda datayı biraz biriktir sonra tahmin yap, ne kadar birikeceğini de sor.
            if y is not None:
                if accuracy:
                    msg['accuracy'] = metrics.accuracy_score(y, y_pred)
                if precision:
                    precision_score = metrics.precision_score(y, y_pred, average=None, labels=self.all_possible_predictions)
                    msg['precision'] = dict(zip(self.all_possible_names, precision_score))
                if recall:
                    recall_score = metrics.recall_score(y, y_pred, average=None, labels=self.all_possible_predictions)
                    msg['recall'] = dict(zip(self.all_possible_names, recall_score))
                if f1:
                    f1_score = metrics.f1_score(y, y_pred, average=None, labels=self.all_possible_predictions)
                    msg['f1_score'] = dict(zip(self.all_possible_names, f1_score))
        
            self.send_nodered(msg)
        else:
            self.status('Model: None')
    