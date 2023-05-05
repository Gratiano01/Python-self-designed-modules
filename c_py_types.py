'''Do all the python types in module \'ctypes\''''
import ctypes, sys, collections, _ctypes, types
from files import _CFILE

PyObject_HEAD = [('ob_refcnt', ctypes.c_ssize_t), ('ob_type', ctypes.c_void_p)]
if sys._getframe(1).f_locals.has_key('DEBUGGING'):
    PyObject_HEAD = [('_ob_next', ctypes.c_int), ('_ob_prev', ctypes.c_int)] + \
                    PyObject_HEAD
PyObject_VAR_HEAD = PyObject_HEAD + [('ob_size', ctypes.c_ssize_t)]
dll = ctypes.pythonapi

def _str_func(self):
    if isNULL(self):return '<%s <NULL>>' % type(self).__name__[3:]
    return '<%s %r>' % (type(self).__name__[3:], get_object(self))

def _del_func(self):
    if not isNULL(self):self.contents.ob_refcnt -= 1

def _POINTER(t):
    pt = ctypes.POINTER(t)
    pt.__repr__ = pt.__str__ = _str_func
    pt.__del__ = _del_func
    return pt

class PyObject(ctypes.Structure):
    '''
typedef struct _object {
    PyObject_HEAD
} PyObject;
'''
    _fields_ = PyObject_HEAD

Object = _POINTER(PyObject)

def isNULL(p):
    return ctypes.cast(p, ctypes.c_void_p).value == None
    
def get_object(struct):
    if isNULL(struct):return None
    return _ctypes.PyObj_FromPtr(ctypes.cast(struct, ctypes.c_void_p).value)

def get_struct(obj, struct_t=Object):
    p = ctypes.cast(id(obj), struct_t)
    p.contents.ob_refcnt += 1
    return p

def make(struct, members=None, args=None):
    if args:
        return struct._type_._new_func(*args)
    alloc = allocobject(ctypes.sizeof(struct._type_))
    s = get_struct(alloc, struct)
    s.contents = struct._type_(*members)
    return s

def allocobject(size, t=object):
    k = (size - ctypes.sizeof(PyObject)) / ctypes.sizeof(Object)
    class A(object):
        __slots__ = tuple(map('x%d'.__mod__, range(k)))
    x = A()
    get_struct(x).contents.ob_type = id(t)
    get_struct(x).contents.ob_refcnt += 1
    return x

def getmember(struct, *args):
    o = struct.contents
    for i in args:
        o = getattr(o, i)
    return o

def _setmember(struct, *args):
    args = list(args)
    value = args.pop()
    if len(args) == 1:
        setattr(struct, args[0], value)
    x = args[0]
    b = getattr(struct, x)
    if isinstance(b, ctypes._Pointer):
        con = b.contents
        _setmember(con, args[1:], value)
        b.contents = con
    else:_setmember(b, args[1:], value)
    setattr(struct, x, b)

def setmember(struct, *args):
    if len(args) == 1:
        struct.contents = args[0]
    else:
        b = struct.contents
        _setmember(b, *args)
        struct.contents = b

_type_cache_ = {}
_struct_cache_ = {}

def _declare(struct_t, type_t):
    _type_cache_[struct_t] = type_t
    _struct_cache_[type_t] = struct_t

def cast(t, type=0):
    if type:
        return _struct_cache_.get(t, Object)
    return _type_cache_.get(t, object)
    
_declare(Object, object)

class PyVarObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_VAR_HEAD
} PyVarObject;
'''
    _fields_ = PyObject_VAR_HEAD

VarObject = _POINTER(PyVarObject)

_type_object_defs = {'destructor':ctypes.PYFUNCTYPE(ctypes.c_short, Object),
                    'freefunc':ctypes.PYFUNCTYPE(ctypes.c_short,
                                                 ctypes.c_void_p),
                    'printfunc':ctypes.PYFUNCTYPE(ctypes.c_int, Object, _CFILE,
                                                  ctypes.c_int),
                    'getattrfunc':ctypes.PYFUNCTYPE(Object, Object,
                                                    ctypes.c_char_p),
                    'getattrofunc':ctypes.PYFUNCTYPE(Object, Object, Object),
                    'setattrfunc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                    ctypes.c_char_p, Object),
                    'setattrofunc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                     Object, Object),
                    'cmpfunc':ctypes.PYFUNCTYPE(ctypes.c_int, Object, Object),
                    'reprfunc':ctypes.PYFUNCTYPE(Object, Object), 
                    'hashfunc':ctypes.PYFUNCTYPE(ctypes.c_long, Object), 
                    'richcmpfunc':ctypes.PYFUNCTYPE(Object, Object, Object,
                                                    ctypes.c_int),  
                    'getiterfunc':ctypes.PYFUNCTYPE(Object, Object), 
                    'iternextfunc':ctypes.PYFUNCTYPE(Object, Object), 
                    'descrgetfunc':ctypes.PYFUNCTYPE(Object, Object, Object,
                                                     Object), 
                    'descrsetfunc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                     Object, Object), 
                    'initproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                     Object, Object), 
                    'newfunc':ctypes.PYFUNCTYPE(Object, ctypes.c_int, Object,
                                                Object),
                    'allocfunc':ctypes.PYFUNCTYPE(Object, ctypes.c_int,
                                                  ctypes.c_ssize_t)
                    }

PyCFunction = ctypes.PYFUNCTYPE(Object, Object, Object)
PyCFunctionWithKeywords = ctypes.PYFUNCTYPE(Object, Object, Object, Object)
PyNoArgsFunction = ctypes.PYFUNCTYPE(Object)
getter = ctypes.PYFUNCTYPE(Object, Object, ctypes.c_void_p)
setter = ctypes.PYFUNCTYPE(ctypes.c_int, Object, Object, ctypes.c_void_p)
wrapperfunc = ctypes.PYFUNCTYPE(Object, Object, Object, ctypes.c_void_p)
wrapperfunc_kwds = ctypes.PYFUNCTYPE(Object, Object, Object, ctypes.c_void_p,
                                    Object)

class Py_buffer(ctypes.Structure):
    _fields_ = [('buf', ctypes.c_void_p), ('obj', Object), ('len',
                                                            ctypes.c_ssize_t),
                ('itemsize', ctypes.c_ssize_t), ('readonly',ctypes.c_int),
                ('ndim', ctypes.c_int), ('format', ctypes.c_char_p),
                ('shape', ctypes.POINTER(ctypes.c_ssize_t)),
                ('strides', ctypes.POINTER(ctypes.c_ssize_t)),
                ('suboffsets', ctypes.POINTER(ctypes.c_ssize_t)),
                 ('smalltable', ctypes.c_ssize_t * 2),
                ('internal', ctypes.c_void_p)
                ]
bufferinfo = Py_buffer
Buffer = ctypes.POINTER(Py_buffer)

_method_defs = {'unaryfunc':ctypes.PYFUNCTYPE(Object, Object),
                'binaryfunc':ctypes.PYFUNCTYPE(Object, Object, Object),
                'ternaryfunc':ctypes.PYFUNCTYPE(Object, Object, Object, Object),
                'inquiry':ctypes.PYFUNCTYPE(ctypes.c_int, Object),
                'lenfunc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object),
                'coercion':ctypes.PYFUNCTYPE(ctypes.c_int, ctypes.POINTER(Object
                                                                         ),
                                            ctypes.POINTER(Object)),
                'intargfunc':ctypes.PYFUNCTYPE(Object, Object, ctypes.c_int),
                'intintargfunc':ctypes.PYFUNCTYPE(Object, Object, ctypes.c_int),
                'ssizeargfunc':ctypes.PYFUNCTYPE(Object, Object,
                                                ctypes.c_ssize_t),
                'ssizessizeargfunc':ctypes.PYFUNCTYPE(Object, Object,
                                                     ctypes.c_ssize_t,
                                                     ctypes.c_ssize_t), 
                'intobjargproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                 ctypes.c_int, Object),
                'intintobjargproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                    ctypes.c_int, ctypes.c_int,
                                                    Object),
                'ssizeobjargproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                   ctypes.c_ssize_t, Object),
                'ssizessizeobjargproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                     ctypes.c_ssize_t,
                                                     ctypes.c_ssize_t, Object),
                'objobjargproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object, Object,
                                                 Object), 
                'getreadbufferproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                     ctypes.c_int,
                                                     ctypes.POINTER(
                                                         ctypes.c_void_p)),
                'getwritebufferproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                      ctypes.c_int,
                                                      ctypes.POINTER(
                                                          ctypes.c_void_p)),
                'getsegcountproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                   ctypes.POINTER(
                                                       ctypes.c_int)),
                'getcharbufferproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                     ctypes.c_int,
                                                     ctypes.POINTER(
                                                         ctypes.c_char_p)),
                'readbufferproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                     ctypes.c_ssize_t,
                                                     ctypes.POINTER(
                                                         ctypes.c_void_p)),
                'writebufferproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                      ctypes.c_ssize_t,
                                                      ctypes.POINTER(
                                                          ctypes.c_void_p)),
                'segcountproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                   ctypes.POINTER(
                                                       ctypes.c_ssize_t)),
                'getcharbufferproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                     ctypes.c_ssize_t,
                                                     ctypes.POINTER(
                                                         ctypes.c_char_p)),
                'readbufferproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                  ctypes.c_ssize_t,
                                                  ctypes.POINTER(ctypes.c_void_p
                                                                 )),
                'writebufferproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                   ctypes.c_ssize_t,
                                                   ctypes.POINTER(
                                                       ctypes.c_void_p)),
                'segcountproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                ctypes.POINTER(ctypes.c_ssize_t)
                                                ),
                'charbufferproc':ctypes.PYFUNCTYPE(ctypes.c_ssize_t, Object,
                                                  ctypes.c_ssize_t,
                                                  ctypes.POINTER(ctypes.c_char_p
                                                                 )),
                'getbufferproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object, Buffer,
                                                 ctypes.c_int),
                'releasebufferproc':ctypes.PYFUNCTYPE(None, Object, Buffer),
                'objobjproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object, Object),
                'visitproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                             ctypes.c_void_p),
                'traverseproc':ctypes.PYFUNCTYPE(ctypes.c_int, Object,
                                                ctypes.c_void_p, ctypes.c_void_p
                                                )
                }
_type_object_defs.update(_method_defs)
_method_defs = _type_object_defs

PyBUF_SIMPLE = 0
PyBUF_WRITABLE = 0x0001
PyBUF_WRITEABLE = PyBUF_WRITABLE
PyBUF_FORMAT = 0x0004
PyBUF_ND = 0x0008
PyBUF_STRIDES = (0x0010 | PyBUF_ND)
PyBUF_C_CONTIGUOUS = (0x0020 | PyBUF_STRIDES)
PyBUF_F_CONTIGUOUS = (0x0040 | PyBUF_STRIDES)
PyBUF_ANY_CONTIGUOUS = (0x0080 | PyBUF_STRIDES)
PyBUF_INDIRECT = (0x0100 | PyBUF_STRIDES)
PyBUF_CONTIG = (PyBUF_ND | PyBUF_WRITABLE)
PyBUF_CONTIG_RO = (PyBUF_ND)
PyBUF_STRIDED = (PyBUF_STRIDES | PyBUF_WRITABLE)
PyBUF_STRIDED_RO = (PyBUF_STRIDES)
PyBUF_RECORDS = (PyBUF_STRIDES | PyBUF_WRITABLE | PyBUF_FORMAT)
PyBUF_RECORDS_RO = (PyBUF_STRIDES | PyBUF_FORMAT)
PyBUF_FULL = (PyBUF_INDIRECT | PyBUF_WRITABLE | PyBUF_FORMAT)
PyBUF_FULL_RO = (PyBUF_INDIRECT | PyBUF_FORMAT)
PyBUF_READ = 0x100
PyBUF_WRITE = 0x200
PyBUF_SHADOW = 0x400

class PyNumberMethods(ctypes.Structure):
    '''
