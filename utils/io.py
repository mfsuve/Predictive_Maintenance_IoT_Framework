from utils.utils import myprint as print
from collections.abc import Iterable
from utils.timed_dict import TimedDict


class Input:
    def __init__(self, _output, _type):
        if _type is None:
            ValueError('Each node type needs to be defined')
        self.output = _output
        self.type = _type
        
    def __repr__(self):
        return f'type: {self.type}\n{self.output}'
        

class Output:
    def __init__(self, secs=None):
        self.results = TimedDict(secs)
        
    def add(self, outputs, _type): # type(outputs) will always be tuple
        for out_port, output in enumerate(outputs):
            self.results[out_port] = Input(output, _type)
        return self
    
    def __getitem__(self, out_port):
        return self.results[out_port]