import pandas as pd
import sys

from utils.utils import myprint as print
from utils.node import Data

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Data):
    def __init__(self, pool, id):
        super().__init__(pool, id)
        self.inputs = [Data]

    def function(self, X, y):
        print(f'MinMax Scaling...')
        return MMS().fit_transform(X), y

class StandardScaler(Data):
    def __init__(self, pool, id):
        super().__init__(pool, id)
        self.inputs = [Data]

    def function(self, X, y):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y