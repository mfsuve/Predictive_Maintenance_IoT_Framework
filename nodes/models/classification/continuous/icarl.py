import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Model

class iCaRL(Model):
    def __init__(self, *args):
        super().__init__(*args)
        self.stream = True

    def function(self, stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum):
        # TODO: Implement iCaRL method here
        # TODO: Then, send aps data sequentially here
            # TODO: First aggregate the data, after the conditions are met with the given configurations, continue learning
        # TODO: Finally, try a socket connection to get the data
        for data in stream_data:
            print(f'stream data: {data}')
            yield data
        # for X, y in stream_data:
        #     yield 55
    