import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Data
from utils.io import InputType

class FillMissing(Data):
    
    interpolation_methods = ['linear', 'quadratic', 'cubic']
    
    def __init__(self, *args):
        super().__init__(*args)
        self.val = 0

        
    def function(self, data, preFillConstant, postFillConstant, preFillSelect, postFillSelect):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        
        # !!! Değiştirmeden önce eskilerini pushla !!! #
        
        
        # Filling missing values
        if preFillSelect == 'constant':
            X.fillna(preFillConstant, inplace=True)
        elif preFillSelect == 'mean':
            X.fillna(X.mean(), inplace=True)
        elif preFillSelect == 'median':
            X.fillna(X.median(), inplace=True)
        elif preFillSelect == 'most':
            X.fillna(X.mode().iloc[0], inplace=True)
        elif preFillSelect == 'nearest':
            X.interpolate(method='nearest', inplace=True)
            X.fillna(method='ffill', inplace=True)
            X.fillna(method='bfill', inplace=True)
        elif preFillSelect in interpolation_methods:
            order = interpolation_methods.index(preFillSelect) + 1
            try:
                X.interpolate(method=preFillSelect, limit_area='inside', inplace=True)
                X.interpolate(method='spline', order=order, limit_direction='both', inplace=True)
            except ValueError:
                self.warning(f"Can't use {preFillSelect} interpolation for the first fill on this data, skipping...")
        
        
        # TODO: Öncesinde ilk zamanlarda yaptığım gibi doldurulmaya çalışılabilir (githubdaki gibi, o ffill, quadratic ve cubic falan olandan).
        # TODO: Eğer o şekilde yapıldıktan sonra sonunda NaN kaldıysa aşağıdaki yöntemlerle devam edilebilir.
        # TODO: Bunu da eğer gelen data birden fazla satır içeriyorsa diye düşündüm.
        # TODO: Ama bu kısımı yapmak için nodered'den eskisi gibi config almam lazım
        
        # * Assuming y will never be NaN
        # TODO: In case it is, handle it here
        
        if postFillSelect != 'none':
            if postFillSelect == 'constant':
                X = X.fillna(postFillConstant)
            else:
                X = X.fillna(self.val)
                if postFillSelect == 'mean':
                    self.val = X.mean()
                elif postFillSelect == 'median':
                    self.val = X.median()
                elif postFillSelect == 'last':
                    self.val = X.iloc[-1]
        
            assert isinstance(X, pd.DataFrame)
            assert not X.isna().any().any()
        
        self.send_next_node((X, y))
        self.done()