typedef struct {
    binaryfunc nb_add;
    binaryfunc nb_subtract;
    binaryfunc nb_multiply;
    binaryfunc nb_divide;
    binaryfunc nb_remainder;
    binaryfunc nb_divmod;
    ternaryfunc nb_power;
    unaryfunc nb_negative;
    unaryfunc nb_positive;
    unaryfunc nb_absolute;
    inquiry nb_nonzero;
    unaryfunc nb_invert;
    binaryfunc nb_lshift;
    binaryfunc nb_rshift;
    binaryfunc nb_and;
    binaryfunc nb_xor;
    binaryfunc nb_or;
    coercion nb_coerce;
    unaryfunc nb_int;
    unaryfunc nb_long;
    unaryfunc nb_float;
    unaryfunc nb_oct;
    unaryfunc nb_hex;
    binaryfunc nb_inplace_add;
    binaryfunc nb_inplace_subtract;
    binaryfunc nb_inplace_multiply;
    binaryfunc nb_inplace_divide;
    binaryfunc nb_inplace_remainder;
    ternaryfunc nb_inplace_power;
    binaryfunc nb_inplace_lshift;
    binaryfunc nb_inplace_rshift;
    binaryfunc nb_inplace_and;
    binaryfunc nb_inplace_xor;
    binaryfunc nb_inplace_or;
    binaryfunc nb_floor_divide;
    binaryfunc nb_true_divide;
    binaryfunc nb_inplace_floor_divide;
    binaryfunc nb_inplace_true_divide;
    unaryfunc nb_index;
} PyNumberMethods;
'''
    _fields_ = [('nb_add', _method_defs['binaryfunc']),
                ('nb_substract', _method_defs['binaryfunc']),
                ('nb_multiply', _method_defs['binaryfunc']),
                ('nb_divide', _method_defs['binaryfunc']),
                ('nb_remainder', _method_defs['binaryfunc']),
                ('nb_divmod', _method_defs['binaryfunc']),
                ('nb_power', _method_defs['ternaryfunc']),
                ('nb_negative', _method_defs['unaryfunc']),
                ('nb_positive', _method_defs['unaryfunc']), ('nb_absolute', _method_defs['unaryfunc']), ('nb_nonzero', _method_defs['inquiry']), ('nb_invert', _method_defs['unaryfunc']), ('nb_lshift', _method_defs['binaryfunc']), ('nb_rshift', _method_defs['binaryfunc']), ('nb_and', _method_defs['binaryfunc']), ('nb_xor', _method_defs['binaryfunc']), ('nb_or', _method_defs['binaryfunc']), ('nb_coerce', _method_defs['coercion']), ('nb_int', _method_defs['unaryfunc']), ('nb_long', _method_defs['unaryfunc']), ('nb_float', _method_defs['unaryfunc']), ('nb_oct', _method_defs['unaryfunc']), ('nb_hex', _method_defs['unaryfunc']), ('nb_inplace_add', _method_defs['binaryfunc']), ('nb_inplace_subtract', _method_defs['binaryfunc']), ('nb_inplace_multiply', _method_defs['binaryfunc']), ('nb_inplace_divide', _method_defs['binaryfunc']), ('nb_inplace_remainder', _method_defs['binaryfunc']), ('nb_inplace_power', _method_defs['ternaryfunc']),
                ('nb_inplace_lshift', _method_defs['binaryfunc']),
                ('nb_inplace_rshift', _method_defs['binaryfunc']),
                ('nb_inplace_and', _method_defs['binaryfunc']),
                ('nb_inplace_xor', _method_defs['binaryfunc']),
                ('nb_inplace_or', _method_defs['binaryfunc']),
                ('nb_floor_divide', _method_defs['binaryfunc']),
                ('nb_true_divide', _method_defs['binaryfunc']), ('nb_inplace_floor_divide', _method_defs['binaryfunc']), ('nb_inplace_true_divide', _method_defs['binaryfunc']), ('nb_index', _method_defs['unaryfunc'])]

class PySequenceMethods(ctypes.Structure):
    '''
