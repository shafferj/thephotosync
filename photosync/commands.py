import logging

from photosync.lib.commands_util import BaseCommand

from photosync.model import AsyncTask, User
from photosync.model.meta import Session
import photosync.worker.tasks

log = logging.getLogger(__name__)


class KickCommand(BaseCommand):
    """Kick burried jobs into action."""

    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    def command(self):
        """Main command that starts the worker."""
        super(KickCommand, self).command()

        users = Session.query(User)\
            .filter(User.fb_uid != None)\
            .filter(User.flickr_nsid != None)

        if self.options.simulate:
            log.info("--SIMULATING--")
        for user in users:
            tasks = AsyncTask.get_for_user(user.id)
            for task in tasks:
                if not (task.is_completed or task.time_left) and task.is_buried:
                    log.info("Running task %r", task)
                    if not self.options.simulate:
                        task.run_now()
