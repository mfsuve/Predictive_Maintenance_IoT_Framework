from utils.node import Node
from glob import glob

# Automatic importing the node classes for NodeFactory to recognize them
for filename in glob('C:\\Users\\mus-k\\Desktop\\Üniversite\\Tez\\Node Red\\nodes2\\nodes\\**\\*.py', recursive=True):
    filename = filename[filename.find('nodes\\'):]
    filename = filename.replace('\\', '.')[:-3]
    exec(f'import {filename}')
    
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
    def create(cls, name, *args):
        if cls.nodes is None:
            cls.nodes = {}
            cls.__init(Node)
        return cls.nodes[name](*args)
