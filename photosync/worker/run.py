import json
import time
import logging

import beanstalkc
from photosync.model.meta import Session
from photosync.model import User, SyncRecord, AsyncTask
from photosync.worker import tasks
from photosync.worker.job import Job

log = logging.getLogger(__name__)

def task_ping(worker, job):
    log.info("ping %s", job.data)
    return "pong %s" % job.data

def run_worker(host, port, tubes=()):

    log.info("Starting photosync worker")
    log.info("Connecting to server: %s:%s", host, port)

    beanstalk = beanstalkc.Connection(host=host, port=int(port))

    log.info("Watching tubes: %s", ', '.join(tubes))
    for tube in tubes:
        beanstalk.watch(tube)

    while True:
        job = beanstalk.reserve()
        log.info("Processing job %s", job.jid)
        Job(beanstalk_job=job).run()
