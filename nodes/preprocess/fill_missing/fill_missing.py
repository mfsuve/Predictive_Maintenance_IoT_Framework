import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Data
from utils.io import InputType

class FillMissing(Data):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.val = 0

        
    def function(self, data, fillConstant, fillSelect):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        
        # TODO: Öncesinde ilk zamanlarda yaptığım gibi doldurulmaya çalışılabilir (githubdaki gibi, o ffill, quadratic ve cubic falan olandan).
        # TODO: Eğer o şekilde yapıldıktan sonra sonunda NaN kaldıysa aşağıdaki yöntemlerle devam edilebilir.
        # TODO: Bunu da eğer gelen data birden fazla satır içeriyorsa diye düşündüm.
        # TODO: Ama bu kısımı yapmak için nodered'den eskisi gibi config almam lazım
        
        # * Assuming y will never be NaN
        # TODO: In case it is, handle it here
        
        if fillSelect == 'constant':
            X.fillna(fillConstant, inplace=True)
        else:
            X.fillna(self.val, inplace=True)
            if fillSelect == 'mean':
                self.val = X.mean()
            elif fillSelect == 'median':
                self.val = X.median()
            elif fillSelect == 'last':
                self.val = X.iloc[-1]
        
        assert isinstance(X, pd.DataFrame)
        assert not X.isna().any().any()
        
        self.send_next_node((X, y))
        self.done()
