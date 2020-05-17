import json
import logging
from types import GeneratorType
from multiprocessing import Lock, Queue

from utils.utils import nodered_function
from utils.utils import myprint as print
from utils.timed_dict import TimedDict

log = logging.getLogger('nodered')

class Node:
    num_running = 0
    num_running_lock = Lock()
    def __init__(self, pool, id, topic, function, end):
        self.pool = pool
        self.id = id
        self.topic = topic
        self.function = function
        self._running = False
        self.results = TimedDict(1)
        self.queue = Queue()
        self.end = end
        
        
    @property
    def running(self):
        return self._running
    
    
    @running.setter
    def running(self, running):
        if not self.running and running:
            self._inc_running()
        elif self.running and not running:
            self._dec_running()
        self._running = running
    
    
    # Callback result function of node threads
    def _function_end(self, outputs):
        if outputs is not None:
            print(f'Data will be sent from node {self.id} ({self.name}):', outputs)
            if not isinstance(outputs, list): # In case of an exception
                self._error(outputs)
            elif self.end: # This is an end node, send this value to node-red
                if isinstance(outputs[0][0], (GeneratorType, map)): # Send sequential results #!(not tested)
                    for i, output in enumerate(outputs[0][0]):
                        self._done(str(output), cont=i+1)
                    self._done()
                else:
                    self._done(str(outputs[0][0]))
            elif isinstance(outputs[0][0], (GeneratorType, map)): # Save sequential results (in case of a generator)
                for i, gen_output in enumerate(outputs[0][0]):
                    if not isinstance(gen_output, list):
                        if isinstance(gen_output, tuple):
                            gen_output = [gen_output]
                        else:
                            gen_output = [(gen_output,)]
                    for out, output in enumerate(gen_output):
                        self.results[out] = output
                    self._done(cont=i+1)
                self._done()
            else:
                for out, output in enumerate(outputs):
                    self.results[out] = output
                self._done()
        else: # previous node had an error
            self._done('error')
            
    
    def run(self, config, prev_node=None, prev_out=None, prev_node_error=None):
        print(f'prev_node: {"None" if prev_node is None else prev_node.name}', f'prev_out: {prev_out}')
        # It doesn't have a previous node, so don't send any incoming data (except node config)
        if prev_out is None: # This is the node that starts our flow
            if self.num_running == 0: # If no nodes are running
                print(f'before self.num_running: {self.num_running}')
                self.running = True
                print(f'after self.num_running: {self.num_running}')
                print(f'kwargs:', config)
                self.pool.apply_async(self.function, kwds=config, callback=self._function_end)
            else: # elif not self.running:
                print('Error: There are still nodes running.')
                self._error('There are still nodes running.')
        else:
            print(f'{self.function.__name__} is{"" if self.running else " not"} running.')
            if not self.running: # For multiple inputs
                self.running = True;
                self.pool.apply_async(self.function, args=(self.queue,), kwds=config, callback=self._function_end)
            if prev_node_error:
                self.queue.put((prev_node.topic, 'error'))
            else:
                self.queue.put((prev_node.topic, prev_node.results[prev_out])) # TODO: make the result generator and send it, define in node-red
    

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
    def _dec_running(cls):
        with cls.num_running_lock:
            cls.num_running -= 1


    @classmethod 
    def _inc_running(cls):
        with cls.num_running_lock:
            cls.num_running += 1
            
    
    @property
    def name(self):
        return self.function.__name__
        
        
    