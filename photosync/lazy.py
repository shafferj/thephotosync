class lazy(object):
    '''Decorator for lazy object retrieval.

    Usage:

      >>> class Foo(object):
      ...   @lazy
      ...   def big_computation(self):
      ...       print "I'm doing a big computation"
      ...       return 1+1

    When you get the result the first time, it will do the computation.

      >>> f = Foo()
      >>> a = f.big_computation
      I'm doing a big computation
      >>> a
      2

    The second time around, we get the cached result.

      >>> f.big_computation
      2
    '''

    def __init__(self, func):
        self._func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, klass=None):
        if obj is None:
            return None
        result = obj.__dict__[self.__name__] = self._func(obj)
        return result

