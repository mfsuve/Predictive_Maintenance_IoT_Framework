import json
import logging
from abc import ABCMeta, abstractmethod
from traceback import format_exc
from queue import Queue
import pickle
from typing import Dict

from utils.utils import myprint as print, threaded, MyJSONEncoder
from utils.save_load_utils import get_path_to_model, add_prefix, get_file_to_load
# from utils.io import Output, Input, InputType
from utils.io import Input, InputType

log = logging.getLogger('nodered')

# TODO: Weighted KNN for Continuous/Incremental/Online Learning (research)

# ** İlerde her node'u bir Process yapabilirsin
class Node:
    
    def __init__(self, id, node_config:Dict):
        self.id = id
        self.node_config = node_config
        self.type = InputType.NODERED
        self.__input_queue = Queue()
        self.next_nodes = []
        self.__run()
        
        self.__function = self.__first_called
        
        
    def add_next_nodes(self, nodeids):
        self.next_nodes.append(nodeids)
        
    
    def first_called(self, *args, **kwargs):
        pass
    
    
    def __first_called(self, *args, **kwargs):
        self.first_called(*args, **kwargs)
        self.function(*args, **kwargs)
        self.__function = self.function
        
    
    def function(self, *args, **kwargs):
        raise NotImplementedError
    
    
    @threaded
    def __run(self):
        for data, node_config in iter(self.__input_queue.get, None):
            print(self.name, '** node_config **:', node_config, '** data **:', data)
            try:
                self.__processing()
                self.__function(data, **node_config)
                print(f'{self.name}.function is done!')
            except Exception as e: # In case of an exception
                self.__error(repr(e) + '\n' + format_exc())

    
    def input(self, _input, node_config=None):
        if node_config is None:
            self.__input_queue.put((_input, self.node_config))
        else:
            self.__input_queue.put((_input, node_config))
    

    def __error(self, message=''):
        log.error(json.dumps({'nodeid': self.id, 'error': f'{message}'}))
        
    
    def __processing(self):
        log.info(json.dumps({'nodeid': self.id, 'processing': True}))
    
    
    def done(self):
        log.info(json.dumps({'nodeid': self.id, 'done': True}))
        
    
    def status(self, message):
        log.info(json.dumps({'nodeid': self.id, 'status': f'{message}'}))
        
    
    def clear_status(self):
        log.info(json.dumps({'nodeid': self.id, 'none': True}))
    
    
    def warning(self, *warnings, sep:str='\n'):
        log.info(json.dumps({'nodeid': self.id, 'warning': sep.join(warnings)}))
        
    
    def send_next_node(self, *outputs):
        for i, nodes_on_out in enumerate(self.next_nodes):
            next_node:Node
            try:
                output = outputs[i]
            except IndexError:
                output = None
            if output is not None:
                for next_node in nodes_on_out:
                    next_node.input(Input(output, self.type))
        
    
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
    def save(self, folder, prefix, obj=None):
        if obj is None:
            raise ValueError("Object to save can't be None")
        obj['name'] = self.name
        path = get_path_to_model(folder, self.name)
        with open(add_prefix('model.pkl', prefix, path), 'wb') as file:
            pickle.dump(obj, file, protocol=pickle.HIGHEST_PROTOCOL)
        return path
        # TODO: FutureWarning: pickle support for Storage will be removed in 1.5. Use `torch.save` instead
    
    @abstractmethod
    def load(self, path, check=None, force=False):
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
        path = get_file_to_load(path, 'model.pkl')
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
        if check is not None:
            for key, name in check:
                var = getattr(self, key)
                if obj[key] != var:
                    if force:
                        raise ValueError(f"{name.capitalize()} value of loaded model should be the same with {name} of this model. Expected {var}, Got {obj[key]}.")
                    else:
                        self.warning(f"{name.capitalize()} value of the loaded model is different than this model. Will use {name} vaule of the loaded model as {obj[key]}.")
        return obj

class Data(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = InputType.DATA
