import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Model

class iCaRL(Model):
    def __init__(self, pool, id):
        super().__init__(pool, id)
        self.stream = True

    def function(self, stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum):
        for data in stream_data:
            print(f'stream data: {data}')
            yield data
        # for X, y in stream_data:
        #     yield 55
    