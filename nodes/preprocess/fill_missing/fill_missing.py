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
        
        # * Assuming y will never be NaN
        # TODO: In case it is, handle it here
        
        # Filling missing values using its own stats
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
        elif preFillSelect in FillMissing.interpolation_methods:
            order = FillMissing.interpolation_methods.index(preFillSelect) + 1
            try:
                X.interpolate(method=preFillSelect, limit_area='inside', inplace=True)
                X.interpolate(method='spline', order=order, limit_direction='both', inplace=True)
            except ValueError:
                self.warning(f"Can't use {preFillSelect} interpolation for the first fill on this data, skipping...")
        
        # Filling the remaining missing values using the stats of old data
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
