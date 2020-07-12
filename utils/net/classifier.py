from utils.utils import myprint as print

from utils.net.utils import Trainable
from utils.net.linear.mlp import MLP
from torch import nn, optim
from torch.nn import functional as F

class Classifier(Trainable):
    def __init__(self, input_size, classes, layers, hid_size=1000, hid_smooth=None, drop=0,
                 batch_norm=True, nl='leakyrelu', gated=False, excitability=False, excit_buffer=False):
        
        super().__init__()
        
        layers = int(layers)
        if layers < 1:
            raise ValueError("The classifier needs to have at least 1 fully-connected layer.")

        ######------SPECIFY MODEL------######
        
        self.mlp = MLP(input_size=input_size, output_size=classes, layers=layers, hid_size=hid_size,
                       hid_smooth=hid_smooth, batch_norm=batch_norm, gated=gated, excitability=excitability,
                       excit_buffer=excit_buffer, drop=drop, nl=nl, output='excitable')
        
        self.loss = nn.CrossEntropyLoss(reduction='mean')
        
        
    def forward(self, x):
        return self.mlp(x)
    
    
    def dist_loss(self, scores, target_scores, T=2.):
        """Compute knowledge-distillation (KD) loss given [scores] and [target_scores].

        Both [scores] and [target_scores] should be tensors, although [target_scores] should be repackaged.
        'Hyperparameter': temperature"""

        log_scores_norm = F.log_softmax(scores / T, dim=1)
        targets_norm = F.softmax(target_scores / T, dim=1)

        # Calculate distillation loss (see e.g., Li and Hoiem, 2017)
        KD_loss_unnorm = -(targets_norm * log_scores_norm)
        KD_loss_unnorm = KD_loss_unnorm.sum(dim=1)                      #--> sum over classes
        KD_loss_unnorm = KD_loss_unnorm.mean()                          #--> average over batch

        # normalize
        KD_loss = KD_loss_unnorm * T**2

        return KD_loss
    
        
    def train_batch(self, x, y, gen_x, gen_y, scores, gen_scores, rnt):
        super().train_batch()
        
        y_hat = self(x)
        total_loss = self.loss(y_hat, y)

        predicted = y_hat.detach().argmax(1)
        correct = (predicted == y).sum().item()
        
        if gen_x is not None:
            y_hat = self(gen_x)
            replay_loss = self.dist_loss(y_hat, gen_scores, T=2.0)
            total_loss = rnt * total_loss + (1 - rnt) * replay_loss
        
        total_loss.backward()
        self.optimizer.step()
        
        return total_loss.item(), correct
        