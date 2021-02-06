import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print, combine_data
from utils.node import Data
from utils.io import InputType

from collections import deque

class ReplayData(Data):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.q = deque()
        self.status(f'data size: 0')

    def function(self, data):
        if data.type != InputType.DATA and data.type != InputType.NODERED:
            raise TypeError(f"Input needs to be either from a data node or from nodered but got from '{data.type.name.lower()}'")
        
        if data.type == InputType.NODERED: # Coming from nodered
            try:
                replayed = self.q.popleft()
                self.send_nodered(replayed)
                self.done()
            except IndexError:
                self.warning('There is no data to be replayed')
        else:
            X, y, encoded = data.get()
            combined = combine_data(X, y)
            self.q.extend([e[1] for e in combined.iterrows()])
                
        self.status(f'data size: {len(self.q)}')
    