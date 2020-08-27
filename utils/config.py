import json
from utils.singleton import SingletonMeta
from utils.utils import myprint as print


class ConfigError(ValueError):
    pass


class Config(metaclass=SingletonMeta):
    """
    ### Numeric Sensor Attributes
    
    - min : `int`
    
    &emsp;&emsp;Minimum possible value of that sensor
    
    - max : `int`
    
    &emsp;&emsp;Maximum possible value of that sensor
    
    ### Categoric Sensor Attributes
    
    - categories : `list<str>`
    
    &emsp;&emsp;All possible categories of that sensor

    """
    

    def __init__(self, configPath=None):
        with open(configPath, 'r', encoding='utf-8') as file:
            self.__config = json.load(file)
        
        # Reading the categoric and numeric columns
        self.categoric_columns = []
        self.numeric_columns = []
        for sensor, params in self.__config['sensors'].items():
            if params['type'] == 'categoric':
                if 'categories' in params:
                    self.categoric_columns.append(sensor)
                else:
                    raise ConfigError("Categoric sensors should define its categories in the config file")
            else:
                if 'min' in params and 'max' in params:
                    self.numeric_columns.append(sensor)
                else:
                    raise ConfigError("Numeric sensors should define its min and max values in the config file")
        
        if not (isinstance(self.__config['classes'], list) and isinstance(self.__config['names'], list)):
            raise ConfigError("'classes' and 'names' should be defined as lists in the config file")
        self.num_classes = len(self.__config['classes'])
        if self.num_classes != len(self.__config['names']):
            raise ConfigError("Number of names and classes should be the same in the config file.")
        
        self.inverse = None
            
            
    def __getitem__(self, key):
        return self.__config[key]
    
    def columns(self):
        return self['sensors'].keys()
    
    def is_categoric(self, sensor):
        try:
            return self['sensors'][sensor]['type'] == 'categoric'
        except KeyError:
            return False
    
    def min(self, sensor):
        try:
            return self['sensors'][sensor]['min']
        except KeyError:
            return 0 # If the sensor is not found, then it is categorical (Because I make sure all sensors are there when loading)
        
    def max(self, sensor):
        try:
            return self['sensors'][sensor]['max']
        except KeyError:
            return 1 # If the sensor is not found, then it is categorical (Because I make sure all sensors are there when loading)
    
    def categories(self, sensor):
        return self['sensors'][sensor]['categories']
        
    def classes(self):
        return self.__config['classes']
    
    def all_names(self):
        return self.__config['names']
    
    def names(self, labels):
        print('Config | labels:', labels)
        classes = self.classes()
        print('Config | Before inverse', 'classes:', classes, 'Type:', [type(c) for c in classes])
        print('Config | self.inverse:', self.inverse)
        if self.inverse is not None:
            classes = self.inverse(classes)
        print('Config | After inverse', 'classes:', classes, 'Type:', [type(c) for c in classes])
        names = dict(zip(classes, self.all_names()))
        print('Config | names:', names)
        return [names[label] for label in labels]


if __name__ == "__main__":
    config = Config('data_config.json')
    
    columns = []
    for col, attr in config['sensors'].items():
        if config.is_numeric(col):
            columns.append(col)
        else:
            for cat in set(attr['categories']):
                columns.append(f'{col}_{cat}')
    
    print(columns)