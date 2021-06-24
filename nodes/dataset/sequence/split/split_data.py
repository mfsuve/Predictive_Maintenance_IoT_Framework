import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Data
from utils.io import Input, InputType


# ? Random state de input olarak verilebilir mi?
class Split(Data):
    
    def function(self, data:Input, shuffle:bool, splitPercentage:int):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X:pd.DataFrame
        y:pd.Series
        encoded:bool
        X, y, encoded, config = data.get()
        num_rows, _ = X.shape
        
        indices = np.random.choice(X.index, size=num_rows, replace=False) if shuffle else X.index
        split_size = int(num_rows * (splitPercentage / 100))
        indices1 = indices[:split_size]
        indices2 = indices[split_size:]
        
        X1:pd.DataFrame = X.loc[indices1].reset_index(drop=True)
        X2:pd.DataFrame = X.loc[indices2].reset_index(drop=True)
        
        if y is None:
            y1, y2 = None, None
        else:
            y1 = y.reindex(indices1).reset_index(drop=True)
            y2 = y.reindex(indices2).reset_index(drop=True)
            
        self.send_next_node(None if X1.empty else (X1, y1, encoded, config), None if X2.empty else (X2, y2, encoded, config))
        self.done()
    