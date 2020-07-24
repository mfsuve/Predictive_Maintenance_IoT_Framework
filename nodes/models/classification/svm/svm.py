import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node

from sklearn.svm import SVC

class SVM(Node):
    def __init__(self, *args):
        super().__init__(*args)

    def function(self, X, y, onlyTest, kernel, degree, C, gammaSelect, gamma):
        # TODO: When onlyTest is True, expect this node to be configured using pretrained model (this is not a stream node, otherwise there would be no model to test on)
        gamma = float(gamma) if gammaSelect == 'value' else gammaSelect
        model = SVC(kernel=kernel, degree=int(degree), gamma=gamma, C=float(C), class_weight='balanced')
        print(f'\nTraining the svm model:', f'Shape of X is {X.shape}', f'Shape of y is {y.shape}')
        model.fit(X, y)
        print('End of training')
        return model
    