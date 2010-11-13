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
            register_handler(caller, tube=tube, server=server)
        else:
            register_handler(func, tube=tube, server=server)
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


def register_handler(handler, tube='default', server=None):
    _handlers[get_handler_name(handler)] = {'handler':handler,
                                            'tube':tube}

def from_id(id):
    if id is None:
        return None
    connection = _get_connection()
    beanstalk_job = connection.peek(int(id))
    job = Job(beanstalk_job) if beanstalk_job else None
    return job

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

def submit(handler, *args, **kwargs):
    return submit_advanced(handler, args, kwargs)


class Job(object):

    def __init__(self, beanstalk_job=None):
        self.job = beanstalk_job
        self.data = json.loads(self.job.body)

    def resubmit(self, delay=0):
        return submit_advanced(
            self.handler,
            self.data['args'],
            self.data['kwargs'],
            delay=delay)

    def delete(self):
        return self.job.delete()

    @lazy
    def stats(self):
        return self.job.stats()

    @property
    def time_left(self):
        return self.stats['time-left']

    @property
    def handler(self):
        name = self.data['handler']
        return _handlers[name]['handler']

    @property
    def queue_id(self):
        return self.job.jid

    def run(self):
        try:
            result = self.handler(self.job, *self.data['args'], **self.data['kwargs'])
        except Exception, e:
            traceback.print_exc()
            log.exception("Uncaught exception while running job %s", self.queue_id)
            self.job.bury()
        else:
            try:
                self.job.delete()
            except Exception, e:
                log.warn("Failed to delete job?? whatevs... %r", e)
            return result