typedef struct {
    lenfunc sq_length;
    binaryfunc sq_concat;
    ssizeargfunc sq_repeat;
    ssizeargfunc sq_item;
    ssizessizeargfunc sq_slice;
    ssizeobjargproc sq_ass_item;
    ssizessizeobjargproc sq_ass_slice;
    objobjproc sq_contains;
    binaryfunc sq_inplace_concat;
    ssizeargfunc sq_inplace_repeat;
} PySequenceMethods;'''
    _fields_ = [('sq_length', _method_defs['lenfunc']),
                ('sq_concat', _method_defs['binaryfunc']),
                ('sq_repeat', _method_defs['ssizeargfunc']),
                ('sq_item', _method_defs['ssizeargfunc']),
                ('sq_slice', _method_defs['ssizessizeargfunc']),
                ('sq_ass_item', _method_defs['ssizeobjargproc']),
                ('sq_ass_slice', _method_defs['ssizessizeobjargproc']),
                ('sq_contains', _method_defs['objobjproc']),
                ('sq_inplace_concat', _method_defs['binaryfunc']),
                ('sq_inplace_repeat', _method_defs['ssizeargfunc'])]

class PyMappingMethods(ctypes.Structure):
    '''
typedef struct {
    lenfunc mp_length;
    binaryfunc mp_subscript;
    objobjargproc mp_ass_subscript;
} PyMappingMethods;'''
    _fields_ = [('mp_length', _method_defs['lenfunc']),
                ('mp_subscript', _method_defs['binaryfunc']),
                ('mp_ass_subscript', _method_defs['objobjargproc'])]

class PyBufferProcs(ctypes.Structure):
    '''
typedef struct {
    readbufferproc bf_getreadbuffer;
    writebufferproc bf_getwritebuffer;
    segcountproc bf_getsegcount;
    charbufferproc bf_getcharbuffer;
    getbufferproc bf_getbuffer;
    releasebufferproc bf_releasebuffer;
} PyBufferProcs;'''
    _fields_ = [('bf_getreadbuffer', _method_defs['readbufferproc']),
                ('bf_getwritebuffer', _method_defs['writebufferproc']),
                ('bf_getsegcount', _method_defs['segcountproc']),
                ('bf_getcharbuffer', _method_defs['charbufferproc']),
                ('bf_getbuffer', _method_defs['getbufferproc']),
                ('bf_releasebuffer', _method_defs['releasebufferproc'])]

NumberMethods, SequenceMethods, MappingMethods, BufferProcs = (ctypes.POINTER
    (PyNumberMethods), ctypes.POINTER(PySequenceMethods), ctypes.POINTER(
        PyMappingMethods), ctypes.POINTER(PyBufferProcs))

class PyMethodDef(ctypes.Structure):
    '''
struct PyMethodDef {
    const char *ml_name;
    PyCFunction ml_meth;
    int	ml_flags;
    const char *ml_doc;
};
typedef struct PyMethodDef PyMethodDef;
'''
    _fields_ = [('ml_name', ctypes.c_char_p), ('ml_meth', PyCFunction),
                ('ml_flags', ctypes.c_int), ('ml_doc', ctypes.c_char_p)]

_MethodDef = ctypes.POINTER(PyMethodDef)

class PyMemberDef(ctypes.Structure):
    '''
typedef struct PyMemberDef {
    char *name;
    int type;
    Py_ssize_t offset;
    int flags;
    char *doc;
} PyMemberDef;
'''
    _fields_ = [('name', ctypes.c_char_p), ('type', ctypes.c_int), ('offset',
                                                            ctypes.c_ssize_t),
                ('flags', ctypes.c_int), ('doc', ctypes.c_char_p)]

_MemberDef = ctypes.POINTER(PyMemberDef)

def offsetof(struct_t, member):
    return getattr(struct_t, member).offset

class PyGetSetDef(ctypes.Structure):
    '''
typedef struct PyGetSetDef {
    char *name;
    getter get;
    setter set;
    char *doc;
    void *closure;
} PyGetSetDef;
'''
    _fields_ = [('name', ctypes.c_char_p), ('get', getter), ('set', setter),
                ('doc', ctypes.c_char_p), ('closure', ctypes.c_void_p)]

_GetSetDef = ctypes.POINTER(PyGetSetDef)

class wrapperbase(ctypes.Structure):
    '''
