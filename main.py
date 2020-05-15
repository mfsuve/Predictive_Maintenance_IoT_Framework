import os
import json
from time import sleep
from pprint import pformat
from traceback import format_exc
# from multiprocessing import Pool # TODO: Use processes instead of threads
from multiprocessing.pool import ThreadPool as Pool
from threading import Thread, Timer

from utils.utils import nodered_function
from utils.utils import myprint as print
from utils.logger import init_logger
from utils.node import Node

from nodes.dataset.load_dataset import load_dataset
from nodes.preprocess.scaler.scaler import minmax_scaler, standard_scaler
from nodes.model_selection.train_test_split.train_test_split import split
from nodes.models.classification.svm.svm import svm
from nodes.result.test_model import test

# * Logging:
# * * warning -> only pythonlog.log
# * * info    -> output for node in node-red
# *              (should be 'nodeid' to indicate which node has this output)

nodes = {}

def call_node(pool, config):
    global log
    
    function_name = str(config['pyfunc']).strip()
    prev_node_error = bool(config['error'])
    # Which output port does this message come from previous node
    prev_out = int(config['prevout'])
    prev_nodeid = str(config['prev_nodeid']).strip()
    nodeid = str(config['id']).strip()
    topic = str(config['topic']).strip().lower()
    end = bool(config['end'])
    del config['id']
    del config['end']
    del config['error']
    del config['topic']
    del config['pyfunc']
    del config['prevout']
    del config['prev_nodeid']

    # * What if process takes too long (like a year)
    # They can change nodes, delete, add. All deleted nodes will be remembered here
    # Solution: In nodered, after node ends, send a message to here to remove the node from the memory of python process
    if nodeid not in nodes:
        nodes[nodeid] = Node(pool, nodeid, topic, globals()[function_name], end)
        print(f'Created node {nodeid}')

    if prev_out == -1: # This is the first node starting the flow (no prev_node, prev_out, prev_error)
        nodes[nodeid].run(config)
    else:
        nodes[nodeid].run(config, nodes[prev_nodeid], prev_out, prev_node_error)
    

def print_num_running_nodes(sec=10):
    print(f'Number of running nodes: {Node.num_running} | PID: {os.getpid()}')
    timer = Timer(sec, print_num_running_nodes, args=(sec,))
    timer.setDaemon(True)
    timer.start()


if __name__ == '__main__':
    global log
    log = init_logger('nodered')
    print("Started python process")
    
    # print_num_running_nodes(20)
    
    with Pool() as pool:
        while True:
            try:
                config = json.loads(input())
            except json.decoder.JSONDecodeError:
                print('Encountered an JSONDecodeError, Exitting...')
                break
            except BaseException:
                print('Encountered something, Exitting...', format_exc())
                raise
            call_node_thread = Thread(target=call_node, args=(pool, config))
            call_node_thread.setDaemon(True)
            call_node_thread.start()
            
    print(f'End of the python process, PID: {os.getpid()}')
