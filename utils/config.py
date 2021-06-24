import json

from numpy.core import machar
from numpy.lib.function_base import select

from utils.singleton import SingletonMeta
from utils.utils import myprint as print


class ConfigError(ValueError):
    pass


class Config(metaclass=SingletonMeta):
    # Since all nodes are initialized at the beginning, I can't cache config at init method
    # Because LoadDataset node wouldn't have initialized it
    """
    ### Numeric Column Attributes
    
    - min : `int`
    
    &emsp;&emsp;Minimum possible value of that column
    
    - max : `int`
    
    &emsp;&emsp;Maximum possible value of that column
    
    ### Categoric Column Attributes
    
    - categories : `list<str>`
    
    &emsp;&emsp;All possible categories of that column

    """
    

    def __init__(self, configPath=None):
        if configPath is None or configPath.strip() == '':
            raise ValueError('At least one of the Dataset Loading nodes should set the data configuration file path')
        try:
            with open(configPath.strip(), 'r', encoding='utf-8') as file:
                self.__config = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Can't find {configPath} file for data configuration")
        
        # Reading the categoric and numeric columns
        self.categoric_columns = []
        self.numeric_columns = []
        for column, params in self.__config['columns'].items():
            if 'type' in params:
                if params['type'] == 'categoric':
                    if 'categories' in params:
                        self.categoric_columns.append(column)
                    else:
                        raise ConfigError("Categoric columns should define its categories in the data configuration file")
                elif params['type'] == 'numeric':
                    if 'min' in params and 'max' in params:
                        if params['min'] > params['min']:
                            raise ConfigError(f"'min' value should not be greater than 'max' value for {column}")
                        self.numeric_columns.append(column)
                    else:
                        raise ConfigError("Numeric columns should define its min and max values in the data configuration file")
                else:
                    raise ConfigError(f"Type of a column can be either 'numeric' or 'categoric'")
            else:
                raise ConfigError(f"Every column must define its type in the data configuration file")
        
        if not isinstance(self.__config['classes'], list):
            raise ConfigError("'classes' should be defined as list in the data configuration file")
        
        if 'names' in self.__config:
            if not isinstance(self.__config['names'], list):
                raise ConfigError("'names' should be defined as list in the data configuration file")
        else:
            self.__config['names'] = list(map(str, self.__config['classes']))
            
        self.num_classes = len(self.__config['classes'])
        if self.num_classes != len(self.__config['names']):
            raise ConfigError("Number of names and classes should be the same in the data configuration file.")
        
        self.class_name_dict = dict(zip(self.classes(), self.names()))
        self.__is_target_numeric = all(not isinstance(c, str) for c in self.classes())
        
            
    def transform_label(self, transform):
        # This is called if the fit function of any encoder is called (OneHotEncoder or SimpleEncoder)
        self.class_name_dict = dict(zip(transform(self.classes()), self.names()))
            
    def __getitem__(self, key):
        return self.__config[key]
    
    def columns(self):
        return list(self['columns'].keys())
    
    def is_categoric(self, column):
        '''Same from the config file (unchanged)'''
        try:
            return self['columns'][column]['type'] == 'categoric'
        except KeyError:
            return False
        
    def is_numeric(self, column):
        '''Same from the config file (unchanged)'''
        return not self.is_categoric(column)
    
    def is_all_numeric(self):
        return len(self.categoric_columns) == 0
    
    def is_all_categoric(self):
        return len(self.numeric_columns) == 0
    
    def is_target_numeric(self):
        '''Returns if target has only non-string values'''
        return self.__is_target_numeric
    
    def is_target_categoric(self):
        '''Returns if target has any string values'''
        return not self.is_target_numeric()
    
    def min(self, column):
        '''Gives the minimum of the column
        (Assumes encoded for the categorical columns)'''
        if column in self.categoric_columns:
            # If column is categorical, then it must be SimpleEncoded
            return 0
        elif column in self.numeric_columns:
            # If column is numeric take the min of it
            return self['columns'][column]['min']
        else:
            # If the column is not found, then it is categorical (Because I make sure all columns are there when loading)
            # OneHotEncoded min is 0
            return 0
        
    def max(self, column):
        '''Gives the maximum of the column
        (Assumes encoded for the categorical columns)'''
        if column in self.categoric_columns:
            # If column is categorical, then it must be SimpleEncoded
            return len(self.categories(column)) - 1
        elif column in self.numeric_columns:
            # If column is numeric take the min of it
            return self['columns'][column]['max']
        else:
            # If the column is not found, then it is categorical (Because I make sure all columns are there when loading)
            # OneHotEncoded max is 1
            return 1
        
    def min_y(self, encoded=False):
        if self.is_target_numeric():
            return min(self.classes())
        elif encoded:
            return 0 # minimum for simple encoding (I always simple encode target aka. y)
        else:
            raise ValueError(f"Categorical column can't have minimum value. If your data has categorical targets, you can pass it through an encoding node.")
        
    def max_y(self, encoded=False):
        if self.is_target_numeric():
            return max(self.classes())
        elif encoded:
            return len(self.classes()) # maximum for simple encoding (I always simple encode target aka. y)
        else:
            raise ValueError(f"Categorical column can't have maximum value. If your data has categorical targets, you can pass it through an encoding node.")
        
    def categories(self, column):
        return self['columns'][column]['categories']
        
    def classes(self):
        '''
        Returns all classes that any initial data directly read from the load_data node can have at their target columns.        
         * It is in the same order as `names()`.
         * Used in the `encoder` node.
        '''
        return self['classes']
    
    def names(self):
        '''
        Returns all possible names that any class can represent.
         * It is in the same order as `classes()`.
         * Used in the `test_model` node for the dashboard to be able to display all names.
        '''
        return self['names']
    
    def predictions(self):
        '''
        Returns all predictions that any model can make with or without encoded class labels.
         * It is in the same order as `classes()` and `names()`.
         * Used in the `test_model` node for all metrics returning multiple values (e.g. precision, recall, etc.)
        '''
        return list(self.class_name_dict.keys())
    
    def convert_to_names(self, labels):
        return [self.class_name_dict[label] for label in labels]


if __name__ == "__main__":
    config = Config('data_config.json')
    
    columns = []
    for col, attr in config['columns'].items():
        if config.is_numeric(col):
            columns.append(col)
        else:
            for cat in set(attr['categories']):
                columns.append(f'{col}_{cat}')
    
    print(columns)