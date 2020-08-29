import enum
from utils.timed_dict import TimedDict


# * Defined to be able to differentiate multiple inputs
class InputType(str, enum.Enum):
    MODEL = 'MODEL'
    DATA = 'DATA'
    NODERED = 'NODERED'
    # * Can add more Type's later


class Input:
    def __init__(self, _output, _type=InputType.NODERED):
        self.output = _output
        self.type = _type
        
    def __repr__(self):
        return f'type: {self.type}\n{self.output}'
        

class Output:
    def __init__(self, secs=None):
        self.results = TimedDict(secs)
        
    def add(self, outputs, _type:InputType): # type(outputs) will always be tuple
        for out_port, output in enumerate(outputs):
            self.results[out_port] = Input(output, _type)
        return self
    
    def __getitem__(self, out_port):
        return self.results[out_port]