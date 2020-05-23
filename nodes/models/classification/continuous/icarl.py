import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print, to_tensor
from utils.node import Model
from utils.nn import create_model

import torch

class iCaRL(Model):
    def __init__(self, *args):
        super().__init__(*args)
        self.stream = True


    @property
    def X(self):
        return self._X[:self.size]


    @property
    def y(self):
        return self._y[:self.size]


    def __init_data(self, stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum):
        self.maxInDataSize = maxInDataSize
        self.maxOldNum = maxOldNum
        self.insize = 0                 # Size of the actual new coming data
        self.size = maxInDataSize       # Overall train size
        self.remainder = None
        
        keepsize = (maxInDataSize * keepDataSize) // 100
        maxsize = keepsize * maxOldNum + maxInDataSize
        X_in, y_in = next(stream_data)
        data_shape = (maxsize, X_in.shape[1])
        self.maxsize = maxsize
        self.keepsize = keepsize
        self._X = torch.zeros(data_shape)
        self._y = torch.zeros(maxsize)
        self.append(X_in, y_in)


    def append(self, X_in, y_in):
        # TODO: shuffle X_in, y_in
        
        X_in, y_in = to_tensor(X_in), to_tensor(y_in)
        input_size = X_in.size()[0]
        if self.insize + input_size > self.maxInDataSize:
            self._X[self.insize:self.maxInDataSize] = X_in[:self.maxInDataSize-self.insize]
            self._y[self.insize:self.maxInDataSize] = y_in[:self.maxInDataSize-self.insize]
            self.remainder = X_in[self.maxInDataSize-self.insize:], y_in[self.maxInDataSize-self.insize:] # TODO: Make this a list of (X, y)'s
            self.insize = self.maxInDataSize
        else:
            self._X[self.insize:self.insize+input_size] = X_in
            self._y[self.insize:self.insize+input_size] = y_in
            self.insize += input_size
        return self.insize >= self.maxInDataSize
                
    
    # * Call only when full
    def reset(self):
        self._X[self.maxInDataSize:] = self._X[self.maxInDataSize-self.keepsize:-self.keepsize]
        
        # TODO: fix y's of old ones (get softmax output from the model)
        self._y[self.maxInDataSize:] = self._y[self.maxInDataSize-self.keepsize:-self.keepsize]
        
        self.insize = 0
        self.size = min(self.size + self.keepsize, self.maxsize)
        if self.remainder is not None:
            remainder = self.remainder
            self.remainder = None
            self.append(*remainder)
            
    
    def train(self):
        pass
        # TODO: Train model here


    def function(self, stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum):
        
        # TODO: Implement iCaRL method here
            # TODO: First aggregate the data, after the conditions are met with the given configurations, continue learning
        # TODO: Then, send aps data sequentially here
        # TODO: Finally, try a socket connection to get the data
        
        self.__init_data(stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum)
        
        for X_in, y_in in stream_data:
            full = self.append(X_in, y_in)
            if full:
                self.train()
                self.reset()
            
            # yield data
        # for X, y in stream_data:
        #     yield 55
        