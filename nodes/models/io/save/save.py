import pandas as pd
import sys
import json
import numpy as np

from utils.utils import myprint as print
from utils.node import Node
from utils.io import InputType

class SaveModel(Node):

    def function(self, data, folder, prefix, timestamp):

        if data.type != InputType.MODEL:
            raise TypeError(f"Input needs to be a model coming from a model node but got '{data.type.name.lower()}'")
        
        model, just_loaded = data.output
        
        if not just_loaded:
            model.save(folder, prefix, timestamp)
            self.done()
        else:
            self.clear_status()
    