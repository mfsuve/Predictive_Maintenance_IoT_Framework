import os
import json
from time import sleep
from pprint import pformat
from traceback import format_exc
# from multiprocessing import Pool # TODO: Use processes instead of threads
from multiprocessing.pool import ThreadPool as Pool
from threading import Thread, Timer

from utils.utils import myprint as print
from utils.logger import init_logger
from utils.node_factory import NodeFactory

# * Logging:
# * * warning -> only pythonlog.log
# * * info    -> output for node in node-red
# *              (should be 'nodeid' to indicate which node has this output)

nodes = {}

def call_node(pool, config):
    global log
    
    node = str(config['pynode']).strip()
    nodeid = str(config['id']).strip()
    # Which output port does this message come from previous node
    prev_out = int(config['prevout'])
    prev_nodeid = str(config['prev_nodeid']).strip()
    prev_node_error = bool(config['error'])
    del config['id']
    del config['error']
    del config['pynode']
    del config['prevout']
    del config['prev_nodeid']

    if nodeid not in nodes:
        nodes[nodeid] = NodeFactory.create(node, pool, nodeid)
        print(f'Created node {node} with id {nodeid}')

    if prev_out == -1: # This is the first node starting the flow (no prev_node, prev_out, prev_error)
        nodes[nodeid].run(config)
    else:
        nodes[nodeid].run(config, nodes[prev_nodeid], prev_out, prev_node_error)
    

# def print_num_running_nodes(sec=10):
#     print(f'Number of running nodes: {Node.num_running} | PID: {os.getpid()}')
#     timer = Timer(sec, print_num_running_nodes, args=(sec,))
#     timer.setDaemon(True)
#     timer.start()


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
