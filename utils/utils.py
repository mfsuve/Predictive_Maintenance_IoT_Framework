import json
import sys
from pprint import pformat
from traceback import format_exc
from functools import wraps
import logging
from threading import Thread, currentThread

log = logging.getLogger('nodered')


class BaseThread(Thread):
    def __init__(self, callback=None, *args, **kwargs):
        target = kwargs.pop('target')
        super().__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target

    def target_with_callback(self, *args, **kwargs):
        name = currentThread().name
        myprint(f'Running {name} in BaseThread')
        result = self.method(*args, **kwargs)
        myprint(f'Result coming from {name} in BaseThread:', result)
        if self.callback is not None:
            myprint(f'Calling back {self.callback.__name__} function for {name} in BaseThread')
            self.callback(result)
            
            
def threaded(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            callback = args[0].function_end
        except (IndexError, AttributeError):
            callback = None
        try:
            name = f'{args[0].__name__} class'
        except (IndexError, AttributeError):
            name = f'{func.__name__} function'
        myprint(f'Threading {name}', f'callback: {callback}', 'args:', args, 'kwargs:', kwargs)
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
