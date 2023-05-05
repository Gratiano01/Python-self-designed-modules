from new import *
from new import __doc__
from new2.meta import NewTypeMeta as _meta
import new2.new_functions
import sys
new_functions = sys.modules['new2.new_functions']
del sys, new2
import types
__all__ = ['classobj', 'function', 'instance', 'instancemethod', 'module',
           'code', 'generator', 'dictproxy', 'traceback', 'dict_keys',
           'dict_values', 'dict_items', 'cell', 'NoneType']
class generator:
    '''
generator(name, iterator=()) -> generator object.\
'''
    __metaclass__ = _meta
    _raw_type = types.GeneratorType
    _func_new = new_functions.new_generator

class dictproxy:
    '''
dictproxy(d={}) -> dictproxy object.\
'''
    __metaclass__ = _meta
    _raw_type = types.DictProxyType
    _func_new = new_functions.new_dict_proxy

class traceback:
    '''
traceback(code) -> traceback object.\
'''
    __metaclass__ = _meta
    _raw_type = types.TracebackType
    _func_new = new_functions.new_traceback

class dict_keys:
    '''
dict_keys(keys) -> dict keys view.
dict_keys(dict) -> dict keys view.
'''
    __metaclass__ = _meta
    _raw_type = type({}.viewkeys())
    _func_new = new_functions.new_dict_keys

class dict_values:
    '''
dict_values(values) -> dict values view.
dict_values(dict) -> dict values view.
'''
    __metaclass__ = _meta
    _raw_type = type({}.viewvalues())
    _func_new = new_functions.new_dict_values

class dict_items:
    '''
dict_items(items) -> dict items view.
dict_items(dict) -> dict items view.
'''
    __metaclass__ = _meta
    _raw_type = type({}.viewitems())
    _func_new = new_functions.new_dict_items

class cell:
    '''
cell(object) -> the object's cell, or you can call it reference
'''
    __metaclass__ = _meta
    _raw_type = new_functions.CellType
    _func_new = new_functions.new_cell

class NoneType:
    '''
NoneType() -> None
'''
    __metaclass__ = _meta
    _raw_type = types.NoneType
    _func_new = new_functions.new_NoneType
