from functools import wraps
import traceback
import logging
import json
import inspect
import beanstalkc

from pylons import app_globals as g

log = logging.getLogger(__name__)
_handlers = {}

def _get_handler_name(handler):
    return '%s:%s' % (handler.__module__, handler.__name__)

def register(tube='default', server=None):
    def decorator(func):
        if inspect.isclass(func):
            @wraps(func)
            def caller(job, *args, **kwargs):
                instance = func(job, *args, **kwargs)
                return instance()
            Job.register_handler(caller, tube=tube, server=server)
        else:
            Job.register_handler(func, tube=tube, server=server)
        return func

    if callable(tube) or inspect.isclass(tube):
        func = tube
        tube = 'default'
        return decorator(func)
    return decorator


class Job(object):

    def __init__(self, beanstalk_job=None):
        self.__job = beanstalk_job
        self.__data = json.loads(self.__job.body)

    @staticmethod
    def register_handler(handler, tube='default', server=None):
        _handlers[_get_handler_name(handler)] = {'handler':handler,
                                                 'tube':tube,
                                                 'server':server}

    @staticmethod
    def submit_advanced(handler, args, kwargs, **put_kwargs):
        name = _get_handler_name(handler)
        if name not in _handlers:
            raise KeyError("The handler %s has not been registered" % name)

        handler_config = _handlers[name]

        payload = {'handler':name,
                   'args':args,
                   'kwargs':kwargs}
        data = json.dumps(payload)

        host, port = (handler_config.get('server') or g.DEFAULT_BEANSTALK).split(':')
        connection = beanstalkc.Connection(host=host, port=int(port))
        id = connection.put(data, **put_kwargs)
        connection.close()
        return id

    @staticmethod
    def submit(handler, *args, **kwargs):
        return Job.submit_advanced(handler, args, kwargs)

    @property
    def handler(self):
        name = self.__data['handler']
        return _handlers[name]['handler']

    @property
    def queue_id(self):
        return self.__job.jid

    def run(self):
        try:
            result = self.handler(self, *self.__data['args'], **self.__data['kwargs'])
        except Exception, e:
            traceback.print_exc()
            log.exception("Uncaught exception while running job %s", self.queue_id)
            self.__job.bury()
        else:
            self.__job.delete()
            return result