struct wrapperbase {
    char *name;
    int offset;
    PyCFunction function;
    wrapperfunc wrapper;
    char *doc;
    int flags;
    PyObject *name_strobj;
};
'''
    _fields_ = [('name', ctypes.c_char_p), ('offset', ctypes.c_int),
                ('function', PyCFunction), ('wrapper', wrapperfunc),
                ('doc', ctypes.c_char_p), ('flags', ctypes.c_int),
                ('name_strobj', Object)]

_wrapperbase = ctypes.POINTER(wrapperbase)

class PyTypeObject(ctypes.Structure):
    '''
typedef struct _typeobject {
    PyObject_VAR_HEAD
    const char *tp_name;
    Py_ssize_t tp_basicsize, tp_itemsize;
    destructor tp_dealloc;
    printfunc tp_print;
    getattrfunc tp_getattr;
    setattrfunc tp_setattr;
    cmpfunc tp_compare;
    reprfunc tp_repr;
    PyNumberMethods *tp_as_number;
    PySequenceMethods *tp_as_sequence;
    PyMappingMethods *tp_as_mapping;
    hashfunc tp_hash;
    ternaryfunc tp_call;
    reprfunc tp_str;
    getattrofunc tp_getattro;
    setattrofunc tp_setattro;
    PyBufferProcs *tp_as_buffer;
    long tp_flags;
    const char *tp_doc;
    traverseproc tp_traverse;
    inquiry tp_clear;
    richcmpfunc tp_richcompare;
    Py_ssize_t tp_weaklistoffset;
    getiterfunc tp_iter;
    iternextfunc tp_iternext;
    struct PyMethodDef *tp_methods;
    struct PyMemberDef *tp_members;
    struct PyGetSetDef *tp_getset;
    struct _typeobject *tp_base;
    PyObject *tp_dict;
    descrgetfunc tp_descr_get;
    descrsetfunc tp_descr_set;
    Py_ssize_t tp_dictoffset;
    initproc tp_init;
    allocfunc tp_alloc;
    newfunc tp_new;
    freefunc tp_free;
    inquiry tp_is_gc;
    PyObject *tp_bases;
    PyObject *tp_mro;
    PyObject *tp_cache;
    PyObject *tp_subclasses;
    PyObject *tp_weaklist;
    destructor tp_del;
    unsigned int tp_version_tag;
#ifdef COUNT_ALLOCS
    Py_ssize_t tp_allocs;
    Py_ssize_t tp_frees;
    Py_ssize_t tp_maxalloc;
    struct _typeobject *tp_prev;
    struct _typeobject *tp_next;
#endif
} PyTypeObject;
'''
    _fields_ = PyObject_VAR_HEAD + [('tp_name', ctypes.c_char_p),
                                    ('tp_basicsize', ctypes.c_ssize_t),
                                    ('tp_itemsize', ctypes.c_ssize_t),
                                    ('tp_dealloc', _type_object_defs[
                                        'destructor']),
                                    ('tp_print', _type_object_defs['printfunc']
                                     ),
                                    ('tp_getattr', _type_object_defs['getattr'
                                                                    'func']),
                                    ('tp_setattr', _type_object_defs['setattr'
                                                                    'func']),
                                    ('tp_compare', _type_object_defs['cmp'
                                                                    'func']),
                                    ('tp_repr', _type_object_defs['reprfunc']),
                                    ('tp_as_number', NumberMethods),
                                    ('tp_as_sequence', SequenceMethods),
                                    ('tp_as_mapping', MappingMethods),
                                    ('tp_hash', _type_object_defs['hashfunc']),
                                    ('tp_call', _type_object_defs['ternaryfunc'])
                                    , ('tp_str', _type_object_defs['reprfunc']),
                                     ('tp_getattro', _type_object_defs[
                                         'getattrofunc']),
                                    ('tp_setattro', _type_object_defs['setattro'
                                                                      'func']),
                                    ('tp_as_buffer', BufferProcs),
                                    ('tp_flags', ctypes.c_long),
                                    ('tp_doc', ctypes.c_char_p),
                                    ('tp_traverse', _method_defs['traverseproc']
                                     ), ('tp_clear', _type_object_defs['inquiry'
                                                                       ]),
                                    ('tp_richcompare', _type_object_defs['rich'
                                                                         'cmp'
                                                                         'func']
                                     ), ('tp_weaklistoffset', ctypes.c_ssize_t),
                                    ('tp_iter', _type_object_defs['getiterfunc']
                                     ), ('tp_iternext', _type_object_defs[
                                         'iternextfunc']), ('tp_methods',
                                                            _MethodDef),
                                    ('tp_members', _MemberDef), ('tp_getset',
                                                                 _GetSetDef),
                                    ('tp_base', Object), ('tp_dict', Object),
                                    ('tp_descr_get', _type_object_defs[
                                        'descrgetfunc']),
                                    ('tp_descr_set', _type_object_defs[
                                        'descrsetfunc']), ('tp_dictoffset',
                                                           ctypes.c_ssize_t),
                                    ('tp_init', _type_object_defs['initproc']),
                                    ('tp_alloc', _type_object_defs['allocfunc'])
                                    , ('tp_new', _type_object_defs['newfunc']),
                                    ('tp_free', _type_object_defs['freefunc']),
                                    ('tp_is_gc', _type_object_defs['inquiry']),
                                    ('tp_bases', Object),
                                    ('tp_mro', Object), ('tp_cache', Object),
                                    ('tp_subclasses', Object), ('tp_weakreflist'
                                                                , Object),
                                    ('tp_del', _type_object_defs['destructor']),
                                    ('tp_version', ctypes.c_uint)
                                    ]
TypeObject = _POINTER(PyTypeObject)
_declare(TypeObject, type)

class PyHeapTypeObject(ctypes.Structure):
    '''
