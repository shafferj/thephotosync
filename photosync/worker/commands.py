from paste.script.command import Command, BadCommand

from photosync.worker.run import run_worker
from photosync.lib.commands_util import BaseCommand

class RunWorkerCommand(BaseCommand):
    """Start a beanstalk worker

    Example::

        $ paster runworker development.ini

    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    CONFIG_SECTION = 'photosync:worker'

    def command(self):
        """Main command that starts the worker."""
        super(RunWorkerCommand, self).command()

        def get_or_raise(key):
            if key not in self.config:
                raise BadCommand(
                    'Error: %s %s configuration section is missing a '
                    'value for %s' % (app_spec, self.CONFIG_SECTION, key))
            return self.config[key]

        host, port = get_or_raise('server').split(':')
        tubes = self.config.get('tubes')
        tubes = tubes.split(' ') if tubes else ()
        pool_size = self.config.get('pool_size')

        #TODO: make this configuration system suck less
        from photosync.worker import job
        job.DEFAULT_TUBE = self.config.get(
            'photosync.default_beanstalk_tube', job.DEFAULT_TUBE)
        job.DEFAULT_BEANSTALK = self.config.get(
            'photosync.default_beanstalk', job.DEFAULT_BEANSTALK)

        if pool_size:
            pool_size = int(pool_size)
        run_worker(host, port, tubes, pool_size)


