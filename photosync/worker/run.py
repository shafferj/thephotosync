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

#def task_long_ping(worker, job):
#    task = Session.query(AsyncTask).filter_by(gearman_unique=job.unique).first()
#    if not task:
#        return
#    N = int(job.data)
#    for i in xrange(N):
#        log.info("did %s sleeps" % i)
#        task.set_status(i, N, "did %s sleeps" % i, worker, job)
#        Session.commit()
#        time.sleep(1)
#    return "all done"

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
