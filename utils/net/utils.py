import torch
from torch import nn, optim
from torch.nn import functional as F
from abc import ABCMeta, abstractmethod
from torch.utils.data import Dataset

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')


class Trainable(nn.Module, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.optimizer = None

    @abstractmethod
    def train_step(self):
        if self.optimizer is None:
            raise AttributeError("'optimizer' and 'loss' attributes need to be initialized before training.")
        self.train()
        self.optimizer.zero_grad()



def to_tensor(tensor):
    return torch.from_numpy(tensor).float()


class SimpleDataset(Dataset):
    def __init__(self, X, y):
        super().__init__()
        self.X = to_tensor(X)
        self.y = to_tensor(y)
        
    def __len__(self):
        return self.X.size()[0]
    
    def __getitem__(self, index):
        if torch.is_tensor(index):
            index = index.tolist()
        return self.X[index, :], self.y[index]
        