from collections import Counter
from os import path
from utils.save_load_utils import add_prefix, get_file_to_load
from lightgbm.engine import train
import pandas as pd
import sys
import json
import numpy as np
from io import StringIO
import lightgbm as lgbm
import warnings
warnings.filterwarnings("ignore")

from utils.config import Config
from utils.utils import myprint as print
from utils.node import Model
from utils.io import InputType


class LightGBMClassifier(Model):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.trained_times = 0
        self.size = 0
        self.remainder = None
        self.task_size = self.node_config['task_size']
        self.model = None
        if 'load_from' in self.node_config:
            self.load(self.node_config['load_from'])
        self.status(f'{self.size}/{self.task_size} | Trained {self.trained_times}')
        
    
    def update_params(self, y):
        '''asking for `y` to see if it is unbalanced'''
        self.params['bagging_fraction'] = self.get_bagging_fraction()
        class_counts = sorted(Counter(y).values())
        self.params['is_unbalance'] = len(class_counts) == 2 and self.is_unbalanced(class_counts)
        print(f"LGBM | is unbalanced: {self.params['is_unbalance']}")
            
    
    def get_bagging_fraction(self):
        x = self.trained_times
        return 0.1 + 0.8 * (1 / (1 + (np.exp(2 - x / 4)))) # Created using sigmoid function https://www.desmos.com/calculator/lkpcwzhzxf?lang=tr
    
    
    def is_unbalanced(self, class_counts):
        [min, max] = class_counts
        x = min + max
        print(f"LGBM | x = min + max: {min} + {max} = {x}")
        return (max / min) >= (500 / (x + 100) + 3) # Created using the function on the bottom https://www.desmos.com/calculator/lkpcwzhzxf?lang=tr
            
    
    def first_called(self, data, task_size, max_depth, num_leaves, num_iterations, learning_rate, load_from=None):
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        config = Config()
        X, y, encoded = data.get()
        self.params = {
            'objective': 'binary' if config.num_classes <= 2 else 'multiclass',
            'num_class': 1 if config.num_classes <= 2 else config.num_classes,
            'metric': 'binary' if config.num_classes <= 2 else 'multiclass',
            'max_depth': max_depth,
            'num_leaves': num_leaves,
            'tree_learner': 'voting',
            'num_iterations': num_iterations,
            'learning_rate': learning_rate,
            'n_jobs': -1,
            'verbose': -1
            # 'feature_fraction': 0.8,
            # 'bagging_freq': 10
        }
        self.params['categorical_column'] = ','.join(str(i) for i, col in enumerate(config.columns()) if config.is_categoric(col))
        # Allocating memory for self.X and self.y
        num_features = X.shape[1]
        if y is None:
            raise ValueError("Input data needs to have target values for training")
        self.X = np.zeros((self.task_size, num_features))
        self.y = np.zeros(self.task_size)
        
        if self.params['objective'] == 'binary':
            def accuracy(preds, train_data):
                labels = train_data.get_label()
                return 'accuracy', np.mean(labels == (preds > 0.5)), True
        else:
            def accuracy(preds, train_data):
                labels = train_data.get_label()
                print(f"LGBM | labels.shape: {labels.shape}", f"LGBM | preds.shape: {preds.shape}")
                return 'accuracy', np.mean(np.argmax(np.reshape(preds, (config.num_classes, -1)).T, axis=1) == labels), True
        self.accuracy = accuracy
        
    
    def train(self):
        self.size = 0
        self.trained_times += 1
        self.update_params(self.y)
        self.status(f"Training...")
        
        print(f"LGBM | Training params:", self.params)
        
        evals_result = {}
        train_set = lgbm.Dataset(self.X, self.y)
        self.model = lgbm.train(self.params,
                                init_model=self.model,                          # * Incremental training
                                train_set=train_set,                            # * Train on train set
                                valid_sets=[train_set],                         # * Eval on train set
                                valid_names=['train'],
                                feval=self.accuracy,
                                evals_result=evals_result,                      # * Store eval results in this dict
                                keep_training_booster=True,                     # * Keep booster for increamental training
                                num_boost_round=self.params['num_iterations'],
                                verbose_eval=False) 
        
        # print(f"LGBM | evals_result", evals_result)
        # print(f"LGBM | predictions", self.model.predict(self.X))
        
        msg = {'train_title': f"Trained {self.trained_times} times"}
        for metric, values in evals_result['train'].items():
            if 'accuracy' == metric:
                msg['accuracy'] = values
            else:
                msg['loss'] = values
        
        print(f"LGBM | out msg:", msg)
        
        self.send_nodered(None, msg)
        self.send_next_node((self, False))
        self.done()
        
    
    def predict(self, X):
        preds = self.model.predict(X)
        if self.params['objective'] == 'binary':
            return (preds > 0.5).astype(int)
        else:
            return np.argmax(preds, axis=1)
        
    
    def save(self, folder, prefix, obj=None):
        path = super().save(folder, prefix, {})
        self.model.save_model(add_prefix('lgbm.txt', prefix, path))
    
    
    def load(self, path):
        self.model = lgbm.Booster(model_file=get_file_to_load(path, 'lgbm.txt'), silent=True)
        self.send_next_node((self, True))
    
    
    def append(self, X:pd.DataFrame, y:pd.Series):
        input_size = X.shape[0]
        if self.size + input_size > self.task_size:
            self.X[self.size:] = X[:self.task_size-self.size]
            self.y[self.size:] = y[:self.task_size-self.size]
            self.remainder = X[self.task_size-self.size:], y[self.task_size-self.size:]
            self.size = self.task_size
        else:
            self.X[self.size:self.size+input_size] = X
            self.y[self.size:self.size+input_size] = y
            self.size += input_size
        self.status(f'{self.size}/{self.task_size} | Trained {self.trained_times}')
        return self.size >= self.task_size
    
    
    # * Call only when full
    def append_remainder(self):
        # * Resetting size and appending the remainder from previous tasks (if any)
        if self.remainder is not None:
            remainder = self.remainder
            self.remainder = None
            return self.append(*remainder)
        self.status(f'{self.size}/{self.task_size} | Trained {self.trained_times}')
        return False
    
    
    def function(self, data, task_size, max_depth, num_leaves, num_iterations, learning_rate, load_from=None):
        
        if data.type != InputType.DATA:
            raise TypeError(f"Input needs to be a data coming from a data node but got '{data.type.name.lower()}'")
        
        X, y, encoded = data.get()
        if y is None:
            raise ValueError(f"Target values need to be set before training")
        
        full = self.append(X, y)
        while full:
            self.train()
            full = self.append_remainder()
            
    