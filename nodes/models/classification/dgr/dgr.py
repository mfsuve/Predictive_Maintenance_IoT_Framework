import pandas as pd
import sys
import json
import numpy as np
import copy
import os

from utils.utils import myprint as print
from utils.save_load_utils import add_prefix, get_file_to_load
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
        
        # TODO: Burda node create edilir edilmez load yapılacaksa yap
        # TODO: self.node_config ile config'i alabilirsin
        
        if os.path.isfile('Loss_Hydraulic_Systems.txt'):
            os.remove('Loss_Hydraulic_Systems.txt')


    def __init_data(self, data, taskSize, CLayers, CHidden, CHiddenSmooth, Clr, GZdim, GLayers, GHidden, GHiddenSmooth, Glr):
        self.task_size = taskSize
        num_classes = Config().num_classes
                
        X_in, y_in, encoded = data
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
        self.status(f'{self.size}/{self.task_size} | trained {self.task}')
        return self.size >= self.task_size
                
    
    # * Call only when full
    def reset_data(self):
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
        # Training mode
        self.model.train()
        self.generator.train()
        
        data_loader = DataLoader(SimpleDataset(self.X, self.y), batch_size=batchSize, shuffle=True, num_workers=0, pin_memory=True, drop_last=False)#True)
        
        gen_x = None
        gen_y = None
        gen_scores = None
        scores = None
        
        loss_values = []
        acc_values = []
        
        print(f'epochs: {epochs}', f'batch size: {batchSize}')
        for epoch in range(1, epochs + 1): # ? I added this
            total_correct, total_loss = 0, 0
            for batch, (x, y) in enumerate(data_loader, 1):
                x, y = x.to(device), y.to(device, dtype=torch.int64)
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
            
            loss_values.append(total_loss)
            acc_values.append(total_correct)
        
        # ? train_count might not be necessary
        self.send_nodered(None, {'loss': loss_values, 'accuracy': acc_values, 'train_count': self.task})
        self.send_next_node((self, False))
        self.done()
        

    def predict(self, X):
        self.model.eval()
        return self.model.predict(X)
    
    
    def save(self, folder, prefix, obj=None):
        obj = dict(
            num_classes = self.num_classes,     # To check if proper model
            num_features = self.num_features,   # To check if proper model
        )   
        path = super().save(folder, prefix, obj)
        # Saving pytorch models separately to use torch.save instead of pickle
        torch.save(self.generator.state_dict(), add_prefix('generator.pt', prefix, path))
        torch.save(self.model.state_dict(), add_prefix('classifier.pt', prefix, path))
        
        
    def load(self, path):
        check = [('num_classes', 'number of classes'),
                 ('num_features', 'number of features')]
        obj = super().load(path, check)
        # Updating the dict
        self.__dict__.update(obj)
        # * Saving pytorch models separately to use torch.save instead of pickle
        self.generator.load_state_dict(torch.load(get_file_to_load(path, 'generator.pt')))
        self.model.load_state_dict(torch.load(get_file_to_load(path, 'classifier.pt')))
        # The second parameter True is to indicate loaded,
        # I am doing this to notify the save node to not save it again
        # I am sending this loaded model only for the test node
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
        else:   
            X_in, y_in, encoded = data
            if y_in is None:
                raise ValueError("Input data needs to have target values for training")
            assert isinstance(X_in, pd.DataFrame), "DGR | X always needs to be a DataFrame!"
            self.full = self.append(X_in, y_in)

        while self.full:
            self.status(f'{self.task + 1}. training')
            self.train(epochs, batchSize)
            self.full = self.reset_data()
            