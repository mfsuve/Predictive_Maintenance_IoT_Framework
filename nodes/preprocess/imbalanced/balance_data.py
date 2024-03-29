import pandas as pd
import numpy as np

from utils.config import Config
from utils.utils import myprint as print
from utils.node import Data, Node
from utils.io import Input, InputType
from collections import Counter

import imblearn

class BalanceData(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        _, sampling_type = self.node_config['sampling_type'].split()
        self.status(sampling_type)
        
        
    def first_called(self, data:Input, sampling_type):
        module, sampling_type = sampling_type.split()
        config:Config
        X, y, encoded, config = data.get()
        if sampling_type == 'SMOTENC':
            cat_cols = [i for i, col in enumerate(X.columns) if config.is_categoric(col)]
            self.sampler = imblearn.__getattribute__(module).__getattribute__(sampling_type)(cat_cols, n_jobs=-1)
        else:
            self.sampler = imblearn.__getattribute__(module).__getattribute__(sampling_type)()
        
    
    def function(self, data:Input, sampling_type):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y, encoded, config = data.get()
        try:
            X_res, y_res = self.sampler.fit_resample(X, y)
        except ValueError as e:
            self.warning(f"{e}. Skipping.")
            X_res, y_res = X, y
        
        print(f"type(X_res): {type(X_res)}", f"type(y_res): {type(y_res)}", f"X.columns:", X.columns)
        print(f"Class sizes before balancing:", sorted(list(Counter(y).items())), f"Class sizes after balancing:", sorted(list(Counter(y_res).items())))

        if X_res.empty:
            self.warning(f"Balance node emptied the data, consider removing it from the pipeline")

        self.send_next_node((X_res, y_res, encoded, config))
        self.done()