typedef struct _heaptypeobject {
    PyTypeObject ht_type;
    PyNumberMethods as_number;
    PyMappingMethods as_mapping;
    PySequenceMethods as_sequence; 
    PyBufferProcs as_buffer;
    PyObject *ht_name, *ht_slots;
} PyHeapTypeObject;
'''
    _fields_ = [('ht_type', PyTypeObject), ('as_number', PyNumberMethods),
                ('as_mapping',PyNumberMethods),('as_sequence',PySequenceMethods)
                , ('as_buffer', PyBufferProcs), ('ht_name', Object),
                ('ht_slots', Object)]
HeapTypeObject = _POINTER(PyHeapTypeObject)
_declare(HeapTypeObject, type)
_declare(TypeObject, type)

class PyIntObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    long ob_ival;
} PyIntObject;'''
    _fields_ = PyObject_HEAD + [('ob_ival', ctypes.c_long)]
    _new_func = dll.PyInt_FromLong
PyBoolObject = PyIntObject
BoolObject = IntObject = _POINTER(PyIntObject)
_declare(IntObject, int)

dll.PyInt_FromLong.restype = IntObject
dll.PyInt_FromLong.argtypes = (ctypes.c_long,)

digit = ctypes.c_ushort
class PyLongObject(ctypes.Structure):
    '''
typedef unsigned short digit;
struct _longobject {
	PyObject_VAR_HEAD
	digit ob_digit[1];
};
typedef struct _longobject PyLongObject;
'''
    _fields_ = PyObject_VAR_HEAD + [('ob_digit', digit * 1)]
LongObject = _POINTER(PyLongObject)
_declare(LongObject, long)

class PyFloatObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    double ob_fval;
} PyFloatObject;
'''
    _fields_ = PyObject_HEAD + [('ob_fval', ctypes.c_double)]
FloatObject = _POINTER(PyFloatObject)
_declare(FloatObject, float)

class Py_complex(ctypes.Structure):
    _fields_ = [('real', ctypes.c_double), ('imag', ctypes.c_double)]

class PyComplexObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    Py_complex cval;
} PyComplexObject;
'''
    _fields_ = PyObject_HEAD + [('cval', Py_complex)]
ComplexObject = _POINTER(PyComplexObject)
_declare(ComplexObject, complex)

class PyStringObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_VAR_HEAD
    long ob_shash;
    int ob_sstate;
    char ob_sval[1];
} PyStringObject;
'''
    _fields_ = PyObject_VAR_HEAD + [('ob_shash', ctypes.c_long), ('ob_sstate',
                                    ctypes.c_int), ('ob_sval', ctypes.c_char*1)]
StringObject = _POINTER(PyStringObject)
_declare(StringObject, str)

class PyUnicodeObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    Py_ssize_t length;
    Py_UNICODE *str;
    long hash;
    PyObject *defenc;
} PyUnicodeObject;
'''
    _fields_ = PyObject_HEAD + [('length', ctypes.c_ssize_t),
                                ('str',ctypes.c_wchar_p),('hash',ctypes.c_long),
                                ('defenc', Object)]
PyWStringObject = PyUnicodeObject
UnicodeObject = WStringObject = _POINTER(PyUnicodeObject)
_declare(UnicodeObject, unicode)

class PyListObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_VAR_HEAD
    PyObject **ob_item;
    Py_ssize_t allocated;
} PyListObject;
'''
    _fields_ = PyObject_VAR_HEAD + [('ob_item', ctypes.POINTER(Object)),
                                    ('allocated', ctypes.c_ssize_t)]
ListObject = _POINTER(PyListObject)
_declare(ListObject, list)

class PyTupleObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_VAR_HEAD
    PyObject *ob_item[1];
} PyTupleObject;
'''
    _fields_ = PyObject_VAR_HEAD + [('ob_item', Object * 1)]
TupleObject = _POINTER(PyTupleObject)
_declare(TupleObject, tuple)

class setentry(ctypes.Structure):
    '''
typedef struct {
    long hash;
    PyObject *key;
} setentry;
'''
    _fields_ = [('hash', ctypes.c_long), ('key', Object)]
_setentry = ctypes.POINTER(setentry)

PySet_MINSIZE = 8

