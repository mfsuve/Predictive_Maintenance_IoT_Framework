import pandas as pd
import sys

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = Node.Type.DATA
        self.min = None
        self.range = None

    def function(self, data):
        if data.type != Node.Type.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        print(f'MinMax Scaling...')
        
        X, y = data.output
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
        # !! Burası datayı spamlayınca hata atıyor !!
        assert ((0 <= X[self.min.keys()]) & (X[self.min.keys()] <= 1)).all().all()
        
        self.send_next_node((X, y))
        self.done()


class StandardScaler(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = Node.Type.DATA

    def function(self, X, y):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y