import pandas as pd
import sys

from utils.utils import myprint as print
from utils.node import Node
from utils.config import Config

from sklearn.preprocessing import MinMaxScaler as MMS, StandardScaler as SS

class MinMaxScaler(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = Node.Type.DATA

        if data.type != Node.Type.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        print(f'MinMax Scaling...')
        return MMS().fit_transform(X), y, onlyTest

class StandardScaler(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.type = Node.Type.DATA

    def function(self, X, y, onlyTest):
        print(f'Standard Scaling...')
        return SS().fit_transform(X), y, onlyTest