from datetime import datetime
import os
from utils.utils import make_sure_folder_exists
from glob import glob


def get_path_to_model(folder, model_name):
    return make_sure_folder_exists(os.path.join(folder, model_name, datetime.now().strftime("%d-%m-%Y_%H-%M-%S")))


def add_prefix(prefix, name, path=None):
    if not isinstance(prefix, str):
        raise TypeError('prefix needs to be a string')
    if prefix.strip() == '':
        prefix = prefix.strip().replace(' ', '_')
        if prefix.endswith('_'):
            name = f'{prefix}{name}'
        else:
            name = f'{prefix}_{name}'
    if path is None:
        return name
    else:
        return os.path.join(path, name)


def get_file_to_load(path, file_name='model.pkl'):
    try:
        return glob(f'{path}/*{file_name}')[0]
    except IndexError:
        raise FileNotFoundError(f"Can't find the model file in {path}.")
        