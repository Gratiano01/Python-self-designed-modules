class NewTypeMeta(type):
    def __new__(mcls, name, bases, varribles):
        t = varribles['_raw_type']
        if varribles.has_key('__doc__'):
            doc = varribles['__doc__']
        else:
            doc = t.__doc__
        varribles.update(vars(t))
        varribles['__doc__'] = doc
        cls = type.__new__(mcls, name, bases, varribles)
        cls.__module__ = getattr(t, '__module__', '__builtin__')
        return cls

    def __call__(cls, *args, **kwargs):
        return cls._func_new(*args, **kwargs)

    def __instancecheck__(cls, inst):
        return isinstance(inst, cls._raw_type)

    def __subclasscheck__(cls, sub):
        return issubclass(sub, cls._raw_type)

    def __eq__(cls, klass):
        return type.__eq__(cls, klass) or (klass == cls._raw_type)

    def __str__(cls):
        return str(cls._raw_type)

    def __repr__(cls):
        return repr(cls._raw_type)
