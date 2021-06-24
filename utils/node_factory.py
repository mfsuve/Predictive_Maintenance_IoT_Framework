from utils.node import Node
from glob import glob
from utils.utils import myprint as print

with open('imported.txt', 'w') as file:
    # Automatic importing the node classes for NodeFactory to recognize them
    for filename in glob('C:\\Users\\mus-k\\Desktop\\Üniversite\\Tez\\Node Red\\nodes2\\nodes\\**\\*.py', recursive=True):
        filename = filename[filename.find('nodes\\'):]
        filename = filename.replace('\\', '.')[:-3]
        exec(f'import {filename}')
        file.write(f'import {filename}\n')
    
class NodeFactory:
    nodes = None
    @classmethod
    def __init(cls, topcls):
        for C in topcls.__subclasses__():
            if len(C.__subclasses__()) == 0:
                cls.nodes[C.__name__] = C
            else:
                cls.__init(C)

    @classmethod
    def create(cls, name, *args) -> Node:
        if cls.nodes is None:
            cls.nodes = {}
            # Add all classes with no subclasses (e.g. all node classes corresponding to NodeRed nodes) into nodes dictionary
            cls.__init(Node)
        return cls.nodes[name](*args)