class PySetObject(ctypes.Structure):
    '''
typedef struct _setobject PySetObject;
struct _setobject {
    PyObject_HEAD

    Py_ssize_t fill;
    Py_ssize_t used;
    Py_ssize_t mask;
    setentry *table;
    setentry *(*lookup)(PySetObject *so, PyObject *key, long hash);
    setentry smalltable[PySet_MINSIZE];

    long hash;
    PyObject *weakreflist;
};
'''
    _fields_ = PyObject_HEAD + [('fill', ctypes.c_ssize_t),
                                ('used', ctypes.c_ssize_t),
                                ('mask', ctypes.c_ssize_t),
                                ('table', _setentry),
                                ('lookup', ctypes.PYFUNCTYPE(_setentry, Object,
                                                            Object,
                                                            ctypes.c_long)),
                                ('smalltable', setentry * PySet_MINSIZE),
                                ('hash', ctypes.c_long),
                                ('weakreflist', Object)]
_setobject = PySetObject
SetObject = _POINTER(PySetObject)
_declare(SetObject, set)

class PyDictEntry(ctypes.Structure):
    '''
typedef struct {
    Py_ssize_t me_hash;
    PyObject *me_key;
    PyObject *me_value;
} PyDictEntry;
'''
    _fields_ = [('me_hash', ctypes.c_ssize_t), ('me_key', Object),
                ('me_value', Object)]
_DictEntry = ctypes.POINTER(PyDictEntry)

PyDict_MINSIZE = 8

class PyDictObject(ctypes.Structure):
    '''
typedef struct _dictobject PyDictObject;
struct _dictobject {
    PyObject_HEAD
    Py_ssize_t ma_fill;
    Py_ssize_t ma_used;
    Py_ssize_t ma_mask;
    PyDictEntry *ma_table;
    PyDictEntry *(*ma_lookup)(PyDictObject *mp, PyObject *key, long hash);
    PyDictEntry ma_smalltable[PyDict_MINSIZE];
};
'''
    _fields_ = PyObject_HEAD + [('ma_fill', ctypes.c_ssize_t),
                                ('ma_used', ctypes.c_ssize_t),
                                ('ma_mask', ctypes.c_ssize_t),
                                ('ma_table', _DictEntry),
                                ('ma_lookup', ctypes.PYFUNCTYPE(_DictEntry,
                                                               Object,
                                                               Object,
                                                               ctypes.c_long)),
                                ('ma_smalltable', PyDictEntry * PyDict_MINSIZE)]
_dictobject = PyDictObject
DictObject = _POINTER(PyDictObject)
_declare(DictObject, dict)

class PyFunctionObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    PyObject *func_code;
    PyObject *func_globals;
    PyObject *func_defaults;
    PyObject *func_closure;
    PyObject *func_doc;
    PyObject *func_name;
    PyObject *func_dict;
    PyObject *func_weakreflist;
    PyObject *func_module;
} PyFunctionObject;
'''
    _fields_ = PyObject_HEAD + \
               collections.OrderedDict.fromkeys(
                   ['func_code', 'func_globals', 'func_defaults', 'func_closure'
                    , 'func_doc', 'func_name', 'func_dict', 'func_weakreflist',
                    'func_module'], Object).items()
FunctionObject = _POINTER(PyFunctionObject)
_declare(FunctionObject, types.FunctionType)

class PyClassObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    PyObject	*cl_bases;
    PyObject	*cl_dict;
    PyObject	*cl_name;
    PyObject	*cl_getattr;
    PyObject	*cl_setattr;
    PyObject	*cl_delattr;
    PyObject    *cl_weakreflist;
} PyClassObject;
'''
    _fields_ = PyObject_HEAD + \
               collections.OrderedDict.fromkeys(
                   ['cl_bases', 'cl_dict', 'cl_name', 'cl_getattr', 'cl_setattr'
                    , 'cl_delattr', 'cl_weakreflist'], Object).items()
ClassObject = _POINTER(PyClassObject)
_declare(ClassObject, types.ClassType)

class PyInstanceObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    PyClassObject *in_class;
    PyObject	  *in_dict;
    PyObject	  *in_weakreflist;
} PyInstanceObject;
'''
    _fields_ = PyObject_HEAD + [('in_class', ClassObject), ('in_dict', Object),
                                ('in_weakreflist', Object)]
InstanceObject = _POINTER(PyInstanceObject)
_declare(InstanceObject, types.InstanceType)

class PyMethodObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    PyObject *im_func;
    PyObject *im_self;
    PyObject *im_class;
    PyObject *im_weakreflist;
} PyMethodObject;
'''
    _fields_ = PyObject_HEAD + \
               collections.OrderedDict.fromkeys(
                   ['im_func', 'im_self', 'im_class', 'im_weakreflist'],
                   Object).items()
MethodObject = _POINTER(PyMethodObject)
_declare(MethodObject, types.MethodType)

class PyCFunctionObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    PyMethodDef *m_ml;
    PyObject    *m_self;
    PyObject    *m_module;
} PyCFunctionObject;
'''
    _fields_ = PyObject_HEAD + [('m_ml', _MethodDef), ('m_self', Object),
                                ('m_module', Object)]
PyBuiltinObject = PyCFunctionObject
BuiltinObject = CFunctionObject = _POINTER(PyCFunctionObject)
_declare(CFunctionObject, types.BuiltinFunctionType)

PyDescr_COMMON = PyObject_HEAD + [('d_type', TypeObject), ('d_name', Object)]

class PyDescrObject(ctypes.Structure):
    '''
