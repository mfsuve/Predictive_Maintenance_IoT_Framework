import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Test

from sklearn import metrics

class TestModel(Test):
    def __init__(self, *args):
        super().__init__(*args)

    # ! Burada train ve test için aynı anda bakarsan 2 tane, 2.si processing'de kalıyor
    # TODO: Kontrol et!
    def function(self, X, y, model, metric):
        print('Testing model', f'X.shape: {X.shape}', f'y_true.shape: {y.shape}')
        y_pred = model.predict(X)
        if metric == 'accuracy':
            result = metrics.accuracy_score(y, y_pred)
        else:
            result = getattr(metrics, f'{metric}_score')(y, y_pred, average=None)
            
        print(f'test model will return:' f'{metric.title()}: {result}')   
        
        return f'{metric.title()}: {result}'
    