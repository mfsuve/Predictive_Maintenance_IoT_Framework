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
        
    def append(self, X, y):
        self.Xs.append(X)
        if y is None:
            self.ys.append(pd.Series([None] * X.shape[0]))
        else:
            self.ys.append(y)
    
    def function(self, data, numData):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        
        if len(self.Xs) < numData - 1:
            self.append(X, y)
        else:
            self.append(X, y)
            if y is None:
                self.send_next_node((pd.concat(self.Xs, ignore_index=True), None))
            else:
                self.send_next_node((pd.concat(self.Xs, ignore_index=True), pd.concat(self.ys, ignore_index=True)))
            self.Xs.clear()
            self.ys.clear()
            self.done()
            
        self.status(f'{len(self.Xs)}/{numData}')
        
    