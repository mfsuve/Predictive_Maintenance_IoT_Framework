import pandas as pd

from utils.node import Data
from utils.io import Input, InputType


class Buffer(Data):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Xs = []
        self.ys = []
        self.status(f'0/{self.node_config["maxData"]} Data')
        self.size = 0
        self.warn_encoded = True
        self.warn_no_target = True
        self.has_encoded = False
        self.has_no_target = False
        
    def append(self, X:pd.DataFrame, y:pd.Series):
        self.Xs.append(X)
        if y is None:
            self.ys.append(pd.Series([None] * X.shape[0]))
        else:
            self.ys.append(y)
        self.size += X.shape[0]
            
    def get_data_to_send(self, maxData:int):
        Xs = pd.concat(self.Xs, ignore_index=True)
        ys = pd.concat(self.ys, ignore_index=True)
        
        while self.size >= maxData:
            X:pd.DataFrame = Xs.iloc[:maxData]
            y:pd.Series = ys.iloc[:maxData]
            Xs = Xs.iloc[maxData:]
            ys = ys.iloc[maxData:]
            self.size -= maxData
            yield X, y
        
        self.Xs = [Xs]
        self.ys = [ys]
    
    def function(self, data:Input, maxData:int):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X:pd.DataFrame
        y:pd.Series
        encoded:bool
        X, y, encoded, config = data.get()
        
        if self.warn_encoded and not self.has_encoded and encoded:
            self.warning(f"Buffering encoded and non-encoded data, will treat them as they were encoded. But it is advised to buffer either all encoded or all non-encoded data.")
            self.warn_encoded = False
        self.has_encoded = self.has_encoded or encoded
        
        if self.warn_no_target and not self.has_no_target and y is None:
            self.warning(f"Buffering data with and without target. It is advised to buffer data only with or without target.")
            self.warn_no_target = False
        self.has_no_target = self.has_no_target or y is None
        
        self.append(X, y)
        for X_to_send, y_to_send in self.get_data_to_send(maxData):
            if y_to_send.isna().all():
                self.send_next_node((X_to_send, None, self.has_encoded, config))
            else:
                self.send_next_node((X_to_send, y_to_send, self.has_encoded, config))
            
        self.status(f'{self.size}/{maxData}')
        
    