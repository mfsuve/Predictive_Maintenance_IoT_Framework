import pandas as pd
import sys
import json
import numpy as np

from utils.config import Config
from utils.utils import myprint as print
from utils.node import Node

class LoadDataset(Node):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.type = Node.Type.DATA


    def load(self, path, hasheader, hasTarget, target_col):
        # * Add more na_values when encountered
        try:
            X = pd.read_csv(path, header=0 if hasheader else None, na_values=['na'], skipinitialspace=True, encoding='utf-8')
        except FileNotFoundError:
            raise FileNotFoundError(f"No such file or directory: '{path}'")

        if hasTarget:
            y = X.iloc[:, target_col]
            X = X.drop([X.columns[target_col]], axis=1)
        else:
            y = None
            
        return X, y


    def drop_unimportant(self, X:pd.DataFrame, y, removeAllnan:bool, removeAllsame:bool):
        # remove 'all nan' rows
        not_nan_idices = X.notna().any(axis=1)
        X = X.loc[not_nan_idices]
        if y is not None:
            y = y[not_nan_idices]
        
        # remove 'all nan' columns
        if removeAllnan:
            X.dropna(axis='columns', how='all', inplace=True)
        
        # remove 'all same' columns
        if removeAllsame and X.shape[0] > 1:
            X = X.loc[:, X.nunique() > 1]
        
        return X.reset_index(drop=True), y.to_numpy() if y is not None else None


    def function(self, data, configPath, isFile, path, col, hasheader, removeAllnan, removeAllsame, hasTarget):
        
        print('LoadDataset | isFile:', isFile)

        # Setting up Config Singleton class and getting the column names
        column_names = Config(configPath).columns()
        
        if isFile:        
            # Reading the data
            X, y = self.load(path, hasheader, hasTarget, col)
            print(f'Loaded dataset from {path}', f'X.shape is {X.shape}', f'y.shape is {y.shape}')

            # Dropping all nan rows and cols, all same cols (in case they were wanted to be dropped)
            X, y = self.drop_unimportant(X, y, removeAllnan, removeAllsame)

            # Assuring that the columns are the same with the configuration file
            if hasheader:
                if set(X.columns) != set(column_names) or len(X.columns) != len(column_names):
                    # print(f'X.columns:', set(X.columns))
                    # print(f'column_names:', set(column_names))
                    raise ValueError('Column names of the input does not match with the config file.')
            else: # * If there is not header, the columns should be in the same order defined in the config file
                X.columns = column_names
        else:
            # TODO: Handle the data coming from websockets
            pass

        
        self.send_next_node((X, y, onlyTest))
        self.done()
    