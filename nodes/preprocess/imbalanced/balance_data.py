import pandas as pd
import sys
import json
import numpy as np

from utils.config import Config
from utils.utils import myprint as print
from utils.node import Data, Node
from utils.io import InputType
from collections import Counter

import imblearn

class BalanceData(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        module, sampling_type = self.node_config['sampling_type'].split()
        self.sampler = imblearn.__getattribute__(module).__getattribute__(sampling_type)()
        self.status(sampling_type)
        
    
    def function(self, data, sampling_type):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        X_res, y_res = self.sampler.fit_resample(X, y)
        
        print(f"type(X_res): {type(X_res)}", f"type(y_res): {type(y_res)}", f"X.columns:", X.columns)
        print(f"Class sizes before balancing:", sorted(list(Counter(y).items())), f"Class sizes after balancing:", sorted(list(Counter(y_res).items())))
        
        self.send_next_node((X_res, y_res))
