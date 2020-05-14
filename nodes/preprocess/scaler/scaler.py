import pandas as pd
import sys

from utils.utils import nodered_function
from utils.utils import myprint as print

from sklearn.preprocessing import MinMaxScaler, StandardScaler

import logging


@nodered_function(data=('X', 'y'))
def minmax_scaler(X, y):
    print(f'MinMax Scaling...')
    return MinMaxScaler().fit_transform(X), y


@nodered_function(data=('X', 'y'))
def standard_scaler(X, y):
    print(f'Standard Scaling...')
    return StandardScaler().fit_transform(X), y