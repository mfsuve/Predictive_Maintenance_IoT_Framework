import os
import json
from time import sleep
from pprint import pformat
from traceback import format_exc
# from multiprocessing import Pool # TODO: Use processes instead of threads

from utils.utils import myprint as print, threaded, after
from utils.net.utils import device
from utils.logger import init_logger
from utils.node_factory import NodeFactory
from utils.io import Input

# * Logging:
# * * warning -> only pythonlog.log
# * * info    -> output for node in node-red
# *              (should be 'nodeid' to indicate which node has this output)

nodes = {}
wires_dict = {}


def init(config):
    global wires_dict
    all_nodeids = set(nodes.keys())
    for nodeid, node_wires in wires_dict.items():
        node = nodes[nodeid]
        for node_wires_from_out in node_wires:
            node.add_next_nodes([nodes[nodeid] for nodeid in (all_nodeids & set(node_wires_from_out))])
    del wires_dict
    

@after(init)
@threaded
def call_node(config):
    nodeid = str(config.pop('id')).strip()
    msg = str(config.pop('msg')).strip()
    nodes[nodeid].input(Input(msg), config)
        

# @threaded
def create_node(args):
    nodeid = args['id']
    wires = args['wires']
    node = args['pynode']
    config = args['config']
    wires_dict[nodeid] = wires
    nodes[nodeid] = NodeFactory.create(node, nodeid, config)
    print(f'Created node {node} with id {nodeid}')


if __name__ == '__main__':
    log = init_logger('nodered')
    print(f'Started python process, PID: {os.getpid()}', f'Using device {device}')
    
    while True:
        try:
            config = json.loads(input())
            if 'create' in config:
                create_node(config)
            else:
                call_node(config)
        except json.decoder.JSONDecodeError:
            print('Encountered a JSONDecodeError, Exitting...')
            break
        except BaseException:
            print('Encountered something, Exitting...', format_exc())
            raise
            
    print(f'End of the python process, PID: {os.getpid()}')
