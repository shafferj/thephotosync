from functools import wraps
import traceback
import logging
import json
import inspect
import beanstalkc

from pylons import app_globals as g

from photosync.lazy import lazy

log = logging.getLogger(__name__)
_handlers = {}

def get_handler_name(handler):
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


_connection = None
def _get_connection():
    global _connection
    if not _connection:
        host, port = g.DEFAULT_BEANSTALK.split(':')
        _connection = beanstalkc.Connection(host=host, port=int(port))
    return _connection


class Job(object):

    def __init__(self, beanstalk_job=None):
        self.__job = beanstalk_job
        self.__data = json.loads(self.__job.body)

    @staticmethod
    def from_id(id):
        if id is None:
            return None
        connection = _get_connection()
        beanstalk_job = connection.peek(int(id))
        job = Job(beanstalk_job) if beanstalk_job else None
        return job

    @staticmethod
    def register_handler(handler, tube='default', server=None):
        _handlers[get_handler_name(handler)] = {'handler':handler,
                                                 'tube':tube}

    @staticmethod
    def submit_advanced(handler, args, kwargs, **put_kwargs):
        name = get_handler_name(handler)
        if name not in _handlers:
            raise KeyError("The handler %s has not been registered" % name)

        handler_config = _handlers[name]

        payload = {'handler':name,
                   'args':args,
                   'kwargs':kwargs}
        data = json.dumps(payload)

        host, port = g.DEFAULT_BEANSTALK.split(':')
        connection = _get_connection()
        if 'tube' in handler_config:
            connection.use(handler_config['tube'])
        id = connection.put(data, **put_kwargs)
        return id

    def resubmit(self):
        return Job.submit_advanced(
            self.handler,
            self.__data['args'],
            self.__data['kwargs'])

    def delete(self):
        return self.__job.delete()

    @lazy
    def stats(self):
        return self.__job.stats()

    @property
    def time_left(self):
        return self.stats['time-left']

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
