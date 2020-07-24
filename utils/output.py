from utils.utils import myprint as print
from collections.abc import Iterable
from utils.timed_dict import TimedDict
import enum


# * Might not be necessary
# * will delete later
class Output:
    def __init__(self, secs=None):
        self.results = TimedDict(secs)
        
    def __add__(self, outputs): # type(outputs) will always be tuple
        for out_port, output in enumerate(outputs):
            self.results[out_port] = output
        return self
    
    def __getitem__(self, out_port):
        return self.results[out_port]