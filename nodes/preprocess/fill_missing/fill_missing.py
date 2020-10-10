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
        self.valX = 0
        self.valy = 0

        
    def function(self, data, preFillConstant, postFillConstant, preFillSelect, postFillSelect):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        
        
        # Filling missing values using its own stats
        if preFillSelect == 'constant':
            X = X.fillna(preFillConstant)
            if y is not None:
                y = y.fillna(preFillConstant)
        elif preFillSelect == 'mean':
            X = X.fillna(X.mean())
            if y is not None:
                y = y.fillna(y.mean())
        elif preFillSelect == 'median':
            X = X.fillna(X.median())
            if y is not None:
                y = y.fillna(y.median())
        elif preFillSelect == 'most':
            X = X.fillna(X.mode().iloc[0])
            if y is not None:
                y = y.fillna(y.mode().iloc[0])
        elif preFillSelect == 'nearest':
            X = X.interpolate(method='nearest')
            X = X.fillna(method='ffill')
            X = X.fillna(method='bfill')
            if y is not None:
                y = y.interpolate(method='nearest')
                y = y.fillna(method='ffill')
                y = y.fillna(method='bfill')
        elif preFillSelect in FillMissing.interpolation_methods:
            order = FillMissing.interpolation_methods.index(preFillSelect) + 1
            try:
                newX = X.interpolate(method=preFillSelect, limit_area='inside')
                newX = newX.interpolate(method='spline', order=order, limit_direction='both')
                if y is not None:
                    newy = y.interpolate(method=preFillSelect, limit_area='inside')
                    newy = newy.interpolate(method='spline', order=order, limit_direction='both')
                else:
                    newy = y
            except ValueError:
                self.warning(f"Can't use {preFillSelect} interpolation for the first fill on this data, skipping...")
            else: # Defined newX and newy not to change them if ValueError happens
                X, y = newX, newy
        
        # Filling the remaining missing values using the stats of old data
        if postFillSelect != 'none':
            if postFillSelect == 'constant':
                X = X.fillna(postFillConstant)
                if y is not None:
                    y = y.fillna(postFillConstant)
            else:
                X = X.fillna(self.valX)
                if y is not None:
                    y = y.fillna(self.valy)
                if postFillSelect == 'mean':
                    self.valX = X.mean()
                    if y is not None:
                        self.valy = y.mean()
                elif postFillSelect == 'median':
                    self.valX = X.median()
                    if y is not None:
                        self.valy = y.median()
                elif postFillSelect == 'last':
                    self.valX = X.iloc[-1]
                    if y is not None:
                        self.valy = y.iloc[-1]
        
        self.send_next_node((X, y))
        self.done()
