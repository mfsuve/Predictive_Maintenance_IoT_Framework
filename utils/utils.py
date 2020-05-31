import json
import sys
import torch
from pprint import pformat
from traceback import format_exc
from functools import wraps
import logging
from threading import Thread, currentThread


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
myprint(f'Using device {device}')
log = logging.getLogger('nodered')


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
        try:
            callback = args[0].function_end
        except (IndexError, AttributeError):
            callback = None
        try:
            name = f'{args[0].__class__.__name__} class'
        except (IndexError, AttributeError):
            name = f'{func.__name__} function'
        myprint(f'Threading {name}', f'callback: {callback}')
        thread = BaseThread(target=func, callback=callback, name=name, args=args, kwargs=kwargs)
        thread.setDaemon(True)
        thread.start()
        return thread
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
   
 
def make_list_of_tuples(val):
    if not isinstance(val, list):
        if isinstance(val, tuple):
            return [val]
        else:
            return [(val,)]
        
def to_tensor(data):
    return torch.from_numpy(data).float().to(device)
