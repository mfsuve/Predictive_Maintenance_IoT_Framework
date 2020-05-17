import pandas as pd
import sys
import json
import numpy as np

from utils.utils import nodered_function
from utils.utils import myprint as print

from sklearn import metrics

# TODO: Burada train ve test için aynı anda bakarsan 2 tane, 2.si processing'de kalıyor. Kontrol et!
@nodered_function(data=('X', 'y_true'), model=('model',))
def test(X, y_true, model, metric):
    print('Testing model', f'X.shape: {X.shape}', f'y_true.shape: {y_true.shape}')
    y_pred = model.predict(X)
    if metric == 'accuracy':
        result = metrics.accuracy_score(y_true, y_pred)
    else:
        result = getattr(metrics, f'{metric}_score')(y_true, y_pred, average=None)
        
    print(f'test model will return:' f'{metric.title()}: {result}')   
    
    return f'{metric.title()}: {result}'
    