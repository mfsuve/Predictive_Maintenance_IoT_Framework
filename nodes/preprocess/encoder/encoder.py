import pandas as pd
import sys
import json
import numpy as np
from abc import ABCMeta, abstractmethod

from utils.utils import myprint as print
from utils.node import Data
from utils.config import Config
from utils.io import InputType

from sklearn.preprocessing import LabelEncoder as LE
from collections import defaultdict

class Encoder(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.encoder = None
        self.warn = True


    def function(self, data, encode):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        X, y, encoded = data.get()
        
        # Encoding
        if self.encoder is None:
            self.encoder = SimpleEncoder().fit(X) if encode == 'S' else OneHotEncoder().fit(X)
    
        if encoded:
            if self.warn:
                self.warning(f"Data is encoded before, skipping!")
                self.warn = False
        else:
            X, y = self.encoder.transform(X, y)
        
        self.send_next_node((X, y, True))
        self.done()

    
class BaseEncoder(metaclass=ABCMeta):
    
    def __init__(self):
        self.config = Config()
        self.fitted = False
    
    def fit(self, X):
        self.class_encoder = LE()
        self.class_encoder.fit(self.config.classes())
        self.config.transform_label(self.class_encoder.transform)
        self.fitted = True
        return self
    
    # Ignoring nan
    def transform_ignore_nan(self, col:pd.Series, temp_val, enc:LE):
        nan_indices = col.isna()
        col[nan_indices] = temp_val # Temporary value to bypass the exception
        col = enc.transform(col).astype(float)
        col[nan_indices] = np.nan
        return col
    
    @abstractmethod
    def transform(self, X, y):
        if not self.fitted:
            raise ValueError("Encoders need to be fitted before transform")
        return pd.Series(self.transform_ignore_nan(y, y.iloc[0], self.class_encoder))
    
    def fit_transform(self, X, y):
        return self.fit(X, y).transform(X, y)


class SimpleEncoder(BaseEncoder):
    
    def __init__(self):
        super().__init__()
        self.encoders = defaultdict(LE)
    
    def fit(self, X):
        # * I am getting categorical columns from the config file
        cat_cols = self.config.categoric_columns
        X[cat_cols].apply(lambda col: self.encoders[col.name].fit(self.config.categories(col.name)))
        return super().fit(X)
    
    def transform(self, X, y):
        cat_cols = self.config.categoric_columns
        X[cat_cols] = X[cat_cols].apply(
            lambda col: self.transform_ignore_nan(col, self.config.categories(col.name)[0], self.encoders[col.name])
        )
        return X, super().transform(X, y)
    

class OneHotEncoder(BaseEncoder):
    
    def __init__(self):
        super().__init__()
        self.columns = []
        self.categorical_columns = []
        for col, attr in self.config['columns'].items():
            if self.config.is_numeric(col):
                self.columns.append(col)
            else:
                self.categorical_columns.append(col)
                for cat in set(attr['categories']):
                    self.columns.append(f'{col}_{cat}')
    
    def transform(self, X, y):
        X = pd.get_dummies(X, columns=self.categorical_columns)
        X = X.reindex(columns=self.columns, fill_value=0)
        return X, super().transform(X, y)