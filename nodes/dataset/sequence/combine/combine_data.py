import pandas as pd

from utils.node import Data
from utils.io import Input, InputType


class Combine(Data):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Xs = []
        self.ys = []
        self.status(f'0/{self.node_config["numData"]} Data')
        self.reset()
        self.warn = True
        
    def append(self, X, y):
        self.Xs.append(X)
        if y is None:
            self.ys.append(pd.Series([None] * X.shape[0]))
        else:
            self.ys.append(y)
            
    def reset(self):
        self.Xs.clear()
        self.ys.clear()
        self.has_encoded = False
    
    def function(self, data:Input, numData):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y, encoded, config = data.get()
        
        if self.warn and not self.has_encoded and encoded:
            self.warning(f"Combining encoded and non-encoded data, will treat them as they were encoded. But it is advised to combine either all encoded or all non-encoded data.")
            self.warn = False
        self.has_encoded = self.has_encoded or encoded
        
        if len(self.Xs) < numData - 1:
            self.append(X, y)
        else:
            self.append(X, y)
            Xs = pd.concat(self.Xs, ignore_index=True)
            ys = pd.concat(self.ys, ignore_index=True)
            if ys.isna().all():
                self.send_next_node((Xs, None, self.has_encoded, config))
            else:
                self.send_next_node((Xs, ys, self.has_encoded, config))
            self.reset()
            self.done()
            
        self.status(f'{len(self.Xs)}/{numData}')
        
    