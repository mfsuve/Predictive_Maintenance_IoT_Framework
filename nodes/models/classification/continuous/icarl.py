import pandas as pd
import sys
import json
import numpy as np
from time import sleep

from utils.utils import nodered_function
from utils.utils import myprint as print

from sklearn.svm import SVC


@nodered_function(data=('X', 'y'))
def icarl(X, y, layerSizes, maxInDataSize, keepDataSize, maxOldNum):
    # for _X, _y in zip(X, y):
    #     pass
    for i in range(5):
        sleep(2)
        yield i
    