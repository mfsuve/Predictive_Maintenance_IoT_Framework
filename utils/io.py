import enum


# * Defined to be able to differentiate multiple inputs
class InputType(str, enum.Enum):
    MODEL = 'MODEL'
    DATA = 'DATA'
    NODERED = 'NODERED'
    # * Can add more Type's later


class Input:
    def __init__(self, _data, _type=InputType.NODERED):
        self.__data = _data
        self.type = _type
        
    def __repr__(self):
        return f'type: {self.type}\n{self.__data}'
    
    def get(self):
        return self.__data
        