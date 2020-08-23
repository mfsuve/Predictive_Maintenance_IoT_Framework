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
        if data.type == Node.Type.NODERED: # Coming from nodered
            try:
                replayed = self.q.popleft()
                self.send_nodered(replayed)
                print('ReplayData | Replayed data', f'ReplayData | Current Lenght: {len(self.q)}')
            except IndexError:
                # TODO: Fix this, what to do if there is no data to be replayed?
                print('ReplayData | Tried to replay but there is no data', f'ReplayData | Current Lenght: {len(self.q)}')
        else:
            if data.type != Node.Type.DATA:
                raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
            _, y, _ = data.output
            self.q.extend(y)
            print('ReplayData | Stored data', f'ReplayData | Current Lenght: {len(self.q)}')
            
            print('ReplayData | Number of data: ', len(self.q))
            print('ReplayData | Number of 1s: ', (np.array(self.q) == 1).sum())
            print('ReplayData | Number of 0s: ', (np.array(self.q) == 0).sum())
        
        self.status(f'data size: {len(self.q)}')
    