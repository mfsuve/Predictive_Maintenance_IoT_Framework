from utils.net.utils import Trainable
from utils.net.linear.mlp import MLP
from torch import nn, optim

class Classifier(Trainable):
    def __init__(self, input_size, classes, layers, hid_size=1000, hid_smooth=None, drop=0,
                 batch_norm=True, nl='leakyrelu', gated=False, excitability=False, excit_buffer=False):
        
        super().__init__()
        
        layers = int(layers)
        if layers < 1:
            raise ValueError("The classifier needs to have at least 1 fully-connected layer.")

        # ? Might not necessary
        # Can create Replayer class
        self.replay_targets = 'soft'
        self.KD_temp = 2.0
        
        ######------SPECIFY MODEL------######
        
        self.mlp = MLP(input_size=input_size, output_size=classes, layers=layers, hid_size=hid_size,
                       hid_smooth=hid_smooth, batch_norm=batch_norm, gated=gated, excitability=excitability,
                       excit_buffer=excit_buffer, drop=drop, nl=nl, output='excitable')
        
        
    def train_step(self, epochs, batch_size):
        super().train_step(epochs, batch_size)
        
        
