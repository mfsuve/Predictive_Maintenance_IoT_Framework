from utils.node import Node
from utils.io import InputType

class SaveModel(Node):

    def function(self, data, folder, prefix):

        if data.type != InputType.MODEL:
            raise TypeError(f"Input needs to be a model coming from a model node but got '{data.type.name.lower()}'")
        
        model, just_loaded = data.get()
        
        if not just_loaded:
            model.save(folder, prefix)
            self.done()
        else:
            self.clear_status()
    