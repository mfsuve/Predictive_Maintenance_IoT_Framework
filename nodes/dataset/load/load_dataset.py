import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node

from sklearn.preprocessing import LabelEncoder

class LoadDataset(Node):
    
    interpolation_methods = ['linear', 'quadratic', 'cubic']
    
    def __init__(self, *args):
        super().__init__(*args)


    def load(self, path, hasheader, target_col):
        # * Add more na_values when encountered
        X = pd.read_csv(path, header=0 if hasheader else None, na_values=['na'])
        r, c = X.shape
        if target_col < 0:
            target_col += c

        y = X.iloc[:, target_col]
        X = X.drop([X.columns[target_col]], axis=1)
        return X, y


    def drop_unimportant(self, X:pd.DataFrame, y, removeAllnan:bool, removeAllsame:bool):
        # remove 'all nan' rows
        not_nan_idices = X.notna().any(axis=1)
        X = X.loc[not_nan_idices]
        y = y[not_nan_idices]
        
        # remove 'all nan' columns
        if removeAllnan:
            X.dropna(axis='columns', how='all', inplace=True)
        
        # remove 'all same' columns
        if removeAllsame:
            X = X.loc[:, X.nunique() > 1]
        
        return X, y

    # TODO: Sürekli gelen veride econding'lerin consistent olması lazım
    # TODO: Bunun için bu enconding kısmı ayrı bir node olarak koyulabilir
    # TODO: Node'a ister misin gibi configuration koymuyorum çünkü eğer ayrı node olarak yaparsam
    # TODO: ilerde WebSocket'ten gelen verileri de direk ona sokabilirim.
        # TODO: Yeni node olarak yapınca eskisini tutup sürekli update ederek mi
        # TODO: yoksa her defasında yeniden mi fitle şeklinde opsiyon koayabilirim.
    def encoding(self, X, y, encode):
        if encode != 'N': # If encoding is set as Simple or OneHot in Node-Red
            le = LabelEncoder()
            if encode == 'S': # Simple Encoding
                cat_cols = X.columns[X.dtypes == 'object'].tolist()
                X[cat_cols] = X[cat_cols].apply(lambda col: le.fit_transform(col))
            else: # OneHot Encoding
                X = pd.get_dummies(X)
            # Always Simple encode y
            y = le.fit_transform(y)
        return X, y


    def function(self, data, path, col, hasheader, encode, fillConstant, fillSelect, removeAllnan, removeAllsame, onlyTest):
        
        # Reading the data
        X, y = self.load(path, hasheader, col)
        print(f'Loaded dataset from {path}', f'X.shape is {X.shape}', f'y.shape is {y.shape}')

        print(f'1: y.sum(): {y.sum()}')

        # Dropping all nan rows and cols, all same cols
        X, y = self.drop_unimportant(X, y, removeAllnan, removeAllsame)

        print(f'2: y.sum(): {y.sum()}')

        # Encoding
        X, y = self.encoding(X, y, encode)
        
        print(f'3: y.sum(): {y.sum()}')
        
        # Filling missing values
        if fillSelect == 'constant':
            X.fillna(fillConstant, inplace=True)
        elif fillSelect == 'mean':
            X.fillna(X.mean(), inplace=True)
        elif fillSelect == 'median':
            X.fillna(X.median(), inplace=True)
        elif fillSelect == 'most':
            X.fillna(X.mode().iloc[0], inplace=True)
        elif fillSelect == 'nearest':
            X.interpolate(method='nearest', inplace=True)
            X.fillna(method='ffill', inplace=True)
            X.fillna(method='bfill', inplace=True)
        elif fillSelect in interpolation_methods:
            order = interpolation_methods.index(fillSelect) + 1
            try:
                X.interpolate(method=fillSelect, limit_area='inside', inplace=True)
                X.interpolate(method='spline', order=order, limit_direction='both', inplace=True)
            except ValueError:
                raise ValueError(f"Can't use {fillSelect} interpolation on {path.split('/')[-1]}. Please try another option.")
        
        self.send_next_node((X, y, onlyTest))
        self.done()
    