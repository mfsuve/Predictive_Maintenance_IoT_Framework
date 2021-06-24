import numpy as np
import pandas as pd

from utils.utils import myprint as print
from utils.node import Data
from utils.config import Config
from utils.io import Input, InputType

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.warn = True
        
    def first_called(self, data:Input):
        self.scaler = MMS()
        config:Config
        X, _, encoded, config = data.get()
        ranges = pd.DataFrame()
        warn = True
        for col in X.columns:
            if encoded or config.is_numeric(col):
                ranges[col] = [config.min(col), config.max(col)]
            elif warn:
                self.warning(f"There are non-encoded categorical values in the data, they will not be scaled. \n\nYou can use the encoder node before this node to get rid of the categorical values.")
                warn = False
        self.scaler.fit(ranges)
        self.columns = list(ranges.columns)

    def function(self, data:Input):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X:pd.DataFrame
        y:pd.Series
        encoded:bool
        X, y, encoded, config = data.get()
        
        # print(f"MinMaxScaler | self.columns", self.columns)
        
        print(f"Scaler | has any columns with any nan before", X[self.columns].isna().any().any())
        X[self.columns] = self.scaler.transform(X[self.columns])
        print(f"Scaler | has any columns with any nan after", X[self.columns].isna().any().any())
        
        # * Assure that all the values are in [0, 1] (ignoring NaN values)
        _X = X[self.columns]
        if not (((_X > 0) & (_X < 1)) | np.isclose(_X, 1) | np.isclose(_X, 0) | _X.isna()).all().all() and self.warn:
            # TODO: print the ones that are outside [0,1]
            temp_x = _X.to_numpy().ravel()
            temp_x = temp_x[((temp_x < 0) | (temp_x > 1)) & pd.notna(temp_x)]
            print('Scaler | X:', temp_x)
            # all_nan_col = temp_x.columns[temp_x.isna().all()]
            # print('Scaler | all_nan_col:', all_nan_col)
            # This can be because of filling with constant outside of the defined range
            self.warning(f"There are some numeric columns detected having values outside of the range of min and max values defined in config file.\
                You may have either defined those ranges incorrectly or filled missing values with a constant outside of ranges in the config file.")
            self.warn = False
        
        self.send_next_node((X, y, encoded, config))
        self.done()


# This is old, I am keeping this so that the program won't crash
# (Direk silebilirdim düzeltip, ama üşendim :)
class StandardScaler(Data):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = InputType.DATA

    def function(self, X, y):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y