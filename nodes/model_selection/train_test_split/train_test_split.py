import pandas as pd
import sys
import json
import numpy as np

from utils.utils import nodered_function

from sklearn.model_selection import train_test_split as ttsplit


# ? Random state de input olarak verilebilir mi?
@nodered_function(data=('X', 'y'))
def split(X, y, testPercentage):
    X_train, X_test, y_train, y_test = ttsplit(X, y, test_size=testPercentage / 100)
    return [(X_train, y_train), (X_test, y_test)]
    