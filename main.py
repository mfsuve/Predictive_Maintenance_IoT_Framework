import os
import json
from time import sleep
from pprint import pformat
from traceback import format_exc
# from multiprocessing import Pool # TODO: Use processes instead of threads

from utils.utils import myprint as print, threaded
from utils.net.utils import device
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
        nodes[nodeid].run(config, nodes[prev_nodeid], prev_out)
    

if __name__ == '__main__':
    log = init_logger('nodered')
    print(f'Started python process, PID: {os.getpid()}', f'Using device {device}')
    
    while True:
        try:
            config = json.loads(input())
        except json.decoder.JSONDecodeError:
            print('Encountered a JSONDecodeError, Exitting...')
            break
        except BaseException:
            print('Encountered something, Exitting...', format_exc())
            raise
        call_node(config)
            
    print(f'End of the python process, PID: {os.getpid()}')
