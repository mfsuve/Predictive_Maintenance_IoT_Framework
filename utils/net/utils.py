import torch
from torch import nn, optim
from abc import ABCMeta, abstractmethod

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')


class Trainable(nn.Module, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.optimizer = None
        self.loss = None

    @abstractmethod
    def train_step(self, epochs, batch_size):
        if self.optimizer is None or self.loss is None:
            raise AttributeError("'optimizer' and 'loss' attributes need to be initialized before training.")


def to_tensor(tensor):
    return torch.from_numpy(tensor).float().to(device)
