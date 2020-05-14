import pandas as pd
import sys
import json
import numpy as np

from utils.utils import nodered_function
from utils.utils import myprint as print

from sklearn.svm import SVC


@nodered_function(data=('X', 'y'))
def svm(X, y, kernel, degree, C, gammaSelect, gamma):
    gamma = float(gamma) if gammaSelect == 'value' else gammaSelect
    model = SVC(kernel=kernel, degree=int(degree), gamma=gamma, C=float(C), class_weight='balanced')
    print(f'\nTraining the svm model:', f'Shape of X is {X.shape}', f'Shape of y is {y.shape}')
    model.fit(X, y)
    print('End of training')
    return model
    