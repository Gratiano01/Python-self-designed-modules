import _abcoll
import c_py_types, ctypes

CellType = type(c_py_types.__(0).func_closure[0])

@staticmethod
def new_generator(name, it=()):
    namespace = {}
    exec '''\
def {name}(it):
    for i in it:yield i'''.format(name=name) in namespace
    return namespace[name](it)

@staticmethod
def new_dict_proxy(d=None):
    if d == None:d = {}
    if not isinstance(d, dict):d = dict(d)
    return c_py_types.get_object(c_py_types.make(c_py_types.DictProxyObject,
                    members=(1, id(type(int.__dict__)),
                             c_py_types.get_struct(d, c_py_types.DictObject))))

@staticmethod
def new_traceback(coding):
    class _W:
        def __init__(self):self.tb = None
        def __enter__(self):return self
        def __exit__(self, etype, v, tb):
            self.tb = tb
            return True
        def run(self, coding):exec coding
    w = _W()
    with w as a:
        a.run(coding)
    return w.tb

@staticmethod
def new_dict_keys(sth):
    if isinstance(sth, _abcoll.Mapping):
        return dict(sth).viewkeys()
    return dict.fromkeys(list(sth)).viewkeys()

@staticmethod
def new_dict_values(sth):
    if isinstance(sth, _abcoll.Mapping):
        return dict(sth).viewvalues()
    return dict(zip(range(len(sth)), sth)).viewvalues()

@staticmethod
def new_dict_items(sth):
    return dict(sth).viewitems()

@staticmethod
def new_cell(obj):
    p = ctypes.pointer(c_py_types.PyCellObject(1, id(
        type(c_py_types.__(0).func_closure[0])), c_py_types.get_struct(obj)))
    p.contents.ob_refcnt += 1
    return c_py_types.get_object(p)

@staticmethod
def new_NoneType():
    return None