typedef struct {
    PyDescr_COMMON;
} PyDescrObject;
'''
    _fields_ = PyDescr_COMMON

class PyMethodDescrObject(ctypes.Structure):
    '''
typedef struct {
    PyDescr_COMMON;
    PyMethodDef *d_method;
} PyMethodDescrObject;
'''
    _fields_ = PyDescr_COMMON + [('d_method', _MethodDef)]

class PyMemberDescrObject(ctypes.Structure):
    '''
typedef struct {
    PyDescr_COMMON;
    struct PyMemberDef *d_member;
} PyMemberDescrObject;
'''
    _fields_ = PyDescr_COMMON + [('d_member', _MemberDef)]

class PyGetSetDescrObject(ctypes.Structure):
    '''
typedef struct {
    PyDescr_COMMON;
    PyGetSetDef *d_getset;
} PyGetSetDescrObject;
'''
    _fields_ = PyDescr_COMMON + [('d_getset', _GetSetDef)]

class PyWrapperDescrObject(ctypes.Structure):
    '''
typedef struct {
    PyDescr_COMMON;
    struct wrapperbase *d_base;
    void *d_wrapped;
} PyWrapperDescrObject;
'''
    _fields_ = PyDescr_COMMON + [('d_base', _wrapperbase), ('d_wrapped',
                                                            ctypes.c_void_p)]
MethodDescrObject = _POINTER(PyMethodDescrObject)
MemberDescrObject = _POINTER(PyMemberDescrObject)
GetSetDescrObject = _POINTER(PyGetSetDescrObject)
WrapperDescrObject = _POINTER(PyWrapperDescrObject)
_declare(MethodDescrObject, type(dict.__dict__['fromkeys']))
_declare(MethodDescrObject, type(dict.keys))
_declare(MemberDescrObject, type(slice.start))
_declare(GetSetDescrObject, type(int.imag))
_declare(WrapperDescrObject, type(type(type(raw_input).__call__).__call__))

class PyModuleObject(ctypes.Structure):
    _fields_ = PyObject_HEAD + [('md_dict',DictObject)]
ModuleObject = _POINTER(PyModuleObject)
_declare(ModuleObject, type(ctypes))

class PyDictProxyObject(ctypes.Structure):
    _fields_ = PyObject_HEAD + [('dp_dict', DictObject)]
DictProxyObject = _POINTER(PyDictProxyObject)
_declare(DictProxyObject, type(int.__dict__))

class PyCellObject(ctypes.Structure):
    '''
typedef struct {
	PyObject_HEAD
	PyObject *ob_ref;	/* Content of the cell or NULL when empty */
} PyCellObject;
'''
    _fields_ = PyObject_HEAD + [('ob_ref', Object)]
CellObject = _POINTER(PyCellObject)
def __(a):
    def ___():return a
    return ___
CellType = type(__(0).func_closure[0])
_declare(CellObject, CellType)

class PyCodeObject(ctypes.Structure):
    '''
typedef struct {
    PyObject_HEAD
    int co_argcount;		/* #arguments, except *args */
    int co_nlocals;		/* #local variables */
    int co_stacksize;		/* #entries needed for evaluation stack */
    int co_flags;		/* CO_..., see below */
    PyObject *co_code;		/* instruction opcodes */
    PyObject *co_consts;	/* list (constants used) */
    PyObject *co_names;		/* list of strings (names used) */
    PyObject *co_varnames;	/* tuple of strings (local variable names) */
    PyObject *co_freevars;	/* tuple of strings (free variable names) */
    PyObject *co_cellvars;      /* tuple of strings (cell variable names) */
    /* The rest doesn't count for hash/cmp */
    PyObject *co_filename;	/* string (where it was loaded from) */
    PyObject *co_name;		/* string (name, for reference) */
    int co_firstlineno;		/* first source line number */
    PyObject *co_lnotab;	/* string (encoding addr<->lineno mapping) See
				   Objects/lnotab_notes.txt for details. */
    void *co_zombieframe;     /* for optimization only (see frameobject.c) */
    PyObject *co_weakreflist;   /* to support weakrefs to code objects */
} PyCodeObject;
'''
    _fields_ = PyObject_HEAD + [('co_argcount', ctypes.c_int), ('co_nlocals',
                                                                ctypes.c_int),
                                ('co_stacksize', ctypes.c_int), ('co_flags',
                                                                 ctypes.c_int),
                                ('co_code', Object), ('co_consts', Object), (
                                    'co_names', Object), ('co_varnames', Object)
                                , ('co_freevars', Object),
                                ('co_cellvars', Object), ('co_filename', Object)
                                , ('co_name', Object), ('co_firstlineno',
                                                        ctypes.c_int), (
                                                            'co_lnotab',Object),
                                ('co_zombieframe', ctypes.c_void_p), (
                                    'co_weakreflist', Object)]
CodeObject = _POINTER(PyCodeObject)
_declare(CodeObject, type(_declare.func_code))
