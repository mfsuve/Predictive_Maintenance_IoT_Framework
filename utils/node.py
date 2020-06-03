import json
import logging
from types import GeneratorType
from abc import ABCMeta, abstractmethod
from traceback import format_exc
from threading import Lock
from queue import Queue

from utils.utils import myprint as print, make_list_of_tuples, threaded
from utils.timed_dict import TimedDict

log = logging.getLogger('nodered')

class Node(metaclass=ABCMeta):
    num_running = 0
    num_running_lock = Lock()
    def __init__(self, id, topic, end=False, inputs=None, stream=False):
        self.id = id
        self.topic = topic
        self._running = False
        self.results = TimedDict(1)
        self.__input_queue = Queue()
        self.stream_queue = Queue()
        self.end = end
        self.inputs = [] if inputs is None else inputs
        self.stream = stream # * If streaming (always running for storing some internal state), only one input is allowed
        
        
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
        print(f'Setting {self.name} from {"" if self._running else "not "}running to {"" if running else "not "}running')
        self._running = running
    
    
    # Will be called after self.function ends
    def function_end(self, outputs):
        print(f'Data that will be sent from node {self.id} ({self.name}):', outputs)
        if outputs is not None:
            if not isinstance(outputs, list): # In case of an exception
                self._error(outputs)
            elif self.end: # This is an end node, send this value to node-red
                if isinstance(outputs[0][0], (GeneratorType, map)): # Send sequential results #!(not tested)
                    for i, output in enumerate(outputs[0][0]):
                        self._done(str(output), cont=i+1)
                    self._done()
                else:
                    self._done(str(outputs[0][0]))
            elif isinstance(outputs[0][0], (GeneratorType, map, filter, zip)): # Save sequential results (in case of a generator)
                for i, gen_output in enumerate(outputs[0][0]):      # Generator loop
                    print('gen_output:', gen_output)
                    gen_output = make_list_of_tuples(gen_output)    # Make sure output is a list of tuples
                    for out, output in enumerate(gen_output):       # Saving all outputs for all output ports
                        self.results[out] = output
                    self._done(cont=i+1)
                print('Done all together')
                self._done()
            else:
                for out, output in enumerate(outputs):
                    self.results[out] = output
                self._done()
        else: # previous node had an error
            self._done('error')
            
    
    def run(self, config, prev_node=None, prev_out=None, prev_node_error=None):
        print(f'prev_node: {"None" if prev_node is None else prev_node.name}', f'prev_out: {prev_out}')
        print(f'{self.name} is{"" if self.running else " not"} running.')
        # It doesn't have a previous node, so don't send any incoming data (except node config)
        if prev_out is None: # This is the node that starts our flow
            if self.num_running == 0: # If no nodes are running
                # print(f'before self.num_running: {self.num_running}')
                self.running = True
                # print(f'after self.num_running: {self.num_running}')
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
                    self.stream_queue.put(prev_node.results[prev_out])
                else:
                    print(f'not streaming node')
                    self.__input_queue.put((prev_node.__class__, prev_node.results[prev_out]))
                self.running = True;


    @threaded
    def __wrap_function(self, **kwargs):
        try:
            print(self.name, f'kwargs:', kwargs)
            
            if self.stream:
                print('In stream')
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
                        return None
                    # Record that the input from _class has been arrived, only accept others if there are.
                    idx = index(_class)
                    if idx is not None:
                        kwargs.update(_class.format(data))
                        _inputs.pop(idx)
            
            returned = None
            try:
                returned = self.function(**kwargs)
            except Exception as e:                                  # In case of an exception
                return repr(e) + '\n' + format_exc()
            print('returned:', returned)
            if returned is None:                                    # In case nothing returns
                return []
            return make_list_of_tuples(returned)                    # In case one out returns
        
        except Exception:
            print(format_exc())
            return []
        
    @abstractmethod
    def function(self, **kwargs):
        raise NotImplementedError()
    
    @classmethod
    def format(cls, data):
        raise NotImplementedError()
    

    def _error(self, msg=''):
        log.error(json.dumps({'nodeid': self.id, 'error': f'{msg}'}))
        self.running = False
        print(f'Error at {self.id}', f'{self.num_running} running nodes')
        
    
    def _done(self, msg=None, cont=None):
        to_send = dict(nodeid=self.id)
            
        if msg is not None:
            to_send['msg'] = msg
            print(f'Node {self.id} sent this message:', msg)            
        
        if cont is not None:
            to_send['cont'] = cont
            print(f'Done and continue {cont}. times {self.id}', f'{self.num_running} running nodes')
        else:
            self.running = False
            print(f'Done {self.id}', f'{self.num_running} running nodes')
        
        log.info(json.dumps(to_send))
        
    
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
    def __init__(self, id):
        super().__init__(id, topic='data')
    
    @classmethod
    def format(cls, data):
        if isinstance(data, GeneratorType):
            return zip(('stream_data',), (data,))
        else:
            return zip(('X', 'y'), data)
        

class Model(Node):
    def __init__(self, id):
        super().__init__(id, topic='model', inputs=[Data])
    
    @classmethod
    def format(cls, data):
        return zip(('model',), data)


class Test(Node):
    def __init__(self, id):
        super().__init__(id, topic='test', end=True, inputs=[Data, Model])