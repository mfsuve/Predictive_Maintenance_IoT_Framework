import json
import logging
import enum
from abc import ABCMeta, abstractmethod
from traceback import format_exc
from queue import Queue

from utils.utils import myprint as print, threaded, MyJSONEncoder
from utils.io import Output, Input

log = logging.getLogger('nodered')

# TODO: Weighted KNN for Continuous/Incremental/Online Learning (research)

# TODO: Create Output class #

# ** İlerde her node'u bir Process yapabilirsin
class Node(metaclass=ABCMeta):
    
    # * Defined to be able to differentiate multiple inputs
    class Type(enum.Enum):
        MODEL = 1
        DATA = 2
        NODERED = 3
        # * Can add more Type's later
    
    def __init__(self, id):
        self.id = id
        self.type = None
        # self._running = False
        self.output = Output(secs=1)
        self.__input_queue = Queue()
        
        self.__wrap_function()
        
        
    def run(self, config, prev_node=None, prev_out=None):
        msg = config.pop('msg')
        if prev_node is None:
            print('prev_node is None')
            # Since the data is coming from nodered, I send the actual message
            self.__input_queue.put((config, Input(msg, Node.Type.NODERED)))
        else:  # Data is coming from another pynode, therefore the actual message is irrelevant (it is something like 'this node is done')
            print('prev_node is not None')
            self.__input_queue.put((config, prev_node.output[prev_out]))


    @threaded
    def __wrap_function(self):
        for config, data in self.inputs():
            print(self.name, '** config **:', config, '** data **:', data)
            try:
                self.function(data, **config)
                print(f'self.function is done!')
            except Exception as e: # In case of an exception
                self._error(repr(e) + '\n' + format_exc())


    @abstractmethod
    def function(self, **kwargs):
        raise NotImplementedError()
    
    
    def inputs(self, times=None):
        if times is None:
            for data in iter(self.__input_queue.get, None):
                yield data
        else:
            for i, data in enumerate(iter(self.__input_queue.get, None)):
                if i < times:
                    yield data
                else:
                    break
    

    def _error(self, message=''):
        log.error(json.dumps({'nodeid': self.id, 'error': f'{message}'}))
    
    
    def done(self):
        log.info(json.dumps({'nodeid': self.id, 'done': True}))
        
    
    # TODO: Might save old status with a function like 'old_status'
    def status(self, message):
        log.info(json.dumps({'nodeid': self.id, 'status': f'{message}'}))
    
    
    # TODO: Implement 'warning' function
        
    
    def send_next_node(self, *outputs):
        self.output.add(outputs, self.type)
        log.info(json.dumps({'nodeid': self.id}))
        
    
    def send_nodered(self, *outputs):
        log.info(json.dumps({'nodeid': self.id, 'message': list(outputs)}, cls=MyJSONEncoder))
    
    
    @property
    def name(self):
        return self.__class__.__name__


class Model(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = InputType.MODEL
        
    @abstractmethod
    def predict(self, X):
        raise NotImplementedError()


class Data(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = InputType.DATA
