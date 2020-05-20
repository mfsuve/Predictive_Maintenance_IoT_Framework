import json
import sys
from pprint import pformat
from traceback import format_exc
from functools import wraps
import logging

log = logging.getLogger('nodered')


# # ! Function having this decorator should not return
# # ! a list for one output, it should be put in a tuple
# # * single output for single output nodes
# # * list of outputs for multiple output nodes
# ##########################################
# # TODO: Put the output in an Output object to store info like
# # TODO: if it is an error, you can also itearte the output
# # TODO: inside the function_end function
# def nodered_function(*inputs):
#     # stream_data = any(isinstance(C, Stream) for C in inputs)
#     inputs = {C.name.lower(): C for C in inputs} # Assuming all input classes have the same name as the topics
#     def decorator(func):
#         @wraps(func)
#         def wrapper(input_queue=None, **kwargs):
#             try:
            
#                 myprint(func.__name__, f'kwargs:', kwargs, f'inputs:', inputs)
                
#                 if input_queue is not None:
#                     for i in range(len(inputs)):
#                         myprint(func.__name__, f'waiting for input...')
#                         topic, data = input_queue.get()
#                         myprint(func.__name__, f'Got {i+1}. input:', 'topic:', topic, 'data:', data)
#                         if data == 'error':
#                             return None
                        
#                         # inputs = (Data, Model)
#                         # topic, data = model, SVM
                        
#                         kwargs.update(inputs[topic].format(data))
                
#                 returned = None
#                 try:
#                     returned = func(**kwargs)
#                 except Exception as e:                                  # In case of an exception
#                     return repr(e) + '\n' + format_exc()
#                 if returned is None:                                    # In case nothing returns
#                     return []
#                 if not isinstance(returned, list):                      # In case one out returns
#                     if isinstance(returned, tuple):
#                         returned = [returned]
#                     else:
#                         returned = [(returned,)]
#                 return returned
            
#             except Exception:
#                 myprint(format_exc())
#                 return []
            
#         return wrapper
#     return decorator


def myprint(*args, end='', sep='\n'):
    final_string = '\n'
    for s in args:
        if isinstance(s, str):
            final_string += s + sep
        else:
            final_string += pformat(s) + sep
    final_string += end
    log.warning(final_string)
   
 
def make_list_of_tuples(val):
    if not isinstance(val, list):
        if isinstance(val, tuple):
            return [val]
        else:
            return [(val,)]
