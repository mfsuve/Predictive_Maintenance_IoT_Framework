import numpy as np
from torch import nn
from utils.net.linear.layers import fc_layer


class MLP(nn.Module):
    '''Module for a multi-layer perceptron (MLP).

    Input:  [batch_size] x ... x [size_per_layer[0]] tensor
    Output: (tuple of) [batch_size] x ... x [size_per_layer[-1]] tensor'''

    def __init__(self, input_size=1000, output_size=10, size_per_layer=None, layers=2, hid_size=1000, hid_smooth=None, drop=0, batch_norm=True,
                 nl="relu", bias=True, excitability=False, excit_buffer=False, gated=False, output='normal'):
        '''sizes: 0th=[input], 1st=[hid_size], ..., 1st-to-last=[hid_smooth], last=[output].
        [input_size]       # of inputs
        [output_size]      # of units in final layer
        [layers]           # of layers
        [hid_size]         # of units in each hidden layer
        [hid_smooth]       if None, all hidden layers have [hid_size] units, else # of units linearly in-/decreases s.t.
                             final hidden layer has [hid_smooth] units (if only 1 hidden layer, it has [hid_size] units)
        [size_per_layer]   None or <list> with for each layer number of units (1st element = number of inputs)
                                --> overwrites [input_size], [output_size], [layers], [hid_size] and [hid_smooth]
        [drop]             % of each layer's inputs that is randomly set to zero during training
        [batch_norm]       <bool>; if True, batch-normalization is applied to each layer
        [nl]               <str>; type of non-linearity to be used (options: "relu", "leakyrelu", "none")
        [gated]            <bool>; if True, each linear layer has an additional learnable gate
        [output]           <str>; if has - "normal", final layer is same as all others
                                         - "excitable", final layer is excitable
                                              --> overwrites excitability and excit_buffer'''

        super().__init__()
        self.output = output
        
        if size_per_layer is None:
            hidden_sizes = []
            if layers < 1:
                size_per_layer = []
            else:
                if layers > 1:
                    if hid_smooth is None:
                        hidden_sizes = [int(hid_size) for _ in range(layers - 1)]
                    else:
                        hidden_sizes = [int(x) for x in np.linspace(hid_size, hid_smooth, num=layers-1)]
                size_per_layer = [input_size] + hidden_sizes + [output_size]
        
        self.size_per_layer = size_per_layer
        num_layers = len(size_per_layer) - 1
        
        if num_layers < 1:
            self.layers = [nn.Identity()]
        else:
            self.layers = [fc_layer(insize, outsize, drop=drop, bias=bias, gated=gated, excitability=excitability,
                                    excit_buffer=True if (i == num_layers - 1 and 'excitable' in output) else excit_buffer,
                                    nl='none' if (i == num_layers - 1 and not 'normal' in output) else nl,
                                    batch_norm=False if (i == num_layers - 1 and not 'normal' in output) else batch_norm)
                           for i, (insize, outsize) in enumerate(zip(size_per_layer, size_per_layer[1:]))]
        
        for i, layer in enumerate(self.layers[:-1]):
            setattr(self, f'fcLayer{i+1}', layer)
        setattr(self, f'outLayer', self.layers[-1])
            
            

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x
    