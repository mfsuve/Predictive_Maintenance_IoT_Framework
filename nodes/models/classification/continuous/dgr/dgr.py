import pandas as pd
import sys
import json
import numpy as np
import copy
import os

from utils.utils import myprint as print
from utils.node import Model
from utils.net.classifier import Classifier
from utils.net.vae import AutoEncoder
from utils.net.utils import device, SimpleDataset

import torch
from torch.utils.data import DataLoader

class DeepGenerativeReplay(Model):
    def __init__(self, *args):
        super().__init__(*args)
        self.stream = True
        
        if os.path.isfile('loss.txt'):
            os.remove('loss.txt')


    def __init_data(self, stream_data, taskSize, CLayers, CHidden, CHiddenSmooth, Clr, GZdim, GLayers, GHidden, GHiddenSmooth, Glr, classes):
        self.taskSize = taskSize
        self.classes = classes
                
        X_in, y_in, onlyTest = next(stream_data)
        self.feature_size = X_in.shape[1]
        self.X = np.zeros((self.taskSize, self.feature_size))
        self.y = np.zeros(self.taskSize)

        ## * Initializin models (Classifier and Generator)
        #  * Classifier
        self.model = Classifier(input_size=self.feature_size, classes=classes, layers=CLayers, hid_size=CHidden,
                                 hid_smooth=CHiddenSmooth).to(device)
        self.model.optimizer = torch.optim.Adam(self.model.parameters(), lr=Clr) # Can reset the optimizer after each task?
        #  * Generator (z_dim is set to be square root of the feature size if not specified, can change later)
        self.generator = AutoEncoder(input_size=self.feature_size, z_dim=int(np.sqrt(self.feature_size) if GZdim < 1 else GZdim),
                                        layers=GLayers, hid_size=GHidden, hid_smooth=GHiddenSmooth).to(device)
        self.generator.optimizer = torch.optim.Adam(self.generator.parameters(), lr=Glr) # Can reset the optimizer after each task?
        
        self.size = 0
        self.task = 0
        self.remainder = None
        
        self.prev_model = None
        self.prev_generator = None
        
        full = False
        if not onlyTest:
            full = self.append(X_in, y_in)
        
        # TODO: Get predictions
        
        return full 


    def append(self, X_in, y_in):
        input_size = X_in.shape[0]
        if self.size + input_size > self.taskSize:
            self.X[self.size:] = X_in[:self.taskSize-self.size]
            self.y[self.size:] = y_in[:self.taskSize-self.size]
            self.remainder = X_in[self.taskSize-self.size:], y_in[self.taskSize-self.size:]
            self.size = self.taskSize
        else:
            self.X[self.size:self.size+input_size] = X_in
            self.y[self.size:self.size+input_size] = y_in
            self.size += input_size
        print(f'DGR | input size: {input_size}', f'DGR | size: {self.size}', f'DGR | full: {self.size >= self.taskSize}', f'DGR | task size: {self.taskSize}')
        self.status(f'{self.size}/{self.taskSize} | trained {self.task}')
        return self.size >= self.taskSize
                
    
    # * Call only when full
    def reset_data(self):
        print(f'DGR | reset_data()')
        # * copying previous model and generator
        self.prev_model = copy.deepcopy(self.model).eval()
        self.prev_generator = copy.deepcopy(self.generator).eval()
        # * Resetting size and appending the remainder from previous tasks (if any)
        self.size = 0
        if self.remainder is not None:
            remainder = self.remainder
            self.remainder = None
            return self.append(*remainder)
        else:
            self.status(f'{self.size}/{self.taskSize} | trained {self.task}')
        return False
            
            
    def train(self, epochs, batchSize):
        self.task += 1
        print(f'task: {self.task}')
        # Training mode
        self.model.train()
        self.generator.train()
        
        data_loader = DataLoader(SimpleDataset(self.X, self.y), batch_size=batchSize, shuffle=True, num_workers=0, pin_memory=True, drop_last=False)#True)
        
        gen_x = None
        gen_y = None
        gen_scores = None
        scores = None
        
        loss_values = []
        
        print(f'epochs: {epochs}', f'batch size: {batchSize}')
        for epoch in range(1, epochs + 1): # ? I added this
            total_correct, total_loss = 0, 0
            print(f'{epoch:>5} Epoch')
            for batch, (x, y) in enumerate(data_loader, 1):
                x, y = x.to(device), y.to(device, dtype=torch.int64)
                print(f'{batch:>9} Batch')
                if self.prev_generator is not None:
                    gen_x = self.prev_generator.sample(batchSize)
                    gen_scores = self.prev_model(gen_x)
                loss, correct = self.model.train_batch(x, y, gen_x=gen_x, gen_y=gen_y, scores=scores, gen_scores=gen_scores, rnt=1./self.task)
                self.generator.train_batch(x, y, gen_x=gen_x, gen_y=gen_y, scores=scores, gen_scores=gen_scores, rnt=1./self.task)
                
                total_correct += correct
                total_loss += loss
                
            total_correct /= self.taskSize
            total_loss /= self.taskSize
            
            self.status(f'{self.task}. training | Loss: {total_loss}')
            
            loss_values.append(total_loss)
        
        with open('loss.txt', 'a') as file:
            for i in loss_values:
                file.write(f'{i}\n')
            file.write(f'TASK {self.task}\n')


    def function(self, stream_data, taskSize, CLayers, CHidden, Clr, GZdim, GLayers, GHidden, Glr, epochs, batchSize, classes, CHiddenSmooth=None, GHiddenSmooth=None):
        '''Aggregate streaming data, train when full and continue

        INPUT:  - [stream_data]     (tuple of 2x) <np.array> partial input data coming from node-red
                - [taskSize]        <int> # inputs for each task
                - [CLayers]         <int> # layers of classifier
                - [CHidden]         <int> hidden layer sizes of classifier
                - [CHiddenSmooth]   if None, all hidden layers have [CHidden] units, else # of units linearly in-/decreases s.t.
                                      final hidden layer has [CHiddenSmooth] units (if only 1 hidden layer, it has [CHidden] units)
                - []
                                      '''
        # TODO: Next, preprocess data
        
        indata = 1
        full = self.__init_data(stream_data, taskSize, CLayers, CHidden, CHiddenSmooth, Clr, GZdim, GLayers, GHidden, GHiddenSmooth, Glr, classes)
        while True:
            indata += 1
            while full:
                print(f'DGR | Full, will train...')
                self.status(f'{self.task + 1}. training')
                self.train(epochs, batchSize)
                print(f'DGR | yielding model...')
                yield self.model
                print(f'DGR | Resetting data')
                full = self.reset_data()
                print(f'DGR | full: {full} after resetting')
            try:
                X_in, y_in, onlyTest = next(stream_data)
                print(f'DGR | Got {indata}. data', 'Only for testing' if onlyTest else 'For training and testing')
            except StopIteration:
                print(f'DGR | Stop Iteration')
                break
            if not onlyTest:
                print(f'DGR | Appending incoming data')
                full = self.append(X_in, y_in)
            