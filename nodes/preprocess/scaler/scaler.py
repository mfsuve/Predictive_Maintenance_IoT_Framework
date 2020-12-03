import pandas as pd

from utils.utils import myprint as print
from utils.node import Data
from utils.config import Config
from utils.io import InputType

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.warn = True
        
    def first_called(self, data):
        self.scaler = MMS()
        config = Config()
        X, _ = data.get()
        ranges = pd.DataFrame()
        warn = True
        for col in X.columns:
            if pd.api.types.is_numeric_dtype(X[col].dtype):
                ranges[col] = [config.min(col), config.max(col)]
            elif warn:
                self.warning(f"There are categorical values in the data, they will not be scaled.")
                warn = False
        self.scaler.fit(ranges)
        self.columns = list(ranges.columns)

    def function(self, data):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        print(f'MinMax Scaling...')
        
        X, y = data.get()
        
        X[self.columns] = self.scaler.transform(X[self.columns])
        
        # TODO: Might delete this later for performance
        # * Assure that all the values are in [0, 1] (ignoring NaN values)
        _X = X[self.columns]
        if not (((_X >= 0) & (_X <= 1)) | _X.isna()).all().all() and self.warn:
            self.warning(f"There are some numeric columns detected having values outside of the range of min and max values of corresponding column.")
            self.warn = False
        
        self.send_next_node((X, y))
        self.done()


class StandardScaler(Data):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = InputType.DATA

    def function(self, X, y):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y