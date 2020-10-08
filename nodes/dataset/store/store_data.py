import pandas as pd
import sys
import json
import numpy as np
import os
from itertools import count
from io import StringIO

from utils.config import Config
from utils.utils import myprint as print, combine_data
from utils.node import Data
from utils.io import InputType
from utils.save_load_utils import add_prefix

from utils.utils import after


class StoreDataset(Data):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = 0
        self.remainder = None
        self.path = None
    
    
    def first_called(self, data, path, numrows):
        print('Store | init', 'numrows', numrows)
        self.X = pd.DataFrame(index=range(numrows), columns=Config().columns() + ['target'])
        

    def append(self, X, numrows):
        print('Store | append', 'X', X)
        next_index = self.index + X.shape[0]
        if next_index > numrows:
            remaining_size = numrows - self.index
            self.X[self.index:] = X[: remaining_size]
            self.remainder = X[remaining_size:]
            self.index = numrows
        else:
            self.X[self.index: next_index] = X
            self.index = next_index
            self.remainder = None
        self.status(f'data size: {self.index}/{numrows}')
        return self.index >= numrows
        
    
    def get_path(self, path):
        dirname, filename = os.path.split(path)
        base, ext = os.path.splitext(filename)
        if ext != '' and ext != '.csv':
            self.warning('Changed extension to `.csv`.')
        for i in count(1):
            filename = f'{base}_{i}.csv'
            yield add_prefix(filename, path=dirname)


    def save_and_reset(self, numrows, path):
        self.index = 0
        next_path = next(path)
        print('Store | save and reset', 'path:', next_path)
        self.X.to_csv(next_path, header=True, index=False)
        self.send_nodered(next_path)
        if self.remainder is not None:
            return self.append(self.remainder, numrows)
        return False
    
    
    def function(self, data, path, numrows):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be data coming from a data node but got from a '{data.type.name.lower()}' node")
        
        # TODO: Data combine node
        
        path = self.get_path(path)
        
        full = self.append(combine_data(*data.get()), numrows)
        print('Store | 1. full', full)
        while full:
            full = self.save_and_reset(numrows, path)
            print('Store | 2. full', full)

        # self.done()
    
    