import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Data
from utils.io import InputType
from utils.config import Config

class FillMissing(Data):
    
    interpolation_methods = ['linear', 'quadratic', 'cubic']
    
    def __init__(self, *args):
        super().__init__(*args)
        
    
    def first_called(self, data, preFillConstantX, postFillConstantX, preFillSelectX, postFillSelectX, preFillConstantY, postFillConstantY, preFillSelectY, postFillSelectY):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        warn = True
        self.valX = pd.Series()
        self.preFillConstantX = pd.Series()
        self.postFillConstantX = pd.Series()
        config = Config()
        X, y = data.get()
        pre_encoded = False
        for col in X.columns:
            
            # If column name is not in columns -> it was OneHot Encoded changing the column name
            # Or if column (was categoric and not OneHot Encoded) but (the current content is numeric) -> it was Simple Encoded
            pre_encoded = col not in config.columns() \
                          or (config.is_categoric(col) and pd.api.types.is_numeric_dtype(X[col].dtype)) \
                          or pre_encoded # To make sure once it is True, it will always be True
            
            # This is the initial value for postFill. Because in postFill, I calculate the fill value from previous data.
            # It was just 0 but for non-encoded categorial variable, it was not ideal.
            self.valX[col] = config.categories(col)[0] if config.is_categoric(col) else config.min(col)
            # if constant, min or max is selected
            if config.is_numeric(col):
                
                if preFillSelectX == 'min':
                    self.preFillConstantX[col] = config.min(col)
                elif preFillSelectX == 'max':
                    self.preFillConstantX[col] = config.max(col)
                else:
                    self.preFillConstantX[col] = preFillConstantX
                
                if postFillSelectX == 'min':
                    self.postFillConstantX[col] = config.min(col)
                elif postFillSelectX == 'max':
                    self.postFillConstantX[col] = config.max(col)
                else:
                    self.postFillConstantX[col] = postFillConstantX
                    
            else:
                self.preFillConstantX[col] = config.categories(col)[0]
                self.postFillConstantX[col] = config.categories(col)[0]
                if warn:
                    if preFillSelectX in ['constant', 'min', 'max']:
                        self.warning(f"There are some non-encoded categorical columns in the data. For those columns, the first category will be used for the first fill.")
                    elif preFillSelectX not in ['most', 'nearest'] and postFillSelectX in ['constant', 'min', 'max', 'mean', 'median']:
                        # postFillSelectX in ['constant', 'min', 'max'] is because they need to be numbers
                        # postFillSelectX in ['mean', 'median'] is because they won't be calculated for categorical values
                        self.warning(f"There are some non-encoded categorical columns in the data. For those columns, the first category will be used for the second fill.")
                    warn = False
        
        # # TODO: Delete this, this is just for to see if pre_encoded variable has the correct value
        # self.warning(f"self.preFillConstantX is:\n{self.preFillConstantX}")
        # self.warning(f"pre_encoded: {pre_encoded}")

        if y is not None:
            if pre_encoded:
                self.valy = config.min_y(X_encoded=True)
                if preFillSelectY == 'min':
                    self.preFillConstantY = config.min_y(X_encoded=True)
                if preFillSelectY == 'max':
                    self.preFillConstantY = config.max_y(X_encoded=True)
                else:
                    self.preFillConstantY = preFillConstantY
                    
                if postFillSelectY == 'min':
                    self.postFillConstantY = config.min_y(X_encoded=True)
                if postFillSelectY == 'max':
                    self.postFillConstantY = config.max_y(X_encoded=True)
                else:
                    self.postFillConstantY = postFillConstantY
            else:
                if pd.api.types.is_numeric_dtype(y.dtype):
                    self.valy = config.min_y(X_encoded=False)
                    if preFillSelectY == 'min':
                        self.preFillConstantY = config.min_y(X_encoded=False)
                    if preFillSelectY == 'max':
                        self.preFillConstantY = config.max_y(X_encoded=False)
                    else:
                        self.preFillConstantY = preFillConstantY
                        
                    if postFillSelectY == 'min':
                        self.postFillConstantY = config.min_y(X_encoded=False)
                    if postFillSelectY == 'max':
                        self.postFillConstantY = config.max_y(X_encoded=False)
                    else:
                        self.postFillConstantY = postFillConstantY
                else:
                    self.valy = config.classes()[0]
                    self.preFillConstantY = config.classes()[0]
                    self.postFillConstantY = config.classes()[0]
                    if preFillSelectY in ['constant', 'min', 'max']:
                        self.warning(f"The target data is categorical and was not encoded, therefore the first class will be used for the first fill.")
                    elif preFillSelectY not in ['most', 'nearest'] and postFillSelectY in ['constant', 'min', 'max', 'mean', 'median']:
                        # postFillSelectX in ['constant', 'min', 'max'] is because they need to be numbers
                        # postFillSelectX in ['mean', 'median'] is because they won't be calculated for categorical values
                        self.warning(f"The target data is categorical and was not encoded, therefore the first class will be used for the second fill.")
        else:
            self.warning(f"Target is None, therefore it can't be filled.")
        
        
    def function(self, data, preFillConstantX, postFillConstantX, preFillSelectX, postFillSelectX, preFillConstantY, postFillConstantY, preFillSelectY, postFillSelectY):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y = data.get()
        
        X = self.pre_fill_X(X, preFillSelectX) # Median
        self.warning(f"pre_fill_X")
        for col in X.columns:
            if X[col].isna().any():
                self.warning(f"{col} has None\ndtype: {X[col].dtype}")
        if y.isna().any():
            self.warning(f"y has None")
        
        X = self.post_fill_X(X, postFillSelectX) # Median
        self.warning(f"post_fill_X")
        for col in X.columns:
            if X[col].isna().any():
                self.warning(f"{col} has None\ndtype: {X[col].dtype}")
        if y.isna().any():
            self.warning(f"y has None")
        
        y = self.pre_fill_y(y, preFillSelectY) # Mean
        self.warning(f"pre_fill_y")
        for col in X.columns:
            if X[col].isna().any():
                self.warning(f"{col} has None\ndtype: {X[col].dtype}")
        if y.isna().any():
            self.warning(f"y has None")
        
        y = self.post_fill_y(y, postFillSelectY) # Min
        self.warning(f"post_fill_y")
        for col in X.columns:
            if X[col].isna().any():
                self.warning(f"{col} has None\ndtype: {X[col].dtype}")
        if y.isna().any():
            self.warning(f"y has None")
        
        assert not (X.isna().any().any() or y.isna().any())
        
        self.send_next_node((X, y))
        self.done()


    def pre_fill_X(self, X, preFillSelectX):
        # Filling missing values using its own stats
        if preFillSelectX in ['constant', 'min', 'max']:
            X = X.fillna(self.preFillConstantX)
        elif preFillSelectX == 'mean':
            X = X.fillna(X.mean())
        elif preFillSelectX == 'median':
            X = X.fillna(X.median())
        elif preFillSelectX == 'most':
            X = X.fillna(X.mode().iloc[0])
        elif preFillSelectX == 'nearest':
            X = X.interpolate(method='nearest')
            X = X.fillna(method='ffill')
            X = X.fillna(method='bfill')
        elif preFillSelectX in FillMissing.interpolation_methods:
            order = FillMissing.interpolation_methods.index(preFillSelectX) + 1
            try:
                newX = X.interpolate(method=preFillSelectX, limit_area='inside')
                newX = newX.interpolate(method='spline', order=order, limit_direction='both')
            except ValueError:
                self.warning(f"Can't use {preFillSelectX} interpolation for the first fill on this data, it will be filled on the second fill.")
            else: # Defined newX and newy not to change them if ValueError happens
                X = newX
        return X
    
    
    def post_fill_X(self, X, postFillSelectX):
        # Filling the remaining missing values using the stats of old data
        if postFillSelectX != 'none':
            if postFillSelectX in ['constant', 'min', 'max']:
                X = X.fillna(self.postFillConstantX)
            else:
                X = X.fillna(self.valX)
                for col in X.columns:
                    if X[col].isna().any():
                        self.warning(f"After filling in postfillX:\n{col} has None\ndtype: {X[col].dtype}")
                self.warning(f"X.columns:\n{X.columns}")
                self.warning(f"valX.columns:\n{self.valX.index}")
                if postFillSelectX == 'mean':
                    self.warning(f"Filling with mean")
                    self.valX = X.mean()
                elif postFillSelectX == 'median':
                    self.warning(f"Filling with median")
                    self.valX = X.median()
                elif postFillSelectX == 'last':
                    self.warning(f"Filling with last")
                    self.valX = X.iloc[-1]
                self.warning(f"new valX nan indices: {self.valX.isna().to_numpy().nonzero()[0]}")
                self.valX = self.valX.reindex(X.columns).fillna(self.postFillConstantX)
        return X


    def pre_fill_y(self, y, preFillSelectY):
        if y is None:
            return None
        # Filling missing values using its own stats
        if preFillSelectY in ['constant', 'min', 'max']:
            y = y.fillna(self.preFillConstantY)
        elif preFillSelectY == 'mean':
            try:
                mean = y.mean()
            except:
                pass
            else:
                y = y.fillna(mean)
        elif preFillSelectY == 'median':
            try:
                median = y.median()
            except:
                pass
            else:
                y = y.fillna(median)
        elif preFillSelectY == 'most':
            y = y.fillna(y.mode().iloc[0])
        elif preFillSelectY == 'nearest':
            y = y.interpolate(method='nearest')
            y = y.fillna(method='ffill')
            y = y.fillna(method='bfill')
        elif preFillSelectY in FillMissing.interpolation_methods:
            order = FillMissing.interpolation_methods.index(preFillSelectY) + 1
            try:
                newy = y.interpolate(method=preFillSelectY, limit_area='inside')
                newy = newy.interpolate(method='spline', order=order, limit_direction='both')
            except ValueError:
                self.warning(f"Can't use {preFillSelectY} interpolation for the first fill on this data, it will be filled on the second fill.")
            else: # Defined newy not to change them if ValueError happens
                y = newy
        return y
    
        
    def post_fill_y(self, y, postFillSelectY):
        # Filling the remaining missing values using the stats of old data
        if postFillSelectY != 'none':
            if postFillSelectY in ['constant', 'min', 'max']:
                y = y.fillna(self.postFillConstantY)
            else:
                y = y.fillna(self.valy)
                if postFillSelectY == 'mean':
                    try:
                        mean = y.mean()
                    except:
                        self.valy = self.postFillConstantY
                    else:
                        self.valy = mean
                elif postFillSelectY == 'median':
                    try:
                        median = y.median()
                    except:
                        self.valy = self.postFillConstantY
                    else:
                        self.valy = median
                elif postFillSelectY == 'last':
                    self.valy = y.iloc[-1]
        return y