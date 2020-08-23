import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node

from sklearn.model_selection import train_test_split as ttsplit


# ? Random state de input olarak verilebilir mi?
class Split(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.inputs = [Data]
        self.type = Node.Type.DATA
    
    def function(self, X, y, onlyTest, testPercentage):
        X_train, X_test, y_train, y_test = ttsplit(X, y, test_size=testPercentage / 100)
        return [(X_train, y_train, onlyTest), (X_test, y_test, True)]
        #      * Use X_train for train depending on the configuraiton
        #      * Use X_test only for testing
    