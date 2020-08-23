import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config

from sklearn import metrics

# TODO: Bunun farklı yerlerden gelebilecek inputları handle edebilecek şekilde tamamlanması lazım.
# TODO: Ama ondan önce Flexsim kısmındaki breakdown simulation ve NodeRed'den gelen datayı kullanarak breakdown'ların zamanını belirleme kısmı yapılacak
class TestModel(Node):
    def __init__(self, *args):
        super().__init__(*args)

        if data.type != Node.Type.DATA and data.type != Node.Type.MODEL:
            raise ValueError(f"Input needs to be a 'data' or a 'model' bu got '{data.type.name.lower()}'")
        y_pred = model.predict(X)
        if metric == 'accuracy':
            result = metrics.accuracy_score(y, y_pred)
        else:
            result = getattr(metrics, f'{metric}_score')(y, y_pred, average=None)
            
        print(f'test model will return:' f'{metric.title()}: {result}')   
        
        return f'{metric.title()}: {result}'
    