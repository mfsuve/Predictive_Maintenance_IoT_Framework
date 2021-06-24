from utils.node import Model, Node
from utils.io import Input, InputType

class SaveModel(Node):

    def function(self, data:Input, folder, prefix):

        if data.type != InputType.MODEL:
            raise TypeError(f"Input needs to be a model coming from a model node but got '{data.type.name.lower()}'")
        
        model:Model
        model, just_loaded = data.get()
        
        if not just_loaded:
            model.save(folder, prefix)
            self.done()
        else:
            self.clear_status()
    