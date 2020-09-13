import json
import logging
from abc import ABCMeta, abstractmethod
from traceback import format_exc
from queue import Queue
import pickle

from utils.utils import myprint as print, threaded, MyJSONEncoder, get_path, make_sure_folder_exists
from utils.io import Output, Input, InputType

log = logging.getLogger('nodered')

# TODO: Weighted KNN for Continuous/Incremental/Online Learning (research)

# ** İlerde her node'u bir Process yapabilirsin
class Node(metaclass=ABCMeta):
    
    def __init__(self, id):
        self.id = id
        self.type = InputType.NODERED
        self.output = Output(secs=1)
        self.__input_queue = Queue()
        
        self.__wrap_function()
        
        
    def run(self, config, prev_node=None, prev_out=None):
        msg = config.pop('msg')
        if prev_node is None:
            print('prev_node is None')
            # Since the data is coming from nodered, I send the actual message
            self.__input_queue.put((config, Input(msg)))
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
        
    
    def clear_status(self):
        log.info(json.dumps({'nodeid': self.id, 'none': True}))
    
    
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
    
    @abstractmethod
    def save(self, folder, prefix, timestamp, obj=None):
        if obj is None:
            raise ValueError("Object to save can't be None")
        obj['name'] = self.name
        make_sure_folder_exists(folder)
        with open(get_path(folder, prefix, self.name, timestamp), 'wb') as file:
            pickle.dump(obj, file, protocol=pickle.HIGHEST_PROTOCOL)
        # TODO: FutureWarning: pickle support for Storage will be removed in 1.5. Use `torch.save` instead
    
    @abstractmethod
    def load(self, path, check):
        '''
        Arguments
        ===
        ---
        ### path
        > Path to load model from
        ---
        ### check
        > Variables to check to have the same value. Expected as a list of tuples where the first 
        element of the tuple is the actual variable name and the second element is a short explanation of it.
        
        ##### Example
            `check = [('num_classes', 'number of classes'), ('num_features', 'number of features')]`
        '''
        # Loading and assuring that the correct model is loaded (same type, correct format, etc.)
        try:
            with open(path, 'rb') as file:
                obj = pickle.load(file)
                if not isinstance(obj, dict):
                    raise ValueError(f"{path} needs to contain a dictionary for loading the model")
                if 'name' not in obj:
                    raise ValueError(f"{path} needs to contain model information saved using 'save' node")
                if obj['name'] != self.name:
                    raise ValueError(f"{obj['name']} type model can not be loaded into {self.name} type model")
        except FileNotFoundError:
            raise FileNotFoundError(f"No such file or directory to load a model: '{path}'")
        # Checking necessary parameters, if they are equal
        for key, name in check:
            var = getattr(self, key)
            if obj[key] != var:
                raise ValueError(f"{name.capitalize()} of loaded model should be the same with {name} of this model. Expected {var}, Got {obj[key]}")
        return obj

class Data(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = InputType.DATA
