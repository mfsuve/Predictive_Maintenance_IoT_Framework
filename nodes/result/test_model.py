import pandas as pd
import os
import json
import numpy as np
np.seterr(all='raise')

from utils.utils import myprint as print
from utils.node import Model, Node
from utils.config import Config
from utils.io import Input, InputType

# from sklearn import metrics
from collections import defaultdict
import pickle

class TestModel(Node):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status('Model: None')
        self.total_tested = 0
        self.metric_save_file = self.node_config.get('metricSaveFile', None)        
        self.metric_values_to_plot = defaultdict(list)
        
    
    def first_called(self, data:Input, accuracy, precision, recall, f1, *args, **kwargs):
        config:Config
        _, _, _, config = data.get()
        self.model:Model = None
        predictions = config.predictions()
        names = config.names()
        self.metrics = []
        if accuracy:
            A = RunningAccuracy()
            self.metrics.append(A)
        if precision:
            P = RunningPrecision(predictions, names)
            self.metrics.append(P)
        else:
            P = None
        if recall:
            R = RunningRecall(predictions, names)
            self.metrics.append(R)
        else:
            R = None
        if f1:
            F = RunningF1(predictions, names, P, R)
            self.metrics.append(F)
            
    
    def clear_from_nan_target(self, X:pd.DataFrame, y:pd.Series):
        if y is None:
            return X, y
        target_not_nan = y.notna()
        if not target_not_nan.any():
            return X, None
        return X[target_not_nan], y[target_not_nan]
        
    
    
    def function(self, data:Input, accuracy, precision, recall, f1, resetAfterTraining, ignoreNanTarget, *args, **kwargs):
        
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
            config:Config
            X, y, encoded, config = data.get()
            assert isinstance(X, pd.DataFrame) and (y is None or isinstance(y, pd.Series))
            
            if ignoreNanTarget:
                X, y = self.clear_from_nan_target(X, y)
            elif y.isna().any():
                raise ValueError(f'There is data point with missing class. Please either remove them or choose "If there is any data point with labels, ignore the ones without" option.')
            
            print('Testing model', f'X.shape: {X.shape}', f'y_true.shape: {y.shape if y is not None else "None"}')
            y_pred = self.model.predict(X)
            
            msg = {'predictions': config.convert_to_names(y_pred),
                   'classes': config.names(),
                   'pred_label': y_pred}
            
            if y is not None:
                msg['ground_truth'] = config.convert_to_names(y)
                self.total_tested += y.size
                # print(f"Test Model | metric names")
                for metric in self.metrics:
                    # print('Test Model | ', type(metric), metric.name)
                    # msg[metric.name] = metric.formatted_score(y, y_pred)
                    score = metric.formatted_score(y, y_pred)
                    msg[metric.name] = score
                    if isinstance(score, dict):
                        self.metric_values_to_plot[metric.name].append(dict(score, total_tested=self.total_tested))
                    else:
                        self.metric_values_to_plot[metric.name].append(dict(accuracy=score, total_tested=self.total_tested))
                if self.metric_save_file is not None:
                    filename = os.path.join(self.metric_save_file, self.model.name, 'results.pkl')
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                    with open(filename, 'wb') as file:
                        pickle.dump(self.metric_values_to_plot, file)

            msg['total_tested'] = self.total_tested

            print('Test Model | msg:', msg)
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
                idx = y_pred == label
                self.results.append(self.metrics[label].score(y[idx], y_pred[idx]))
            self.results = np.array(self.results)
        # print(f"Precision | results:, ", self.results)
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
                idx = y == label
                self.results.append(self.metrics[label].score(y[idx], y_pred[idx]))
            self.results = np.array(self.results)
        # print(f"Recall | results:, ", self.results)
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
    
    
if __name__ == '__main__':
    y       = np.array([1, 1, 1, 1, 0, 0, 1])
    y_pred  = np.array([1, 0, 1, 0, 1, 0, 1])

    p = RunningPrecision(labels=[0, 1], names=['0', '1'])
    r = RunningRecall(labels=[0, 1], names=['0', '1'])
    
    print(p.score(y, y_pred))
    print(r.score(y, y_pred))
