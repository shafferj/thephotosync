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

STATE_BURIED = 'buried'

DEFAULT_TUBE = 'default'
DEFAULT_BEANSTALK = 'localhost:11300'


def get_handler_name(handler):
    return '%s:%s' % (handler.__module__, handler.__name__)

def register(func):
    if inspect.isclass(func):
        @wraps(func)
        def caller(job, *args, **kwargs):
            instance = func(job, *args, **kwargs)
            return instance()
        register_handler(caller)
    else:
        register_handler(func)
    return func


_connection = None
def _get_connection():
    global _connection
    if not _connection:
        try:
            host, port = g.DEFAULT_BEANSTALK.split(':')
        except TypeError:
            host, port = DEFAULT_BEANSTALK.split(':')
        _connection = beanstalkc.Connection(host=host, port=int(port))
    return _connection

def register_handler(handler):
    _handlers[get_handler_name(handler)] = handler

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

    connection = _get_connection()

    try:
        # TODO: stop using pylons global object for configuration
        # because it is not always available
        tube = g.DEFAULT_BEANSTALK_TUBE
    except TypeError:
        tube = DEFAULT_TUBE

    try:
        connection.use(tube)
    except beanstalkc.UnexpectedResponse, e:
        log.exception(e)
        log.error("Got an unexpected beanstalk response using tube %s. Retrying", tube)
        connection.use(tube)
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
        return _handlers[name]

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
