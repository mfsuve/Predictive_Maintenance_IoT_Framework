import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Data

from collections import deque

class ReplayData(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.inputs.append(Data)
        self.stream = True


    def function(self, stream_data):
        data = deque()
        # Currently just storing y
        for X, y, onlyTest in stream_data:
            if y is None:
                try:
                    replayed = data.popleft()
                except IndexError:
                    # TODO: Fix this, what to do if there is no data to be replayed?
                    print('ReplayData | Tried to replay but there is no data', f'ReplayData | Current Lenght: {len(data)}')
                    continue
                self.send_next_node(replayed)
                print('ReplayData | Replayed data', f'ReplayData | Current Lenght: {len(data)}')
            else:
                data.append(y)
                print('ReplayData | Stored data', f'ReplayData | Current Lenght: {len(data)}')
            
            self.status(f'data size: {len(data)}')
    