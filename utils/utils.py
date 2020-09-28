import json
import sys
import numpy as np
from pprint import pformat
from traceback import format_exc
from functools import wraps
import logging
from threading import Thread, currentThread
import os

log = logging.getLogger('nodered')


# * Works with numpy typed inputs
class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super().default(obj)
        

class BaseThread(Thread):
    def __init__(self, callback=None, *args, **kwargs):
        target = kwargs.pop('target')
        super().__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target

    def target_with_callback(self, *args, **kwargs):
        name = currentThread().name
        result = self.method(*args, **kwargs)
        if self.callback is not None:
            self.callback(result)
            
            
def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = BaseThread(target=func, callback=None, name=func.__name__, args=args, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()
        return thread
    return wrapper


def after(first):
    def wrapper(second):
        temp = None
        def sub(*args, **kwargs):
            nonlocal temp
            first(*args, **kwargs)
            temp = second
            return func(*args, **kwargs)
        def func(*args, **kwargs):
            return temp(*args, **kwargs)
        temp = sub
        return func
    return wrapper


def myprint(*args, end='', sep='\n'):
    final_string = '\n'
    for s in args:
        if isinstance(s, str):
            final_string += s + sep
        else:
            final_string += pformat(s) + sep
    final_string += end
    log.warning(final_string)
    

def make_sure_folder_exists(pathname):
    if not os.path.isdir(pathname):
        os.makedirs(pathname)
        myprint(f' * {pathname} folder is created.')
    return pathname
   

def combine_data(_X, _y):
    '''Combines X and y into a numpy array'''
    X = np.zeros((_X.shape[0], _X.shape[1] + 1))
    X[:, -1] = _y
    X[:, :-1] = _X
    return X
    