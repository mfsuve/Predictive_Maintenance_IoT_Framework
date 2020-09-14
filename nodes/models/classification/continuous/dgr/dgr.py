import pandas as pd
import sys
import json
import numpy as np
import copy
import os

from utils.utils import myprint as print
from utils.node import Model
from utils.config import Config
from utils.io import InputType

from utils.net.classifier import Classifier
from utils.net.vae import AutoEncoder
from utils.net.utils import device, SimpleDataset

import torch
from torch.utils.data import DataLoader

class DeepGenerativeReplay(Model):
    def __init__(self, *args):
        super().__init__(*args)
        self.initialized = False
        self.full = False
        
        if os.path.isfile('Loss_Hydraulic_Systems.txt'):
            os.remove('Loss_Hydraulic_Systems.txt')


    def __init_data(self, data, taskSize, CLayers, CHidden, CHiddenSmooth, Clr, GZdim, GLayers, GHidden, GHiddenSmooth, Glr):
        self.task_size = taskSize
        num_classes = Config().num_classes
                
        X_in, y_in = data
        # Getting num_feature from X_in since it might have been onehot encoded
        num_features = X_in.shape[1]
        
        # Storing these variables to make sure a proper model is loaded when loading from disk
        self.num_features = num_features
        self.num_classes = num_classes
        
        if y_in is None:
            raise ValueError("Input data needs to have target values for training")
        self.X = np.zeros((self.task_size, num_features))
        self.y = np.zeros(self.task_size)

        ## * Initializin models (Classifier and Generator)
        #  * Classifier
        self.model = Classifier(input_size=num_features, classes=num_classes, layers=CLayers, hid_size=CHidden,
                                hid_smooth=CHiddenSmooth, name=self.name).to(device)
        self.model.optimizer = torch.optim.Adam(self.model.parameters(), lr=Clr) # Can reset the optimizer after each task?
        #  * Generator (z_dim is set to be square root of the feature size if not specified, can change later)
        self.generator = AutoEncoder(input_size=num_features, z_dim=int(np.sqrt(num_features) if GZdim < 1 else GZdim),
                                     layers=GLayers, hid_size=GHidden, hid_smooth=GHiddenSmooth).to(device)
        self.generator.optimizer = torch.optim.Adam(self.generator.parameters(), lr=Glr) # Can reset the optimizer after each task?
        
        self.size = 0
        self.task = 0
        self.remainder = None
        
        self.prev_model = None
        self.prev_generator = None
        
        full = self.append(X_in, y_in)
        
        self.initialized = True
        return full 


    def append(self, X_in, y_in):
        input_size = X_in.shape[0]
        if self.size + input_size > self.task_size:
            self.X[self.size:] = X_in[:self.task_size-self.size]
            self.y[self.size:] = y_in[:self.task_size-self.size]
            self.remainder = X_in[self.task_size-self.size:], y_in[self.task_size-self.size:]
            self.size = self.task_size
        else:
            self.X[self.size:self.size+input_size] = X_in
            self.y[self.size:self.size+input_size] = y_in
            self.size += input_size
        print(f'DGR | input size: {input_size}', f'DGR | size: {self.size}', f'DGR | full: {self.size >= self.task_size}', f'DGR | task size: {self.task_size}')
        self.status(f'{self.size}/{self.task_size} | trained {self.task}')
        return self.size >= self.task_size
                
    
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
        self.status(f'{self.size}/{self.task_size} | trained {self.task}')
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
        
        print(f'DGR | Number of 1 class: {(self.y == 1).sum()}', f'DGR | Number of 0 class: {(self.y == 0).sum()}')
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
                
            total_correct /= self.task_size
            total_loss /= self.task_size
            
            self.status(f'{self.task}. training | Loss: {total_loss}')
            
            self.send_nodered(None, {'loss': total_loss, 'accuracy': total_correct, 'train_count': self.task})
            
            loss_values.append(total_loss)
            
        self.send_next_node((self, False))
        
        with open('Loss_Hydraulic_Systems.txt', 'a') as file:
            for i in loss_values:
                file.write(f'{i}\n')
            file.write(f'TASK {self.task} msg #1: {(self.y == 1).sum()} | #0: {(self.y == 0).sum()}\n')


    def predict(self, X):
        return self.model.predict(X)
    
    
    def save(self, folder, prefix, timestamp, obj=None):
        obj = dict(
            generator = self.generator,
            model = self.model,
            prev_generator = self.prev_generator,
            prev_model = self.prev_model,
            num_classes = self.num_classes,     # To check if proper model
            num_features = self.num_features,   # To check if proper model
        )   
        super().save(folder, prefix, timestamp, obj)
        
        
    def load(self, path):
        check = [('num_classes', 'number of classes'),
                 ('num_features', 'number of features')]
        obj = super().load(path, check)
        # Updating the dict
        self.__dict__.update(obj)
        # True for loaded, I am doing this to notify the save node to not save it again
        # I am sending this loaded model for the test node
        self.send_next_node((self, True))
        

    def function(self, data, taskSize, CLayers, CHidden, Clr, GZdim, GLayers, GHidden, Glr, epochs, batchSize, CHiddenSmooth=None, GHiddenSmooth=None, loadFrom=None):
        '''Aggregate streaming data, train when full and continue

        INPUT:  - [stream_data]     (tuple of 2x) <np.array> partial input data coming from node-red
                - [taskSize]        <int> # inputs for each task
                - [CLayers]         <int> # layers of classifier
                - [CHidden]         <int> hidden layer sizes of classifier
                - [CHiddenSmooth]   if None, all hidden layers have [CHidden] units, else # of units linearly in-/decreases s.t.
                                      final hidden layer has [CHiddenSmooth] units (if only 1 hidden layer, it has [CHidden] units)
                - []
                                      '''
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        data = data.get()
        
        if not self.initialized:
            self.full = self.__init_data(data, taskSize, CLayers, CHidden, CHiddenSmooth, Clr, GZdim, GLayers, GHidden, GHiddenSmooth, Glr)
            # Loading old model if it is asked
            if loadFrom is not None:
                self.load(loadFrom)
                print(f'DGR | Successfully loaded from {loadFrom}')
            else:
                print(f'DGR | Not loading from any model')
        else:   
            X_in, y_in = data
            if y_in is None:
                raise ValueError("Input data needs to have target values for training")
            assert isinstance(X_in, pd.DataFrame), "DGR | X always needs to be a DataFrame!"
            self.full = self.append(X_in, y_in)

        while self.full:
            self.status(f'{self.task + 1}. training')
            self.train(epochs, batchSize)
            self.full = self.reset_data()
            