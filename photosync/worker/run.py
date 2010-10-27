import time
import logging

from gearman import GearmanWorker
from photosync.model.meta import Session
from photosync.model import User, SyncRecord, AsyncTask

log = logging.getLogger(__name__)

def task_ping(worker, job):
    log.info("ping %s", job.data)
    return "pong %s" % job.data

def task_long_ping(worker, job):
    task = Session.query(AsyncTask).filter_by(gearman_unique=job.unique).first()
    if not task:
        return
    N = int(job.data)
    for i in xrange(N):
        log.info("did %s sleeps" % i)
        task.set_status(i, N, "did %s sleeps" % i, worker, job)
        Session.commit()
        time.sleep(1)
    return "all done"

def run_worker(servers, client_id):
    log.info("Starting gearman worker '%s'", client_id)
    log.info("Connecting to servers: %s", ' '.join(servers))
    worker = GearmanWorker(servers)
    worker.set_client_id(client_id)
    worker.register_task('ping', task_ping)
    worker.register_task('long_ping', task_long_ping)
    worker.work()
