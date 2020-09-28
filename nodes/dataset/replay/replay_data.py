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

    def function(self, data):
        if data.type != InputType.DATA and data.type != InputType.NODERED:
            raise TypeError(f"Input needs to be either from a data node or from nodered but got from '{data.type.name.lower()}'")
        
        if data.type == InputType.NODERED: # Coming from nodered
            try:
                replayed = self.q.popleft()
                self.send_nodered(replayed)
                print('ReplayData | Replayed data', f'ReplayData | Current Lenght: {len(self.q)}')
            except IndexError:
                self.warning('There is no data to be replayed')
                print('ReplayData | Tried to replay but there is no data', f'ReplayData | Current Lenght: {len(self.q)}')
        else:
            self.q.extend(combine_data(*data.get()))
            print('ReplayData | Stored data', f'ReplayData | Current Lenght: {len(self.q)}')
                
        self.status(f'data size: {len(self.q)}')
    