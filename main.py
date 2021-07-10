from typing import Dict
from utils.node import Node
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import os
import json
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
# *              (should contain 'nodeid' to indicate which node has this output)

nodes:Dict[str, Node] = {}
wires_dict = {}


def init(config):
    global wires_dict
    all_nodeids = set(nodes.keys())
    for nodeid, node_wires in wires_dict.items():
        node = nodes[nodeid]
        for node_wires_from_out in node_wires:
            node.add_next_nodes([nodes[_nodeid] for _nodeid in (all_nodeids & set(node_wires_from_out))])
    del wires_dict
    

@after(init)
@threaded
def call_node(config:Dict):
    nodeid = str(config.pop('id')).strip()
    msg = str(config.pop('msg')).strip()
    nodes[nodeid].input(Input(msg), config)
        

# @threaded
def create_node(args):
    global wires_dict
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
            config:Dict = json.loads(input())
            if 'create' in config:
                create_node(config)
            else:
                call_node(config)
        except json.decoder.JSONDecodeError as e:
            print('Encountered a JSONDecodeError, Exitting...', format_exc())
            print(e)
            break
        except BaseException as e:
            print('Encountered something, Exitting...', format_exc())
            print(e)
            raise
            
    print(f'End of the python process, PID: {os.getpid()}')
