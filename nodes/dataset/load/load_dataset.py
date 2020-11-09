import pandas as pd
import sys
import json
import numpy as np
from io import StringIO

from utils.config import Config
from utils.utils import myprint as print
from utils.node import Data, Node
from utils.io import InputType

class LoadDataset(Data):
    
    def load(self, path, hasheader, hasTarget, target_col, column_names):
        # * Add more na_values when encountered
        if not path.endswith('.csv'):
            path += '.csv'
        try:
            X = pd.read_csv(path, header=0 if hasheader else None, na_values=['na'], skipinitialspace=True, encoding='utf-8')
        except FileNotFoundError:
            raise FileNotFoundError(f"No such file or directory: '{path}'")

        if hasTarget:
            y = X.iloc[:, target_col]
            X = X.drop([X.columns[target_col]], axis=1)
            if y.isna().all():
                y = None
        else:
            y = None
        

        # Assuring that the columns are the same with the configuration file
        if hasheader:
            # Assuring that they contain the same column names (no more, no less) regardless of the ordering
            if set(X.columns) != set(column_names) or len(X.columns) != len(column_names):
                print('X.columns:', X.columns, '\ncolumn_names:', column_names)
                raise ValueError('Column names of the input does not match with the config file.')
            # If columns are the same, it takes x4 time for (1M, 100) shaped data,
            # even it is not necessary to reindex since they are already the same
            if not (X.columns == column_names).all():
                # Making sure that the columns are in the same order (for DGR and Store nodes)
                X.reindex(column_names)
        else: # * If there is no header, the columns are expected to be in the same order defined in the config file
            X.columns = column_names
            
        return X, y


    def drop_unimportant(self, X:pd.DataFrame, y, removeAllnan:bool, removeAllsame:bool):
        # remove 'all nan' rows
        not_nan_indices = X.notna().any(axis=1)
        X = X.loc[not_nan_indices]
        if y is not None:
            y = y[not_nan_indices]
            
        # remove duplicated rows
        non_duplicate_indices = ~X.duplicated()
        X = X[non_duplicate_indices]
        if y is not None:
            y = y[non_duplicate_indices]
            
        # remove 'all nan' columns
        if removeAllnan:
            X.dropna(axis='columns', how='all', inplace=True)
        
        # remove 'all same' columns
        if removeAllsame and X.shape[0] > 1:
            X = X.loc[:, X.nunique() > 1]
        
        return X.reset_index(drop=True), y


    def function(self, data, configPath, isFile, path, col, hasheader, removeAllnan, removeAllsame, hasTarget):
        
        # Setting up Config Singleton class and getting the column names
        column_names = Config(configPath).columns()
        
        if not path.endswith('.csv'):
            raise ValueError(f"The file to be loaded needs to be a csv file but got {path}")
        
        if isFile:
            # Reading the data from file
            X, y = self.load(path, hasheader, hasTarget, col, column_names)
            print(f'Loaded dataset from {path}', f'X.shape is {X.shape}', f'y is None' if y is None else f'y.shape is {y.shape}')

            # Dropping all nan rows and cols, all same cols (in case they were wanted to be dropped)
            X, y = self.drop_unimportant(X, y, removeAllnan, removeAllsame)

        else:
            # Reading the data from strings of data
            if data.type != InputType.NODERED:
                raise TypeError(f"Input needs to be string coming from node-red while reading from strings of data but got from a '{data.type.name.lower()}' node")
            X, y = self.load(StringIO(data.get()), hasheader, hasTarget, col, column_names)
            print(f'Loaded dataset from incoming data', f'X.shape is {X.shape}', f'y is None' if y is None else f'y.shape is {y.shape}')
            # Dropping all nan rows and cols, all same cols (in case they were wanted to be dropped)
            X, y = self.drop_unimportant(X, y, False, False)

        if X.empty:
            self.clear_status()
            self.warning('Since loaded data was either empty or consisted of all NaN values, it is not transmitted to the next node.')
        else:
            self.send_next_node((X, y))
            self.done()
    