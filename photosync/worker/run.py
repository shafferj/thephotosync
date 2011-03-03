import json
import time
import logging
import multiprocessing

import beanstalkc
from photosync.model.meta import Session
from photosync.model import User, SyncRecord, AsyncTask
from photosync.worker import tasks
from photosync.worker.job import Job

log = logging.getLogger(__name__)

def task_ping(worker, job):
    log.info("ping %s", job.data)
    return "pong %s" % job.data

def run_loop(host, port, tubes=()):
    log.info("Starting photosync worker")
    log.info("Connecting to server: %s:%s", host, port)

    beanstalk = beanstalkc.Connection(host=host, port=int(port))


    for tube in tubes:
        beanstalk.watch(tube)

    # stop watching all other tubes, including default
    # we have to do this second because beanstalk must
    # always watch at least one tube.
    for tube in beanstalk.watching():
        if tube not in tubes:
            beanstalk.ignore(tube)
    log.info("Watching tubes: %s", ', '.join(beanstalk.watching()))

    while True:
        job = beanstalk.reserve()
        log.info("Processing job %s", job.jid)
        Job(beanstalk_job=job).run()

def run_worker(host, port, tubes=(), pool_size=None):
    # Weeee! we're going to create a pool and run tons of workers!
    pool_size = pool_size or multiprocessing.cpu_count()

    log.info("Kicking off %s worker processes", pool_size)

    if pool_size > 1:
        pool = multiprocessing.Pool(pool_size - 1)
        for i in xrange(pool_size-1):
            pool.apply_async(run_loop, [host, port], {'tubes':tubes})

    run_loop(host, port, tubes=tubes)
