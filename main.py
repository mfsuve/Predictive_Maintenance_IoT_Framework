import os
import json
from time import sleep
from pprint import pformat
from traceback import format_exc
# from multiprocessing import Pool # TODO: Use processes instead of threads

from utils.utils import myprint as print, threaded
from utils.logger import init_logger
from utils.node_factory import NodeFactory

# * Logging:
# * * warning -> only pythonlog.log
# * * info    -> output for node in node-red
# *              (should be 'nodeid' to indicate which node has this output)

nodes = {}

@threaded
def call_node(config):
    node = str(config.pop('pynode')).strip()
    nodeid = str(config.pop('id')).strip()
    # Which output port does this message come from previous node
    prev_out = int(config.pop('prevout'))
    prev_nodeid = str(config.pop('prev_nodeid')).strip()
    prev_node_error = bool(config.pop('error'))

    if nodeid not in nodes:
        nodes[nodeid] = NodeFactory.create(node, nodeid)
        print(f'Created node {node} with id {nodeid}')

    if prev_out == -1: # This is the first node starting the flow (no prev_node, prev_out, prev_error)
        nodes[nodeid].run(config)
    else:
        nodes[nodeid].run(config, nodes[prev_nodeid], prev_out, prev_node_error)
    

if __name__ == '__main__':
    log = init_logger('nodered')
    print("Started python process")
    
    while True:
        try:
            config = json.loads(input())
        except json.decoder.JSONDecodeError:
            print('Encountered an JSONDecodeError, Exitting...')
            break
        except BaseException:
            print('Encountered something, Exitting...', format_exc())
            raise
        call_node(config)
            
    print(f'End of the python process, PID: {os.getpid()}')
