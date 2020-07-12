import json
import logging
from types import GeneratorType
from abc import ABCMeta, abstractmethod
from traceback import format_exc
from threading import Lock
from queue import Queue

from utils.utils import myprint as print, threaded
from utils.output import Output

log = logging.getLogger('nodered')

# TODO: Weighted KNN for Continuous/Incremental/Online Learning (research)

# TODO: Create Output class #

class Node(metaclass=ABCMeta):
    num_running = 0
    num_running_lock = Lock()
    def __init__(self, id, inputs=None):
        self.id = id
        self._running = False
        self.output = Output(secs=1)
        
        self.__input_queue = Queue()
        self.stream_queue = Queue()
        self.inputs = [] if inputs is None else inputs
        
        self.stream = False
        
        
    @property
    def running(self):
        return self._running
    
    
    @running.setter
    def running(self, running):
        if not self.stream:
            if not self.running and running:
                self.__inc_running()
            elif self.running and not running:
                self.__dec_running()
        # print(f'Setting {self.name} from {"" if self._running else "not "}running to {"" if running else "not "}running')
        self._running = running
    
    
    def run(self, config, prev_node=None, prev_out=None, prev_node_error=None):
        print(f'prev_node: {"None" if prev_node is None else prev_node.name}', f'prev_out: {prev_out}')
        print(f'{self.name} is{"" if self.running else " not"} running.')
        # It doesn't have a previous node, so don't send any incoming data (except node config)
        if prev_out is None: # This is the node that starts our flow
            if self.num_running == 0: # If no nodes are running
                self.running = True
                print(f'prev_out is None - kwargs:', config)
                self.__wrap_function(**config)
            else: # elif not self.running:
                self._error('There are still nodes running.')
        else:
            if not self.running:
                self.__wrap_function(**config)
            if prev_node_error:
                print(f'{self.name} prev_node_error')
                self.__input_queue.put((prev_node.__class__, 'error'))
            else: # For multiple inputs
                if self.stream:
                    print(f'streaming node')
                    self.stream_queue.put(prev_node.output[prev_out])
                else:
                    print(f'not streaming node')
                    self.__input_queue.put((prev_node.__class__, prev_node.output[prev_out]))
                self.running = True;


    @threaded
    def __wrap_function(self, **kwargs):
        try:
            print(self.name, f'kwargs:', kwargs)
            
            if self.stream:
                print('In stream')
                # Streaming nodes should have one and only one input
                _class = self.inputs[0]
                def gen():
                    while True:
                        d = self.stream_queue.get()
                        if d is None:
                            break
                        yield d
                data = gen()
                kwargs.update(_class.format(data))
                
            else:
                print('In not stream')
                _inputs = self.inputs.copy()
                def index(C): # give index where class C occurs in a list of classes (_inputs), even with subclasses
                    for i, _C in enumerate(_inputs):
                        if issubclass(C, _C):
                           return i 
                    return None
                while _inputs: # Loop and get all inputs
                    print(self.name, f'waiting for input...')
                    _class, data = self.__input_queue.get()
                    print(self.name, f'Got an input from {_class.__name__}', 'data:', data)
                    if data == 'error': # Previous node had an error
                        self._prev_error()
                    # Record that the input from _class has been arrived, only accept others if there are.
                    idx = index(_class)
                    if idx is not None:
                        kwargs.update(_class.format(data))
                        _inputs.pop(idx)
            
            try:
                self.function(**kwargs)                             # * self.function will return a generator (e.g. for DGR) if it contains yield in the class implementation
                print(f'self.function is done!')
                self._done()
            except Exception as e:                                  # In case of an exception
                self._error(repr(e) + '\n' + format_exc())
        
        except Exception:
            print(format_exc())
        
    @abstractmethod
    def function(self, **kwargs):
        raise NotImplementedError()
    
    @classmethod
    def format(cls, data):
        raise NotImplementedError()
    

    def _error(self, message=''):
        log.error(json.dumps({'nodeid': self.id, 'error': f'{message}'}))
        self.running = False
        
        
    def _prev_error(self):
        log.info(json.dumps({'nodeid': self.id, 'prev_error': True}))
        self.running = False
    
    
    def _done(self):
        log.info(json.dumps({'nodeid': self.id, 'done': True}))
        self.running = False
        
    
    def status(self, message):
        log.info(json.dumps({'nodeid': self.id, 'status': f'{message}'}))
        
    
    def send_next_node(self, *outputs):
        self.output += outputs
        log.info(json.dumps({'nodeid': self.id}))
        
    
    def send_nodered(self, *outputs):
        log.info(json.dumps({'nodeid': self.id, 'message': list(outputs)}))
    
    
    @classmethod 
    def __dec_running(cls):
        with cls.num_running_lock:
            cls.num_running -= 1


    @classmethod 
    def __inc_running(cls):
        with cls.num_running_lock:
            cls.num_running += 1
            
    
    @property
    def name(self):
        return self.__class__.__name__
        
        
class Data(Node):
    def __init__(self, *args):
        super().__init__(*args)
    
    @classmethod
    def format(cls, data):
        if isinstance(data, GeneratorType):
            return zip(('stream_data',), (data,))
        else:
            return zip(('X', 'y', 'onlyTest'), data)
        

class Model(Node):
    def __init__(self, *args):
        super().__init__(*args, inputs=[Data])                  # TODO: ? Define inputs in the actual pynodes (e.g. LoadDataset, DGR ...)
    
    @classmethod
    def format(cls, data):
        return zip(('model',), data)


class Test(Node):
    def __init__(self, *args):
        super().__init__(*args, inputs=[Data, Model])           # TODO: ? Define inputs in the actual pynodes (e.g. LoadDataset, DGR ...)