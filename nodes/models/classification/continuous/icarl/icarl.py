import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.net.utils import to_tensor, device
from utils.node import Node
from utils.model import Network

import torch

class iCaRL(Node):
    def __init__(self, *args):
        super().__init__(*args)
        self.stream = True


    @property
    def X(self):
        return self._X[:self.size]


    @property
    def y(self):
        return self._y[:self.size]
    
    
    @X.setter
    def X(self, val):
        self._X[:self.size] = val
    
    
    @y.setter
    def y(self, val):
        self._y[:self.size] = val
        
    
    @property
    def model(self):
        if self._model is None:
            self._model = Network(self.feature_size, self.layerSizes, torch.unique(self.y).tolist())
            self._model.to(device)
            # self.num_class = torch.unique(self.y).size().index()
            # self.
        return self._model
    

    def __init_data(self, stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum):
        # [| __________ | __ | __ | __ | __ |]
        #     new data       old data ...
        #  <--------- overall data --------->
        self.maxInDataSize = maxInDataSize
        self.maxOldNum = maxOldNum
        self.layerSizes = layerSizes
        self.insize = 0                 # Size of the actual new coming data
        self.size = maxInDataSize       # Overall train size
        self.remainder = None
        self._model = None
        
        self.keep_size = (maxInDataSize * keepDataSize) // 100
        self.full_size = self.keep_size * maxOldNum + maxInDataSize
        X_in, y_in = next(stream_data)
        self.feature_size = X_in.shape[1]
        self._X = torch.zeros((self.full_size, self.feature_size))
        self._y = torch.zeros(self.full_size)
        return self.append(X_in, y_in)


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
    def reset_data(self):
        # TODO: make categorical **************************************
        tokeep = self._X[self.maxInDataSize-self.keep_size:-self.keep_size]
        
        self._y[self.maxInDataSize:] = self.model(tokeep)
        self._X[self.maxInDataSize:] = tokeep
        
        self.insize = 0
        self.size = min(self.size + self.keep_size, self.full_size)
        if self.remainder is not None:
            remainder = self.remainder
            self.remainder = None
            self.append(*remainder)
            
    
    # TODO: Try to implement the part where 'numClass' can be increased
    def function(self, stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum, numClass):
        
        # * DONE: First, create model
        # * DONE: Implement iCaRL method here
            # * DONE: First aggregate the data, after the conditions are met with the given configurations, continue learning
        # TODO: Then, send aps data sequentially here
        # TODO: Finally, try a socket connection to get the data
        
        full = self.__init_data(stream_data, layerSizes, maxInDataSize, keepDataSize, maxOldNum)
        
        for X_in, y_in in stream_data:
            if full:
                loss = self.model.train(self.X, self.y)
                self.reset_data()
            full = self.append(X_in, y_in)
            
            # yield data
        # for X, y in stream_data:
        #     yield 55
        