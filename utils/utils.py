import json
import sys
import numpy as np
from pprint import pformat
from traceback import format_exc
from functools import wraps
import logging
from threading import Thread, currentThread
import os
from datetime import datetime

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
   

def get_path(folder, prefix:str, file, timestamp, default_extension='.pkl'):
    if not default_extension.startswith('.'):
        default_extension = '.' + default_extension
    prefix = prefix.replace(' ', '_')
    if prefix.endswith('_'):
        file = f'{prefix}{file}'
    else:
        file = f'{prefix}_{file}'
    # myprint('*' * 300)
    # myprint('folder:', folder, 'timestamp:', timestamp)
    path = os.path.join(folder, file)
    # myprint('path:', path)
    if timestamp:
        no_ext, ext = os.path.splitext(path)
        ext = ext.strip()
        no_ext = no_ext.strip()
        # myprint('no_ext:', no_ext, 'ext:', ext)
        path = f'{no_ext}_{datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}{ext if len(ext) > 1 else ".pkl"}'
        # myprint('final path:', path)
    return path
