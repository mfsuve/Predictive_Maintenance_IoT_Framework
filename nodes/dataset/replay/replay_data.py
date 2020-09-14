import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Data
from utils.io import InputType

from collections import deque

class ReplayData(Data):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.q = deque()

    def function(self, data):
        # Currently just storing y
        if data.type == InputType.NODERED: # Coming from nodered
            try:
                replayed = self.q.popleft()
                self.send_nodered(replayed)
                print('ReplayData | Replayed data', f'ReplayData | Current Lenght: {len(self.q)}')
            except IndexError:
                # TODO: Fix this, what to do if there is no data to be replayed?
                print('ReplayData | Tried to replay but there is no data', f'ReplayData | Current Lenght: {len(self.q)}')
        else:
            if data.type != InputType.DATA:
                raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
            _, y = data.get()
            if y is not None:
                self.q.extend(y)
                print('ReplayData | Stored data', f'ReplayData | Current Lenght: {len(self.q)}')
                
        self.status(f'data size: {len(self.q)}')
    