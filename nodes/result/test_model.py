import pandas as pd
import sys
import json
import numpy as np
np.seterr(all='raise')

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config
from utils.io import InputType

# from sklearn import metrics
from collections import defaultdict

class TestModel(Node):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status('Model: None')
        self.total_tested = 0
        
    
    def first_called(self, data, accuracy, precision, recall, f1, resetAfterTraining):
        self.config = Config()
        self.model = None
        predictions = self.config.predictions()
        names = self.config.names()
        self.metrics = []
        if accuracy:
            A = RunningAccuracy()
            self.metrics.append(A)
        if precision:
            P = RunningPrecision(predictions, names)
            self.metrics.append(P)
        if recall:
            R = RunningRecall(predictions, names)
            self.metrics.append(R)
        if f1:
            F = RunningF1(predictions, names,
                          P if precision else None,
                          R if recall else None)
            self.metrics.append(F)
    
    
    def function(self, data, accuracy, precision, recall, f1, resetAfterTraining):
        
        if data.type != InputType.DATA and data.type != InputType.MODEL:
            raise ValueError(f"Input needs to be a 'data' or a 'model' but got '{data.type.name.lower()}'")
        
        if data.type == InputType.MODEL:
            self.model, _ = data.get()
            self.status(f'Model: {self.model.name}')
            self.done()
            # Resetting all the metrics since a new version of the model has come
            if resetAfterTraining:
                for metric in self.metrics:
                    metric.reset()
                self.total_tested = 0
                self.send_nodered({'reset': True}) # To reset the training plots
        elif self.model is not None:
            X, y = data.get()
            assert isinstance(X, pd.DataFrame) and isinstance(y, pd.Series)
            
            print('Testing model', f'X.shape: {X.shape}', f'y_true.shape: {y.shape if y is not None else "None"}')
            y_pred = self.model.predict(X)
            
            msg = {'predictions': self.config.convert_to_names(y_pred),
                   'classes': self.config.names(),
                   'pred_label': y_pred}
            
            if y is not None:
                msg['ground_truth'] = self.config.convert_to_names(y)
                self.total_tested += y.size
                for metric in self.metrics:
                    msg[metric.name] = metric.formatted_score(y, y_pred)

            msg['total_tested'] = self.total_tested

            self.send_nodered(msg)
            self.done()
        else:
            self.warning('There is no model to test')


class RunningAccuracy:
    
    def __init__(self):
        self.reset()
        self.name = 'accuracy'
    
    def score(self, y, y_pred):
        self.correct += (y == y_pred).sum()
        self.count += y.size
        if self.count == 0:
            return 0
        else:
            return self.correct / self.count
    
    def reset(self):
        self.correct = 0
        self.count = 0
        
    def formatted_score(self, y, y_pred):
        return self.score(y, y_pred)


class RunningPrecision:
    
    def __init__(self, labels, names):
        self.labels = labels
        self.names = names
        self.metrics = defaultdict(RunningAccuracy)
        self.name = 'precision'
        self.results = [0] * len(labels)
    
    def score(self, y=None, y_pred=None):
        # In case it is called from RunningF1
        if y is not None:
            self.results = []
            for label in self.labels:
                pred_idx = y_pred == label
                self.results.append(self.metrics[label].score(y[pred_idx], y_pred[pred_idx]))
            self.results = np.array(self.results)
        return self.results
    
    def reset(self):
        for label in self.labels:
            self.metrics[label].reset()
        
    def formatted_score(self, y, y_pred):
        return dict(zip(self.names, self.score(y, y_pred)))


class RunningRecall:
    
    def __init__(self, labels, names):
        self.labels = labels
        self.names = names
        self.metrics = defaultdict(RunningAccuracy)
        self.name = 'recall'
        self.results = [0] * len(labels)
    
    def score(self, y=None, y_pred=None):
        # In case it is called from RunningF1
        if y is not None:
            self.results = []
            for label in self.labels:
                pred_idx = y == label
                self.results.append(self.metrics[label].score(y[pred_idx], y_pred[pred_idx]))
            self.results = np.array(self.results)
        return self.results
    
    def reset(self):
        for label in self.labels:
            self.metrics[label].reset()
        
    def formatted_score(self, y, y_pred):
        return dict(zip(self.names, self.score(y, y_pred)))


class ReusableMetric:
    def __init__(self, m):
        self.m = m
    def score(self, *args): # Do not calculate it again (for f1)
        return self.m.score()
    def reset(self): # When one metric out of 4 reset, it is guaranteed that all will reset, no need to reset it again
        pass


class RunningF1:
        
    def __init__(self, labels, names, running_precision, running_recall):
        self.labels = labels
        self.names = names
        self.name = 'f1_score'
        self.precision = RunningPrecision(labels, names) if running_precision is None else ReusableMetric(running_precision)
        self.recall = RunningRecall(labels, names) if running_recall is None else ReusableMetric(running_recall)
    
    def score(self, y, y_pred):
        '''This should be called after score functions of RunningPrecision and RunningRecall'''
        P = self.precision.score(y, y_pred)
        R = self.recall.score(y, y_pred)
        a = (2 * P * R)
        b = (P + R)
        return np.divide(a, b, out=np.zeros_like(a), where=b!=0)

    def reset(self):
        self.precision.reset()
        self.recall.reset()
        
    def formatted_score(self, y, y_pred):
        return dict(zip(self.names, self.score(y, y_pred)))
