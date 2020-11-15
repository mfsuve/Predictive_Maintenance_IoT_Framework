import pandas as pd
import sys

from utils.utils import myprint as print
from utils.node import Data
from utils.config import Config
from utils.io import InputType

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.min = None
        self.range = None

    def function(self, data):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        print(f'MinMax Scaling...')
        
        X, y = data.get()
        
        if (X.dtypes == 'object').any() or y.dtype == 'object':
            raise ValueError(f"Data needs to contain only numerical values in order to be scaled, but there are non numeric values in the data.")
        
        if self.min is None:
            print('Scaler | self.min is None!')
            config = Config()
            m = pd.Series()
            M = pd.Series()
            for col in X.columns:
                if not config.is_categoric(col):
                    m[col] = config.min(col)
                    M[col] = config.max(col)
            self.min = m
            self.range = M - m
            
        print('Scaler min', self.min)
        
        X[self.min.keys()] = (X[self.min.keys()] - self.min) / self.range
        
        print('Scaled min:', X.min())
        print('Scaled max:', X.max())
        
        # TODO: Might delete this later for performance
        # * Assure that all the values are in [0, 1]
        assert ((0 <= X[self.min.keys()]) & (X[self.min.keys()] <= 1)).all().all()
        
        self.send_next_node((X, y))
        self.done()


class StandardScaler(Data):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = InputType.DATA

    def function(self, X, y):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y