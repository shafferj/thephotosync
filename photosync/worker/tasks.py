import time
import traceback
import logging

from photosync.model.meta import Session
from photosync.model import User, SyncRecord, AsyncTask

log = logging.getLogger(__name__)


class TaskHandler(object):

    def __init__(self, worker, job):
        self.worker = worker
        self.job = job

    _task = None
    _task_fetched = False
    @property
    def task(self):
        if not self._task_fetched:
            self._task_fetched = True
            self._task = Session.query(AsyncTask).filter_by(
                gearman_unique=self.job.unique).first()
        return self._task


    @classmethod
    def runner(cls, worker, job):
        try:
            return cls(worker, job).run()
        except Exception, e:
            traceback.print_exc()
            log.exception("Failed to run task %s", self.__class__.__name__)
            raise

    def set_status(self, completed, total, data):
        log.info("%s %s Completed %s/%s: %r",
                 self.__class__.__name__, self.job.unique,
                 completed, total, data)
        self.task.set_status(completed, total, data, worker=self.worker, job=self.job)
        self.worker.send_job_status(self.job, completed, total)
        if data:
            self.worker.send_job_data(self.job, str(data))
        Session.commit()

    def run(self):
        return


class LongPing(TaskHandler):

    def run(self):
        N = int(self.job.data)
        for i in xrange(N):
            log.info("did %s sleeps" % i)
            self.set_status(i+1, N, "did %s sleeps" % i)
            time.sleep(1)
        return "all done"
