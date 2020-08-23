import pandas as pd
import sys
import json
import numpy as np
from abc import ABCMeta, abstractmethod

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config

from sklearn.preprocessing import LabelEncoder as LE
from collections import defaultdict

class Encoder(Node):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.type = Node.Type.DATA
        self.encoder = None


    # TODO: Sürekli gelen veride econding'lerin consistent olması lazım
    # TODO: Bunun için bu enconding kısmı ayrı bir node olarak koyulabilir
    # TODO: Node'a ister misin gibi configuration koymuyorum çünkü eğer ayrı node olarak yaparsam
    # TODO: ilerde WebSocket'ten gelen verileri de direk ona sokabilirim.
        # TODO: Yeni node olarak yapınca eskisini tutup sürekli update ederek mi
        # TODO: yoksa her defasında yeniden mi fitle şeklinde opsiyon koayabilirim.
    def function(self, data, encode):
        if data.type != Node.Type.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        X, y, onlyTest = data.output
        
        print(f'Before Encoding: {y}', f'#1: {(y == 1).sum()}', f'#0: {(y == 0).sum()}')
        before_ones = (y == 1).sum()
        before_zeros = (y == 0).sum()
        
        # Encoding
        if self.encoder is None:
            self.encoder = SimpleEncoder().fit(X) if encode == 'S' else OneHotEncoder().fit(X)
        # elif not persist: # If I need to re-fit the encoder
            # self.encoder.fit(X, y)
        X, y = self.encoder.transform(X, y)
        
        print(f'After Encoding: {y}', f'#1: {(y == 1).sum()}', f'#0: {(y == 0).sum()}')
        after_ones = (y == 1).sum()
        after_zeros = (y == 0).sum()
        
        print('They are equal' if (after_ones == before_ones and after_zeros == before_zeros) else 'They are different')
        
        self.send_next_node((X, y, onlyTest))
        self.done()

    
class Encoder(metaclass=ABCMeta):
    
    def __init__(self):
        self.config = Config()
    
    def fit(self, X):
        self.class_encoder = LE()
        self.class_encoder.fit(self.config.classes())
        self.config.inverse = self.class_encoder.inverse_transform
        return self
    
    @abstractmethod
    def transform(self, X, y):
        raise NotImplementedError()
    
    def fit_transform(self, X, y):
        return self.fit(X, y).transform(X, y)


class SimpleEncoder(Encoder):
    
    def __init__(self):
        super().__init__()
        self.encoders = defaultdict(LE)
    
    def fit(self, X):
        # * I am getting categorical columns from the config file
        # cat_cols = X.columns[X.dtypes == 'object'].tolist()
        cat_cols = self.config.categoric_columns
        X[cat_cols].apply(lambda col: self.encoders[col.name].fit(self.config.categories(col.name)))
        return super().fit(X)
    
    def transform(self, X, y):
        # cat_cols = X.columns[X.dtypes == 'object'].tolist()
        cat_cols = self.config.categoric_columns
        X[cat_cols] = X[cat_cols].apply(lambda col: self.encoders[col.name].transform(col))
        y = self.class_encoder.transform(y)
        return X, y
    

class OneHotEncoder(Encoder):
    
    def __init__(self):
        super().__init__()
        self.columns = []
        for col, attr in self.config['sensors'].items():
            if not self.config.is_categoric(col):
                self.columns.append(col)
            else:
                for cat in set(attr['categories']):
                    self.columns.append(f'{col}_{cat}')
    
    def transform(self, X, y):
        X = pd.get_dummies(X)
        X = X.reindex(columns=self.columns, fill_value=0)
        y = self.class_encoder.transform(y)
        return X, y