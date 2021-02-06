from numpy.lib.function_base import append
import pandas as pd
import sys
import json
import numpy as np

from utils.utils import combine_data, myprint as print
from utils.node import Data
from utils.io import InputType


class Combine(Data):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Xs = []
        self.ys = []
        self.status(f'0/{self.node_config["numData"]} Data')
        self.reset()
        self.warn = True
        
    def append(self, X, y):
        self.Xs.append(X)
        if y is None:
            self.ys.append(pd.Series([None] * X.shape[0]))
        else:
            self.ys.append(y)
            
    def reset(self):
        self.Xs.clear()
        self.ys.clear()
        self.has_encoded = False
    
    def function(self, data, numData):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y, encoded = data.get()
        
        if self.warn and not self.has_encoded and encoded:
            self.warning(f"Combining encoded and non-encoded data, will treat them as they were encoded. But it is advised to combine all encoded or all non-encoded data.")
            self.warn = False
        self.has_encoded = self.has_encoded or encoded
        
        if len(self.Xs) < numData - 1:
            self.append(X, y)
        else:
            self.append(X, y)
            if y is None:
                self.send_next_node((pd.concat(self.Xs, ignore_index=True), None, self.has_encoded))
            else:
                self.send_next_node((pd.concat(self.Xs, ignore_index=True), pd.concat(self.ys, ignore_index=True), self.has_encoded))
            self.reset()
            self.done()
            
        self.status(f'{len(self.Xs)}/{numData}')
        
    