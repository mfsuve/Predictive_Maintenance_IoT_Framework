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
   