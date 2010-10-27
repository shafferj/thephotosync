import logging

from gearman import GearmanWorker

log = logging.getLogger(__name__)

def task_ping(worker, job):
    log.info("ping %s", job.data)
    return "pong %s" % job.data

def run_worker(servers, client_id):
    log.info("Starting gearman worker '%s'", client_id)
    log.info("Connecting to servers: %s", ' '.join(servers))
    worker = GearmanWorker(servers)
    worker.set_client_id(client_id)
    worker.register_task('ping', task_ping)
    worker.work()
