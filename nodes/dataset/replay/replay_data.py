import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node

from collections import deque

class ReplayData(Node):
    
    def __init__(self, *args):
        super().__init__(*args)
        # self.inputs.append(Data)
        self.q = deque()


    def function(self, data):
        # Currently just storing y
        if data is None:
            try:
                replayed = self.q.popleft()
                self.send_nodered(replayed)
                print('ReplayData | Replayed data', f'ReplayData | Current Lenght: {len(self.q)}')
            except IndexError:
                # TODO: Fix this, what to do if there is no data to be replayed?
                print('ReplayData | Tried to replay but there is no data', f'ReplayData | Current Lenght: {len(self.q)}')
        else:
            X, y, onlyTest = data
            self.q.extend(y)
            print('ReplayData | Stored data', f'ReplayData | Current Lenght: {len(self.q)}')
        
        self.status(f'data size: {len(self.q)}')
    