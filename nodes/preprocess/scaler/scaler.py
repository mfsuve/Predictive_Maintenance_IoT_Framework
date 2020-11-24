import pandas as pd

from utils.utils import myprint as print
from utils.node import Data
from utils.config import Config
from utils.io import InputType

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        
    def first_called(self, data):
        self.scaler = MMS()
        config = Config()
        X, _ = data.get()
        ranges = pd.DataFrame(index=range(2), columns=X.columns)
        for col in ranges.columns:
            ranges.loc[0, col] = config.min(col)
            ranges.loc[1, col] = config.max(col)
        self.scaler.fit(ranges)

    def function(self, data):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        print(f'MinMax Scaling...')
        
        X, y = data.get()
        
        if not all(map(pd.api.types.is_numeric_dtype, X.dtypes)) or not pd.api.types.is_numeric_dtype(y.dtype):
            raise ValueError(f"Data needs to contain only numerical values in order to be scaled, but there are non numeric values in the data.")
        
        X[:] = self.scaler.transform(X)
        
        # print('Scaled min:', X.min())
        # print('Scaled max:', X.max())
        
        # print('almost_le(0, X):', almost_le(0, X).all())
        # print('almost_le(X, 1):', almost_le(X, 1).all())
        
        # TODO: Might delete this later for performance
        # * Assure that all the values are in [0, 1] (ignoring NaN values)
        assert (((X >= 0) & (X <= 1)) | X.isna()).all().all()
        
        self.send_next_node((X, y))
        self.done()


class StandardScaler(Data):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = InputType.DATA

    def function(self, X, y):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y