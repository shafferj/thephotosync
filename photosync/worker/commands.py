import os
import ConfigParser

from paste.script.command import Command, BadCommand

from photosync.worker.run import run_worker

CONFIG_SECTION = 'photosync:worker'

class RunWorkerCommand(Command):
    """Start a Gearman worker

    Example::

        $ paster runworker development.ini

    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    min_args = 0
    max_args = 1
    group_name = 'photosync'

    parser = Command.standard_parser(simulate=True)

    parser.add_option('-q',
                      action='count',
                      dest='quiet',
                      default=0,
                      help=("Do not load logging configuration from the "
                            "config file"))

    def command(self):
        """Main command that starts the worker."""
        if len(self.args) == 0:
            # Assume the .ini file is ./development.ini
            config_file = 'development.ini'
            if not os.path.isfile(config_file):
                raise BadCommand('%sError: CONFIG_FILE not found at: .%s%s\n'
                                 'Please specify a CONFIG_FILE' % \
                                 (self.parser.get_usage(), os.path.sep,
                                  config_file))
        else:
            config_file = self.args[0]

        config_name = 'config:%s' % config_file
        here_dir = os.getcwd()

        if not self.options.quiet:
            # Configure logging from the config file
            self.logging_file_config(config_file)

        parser = ConfigParser.ConfigParser()
        parser.read([config_file])
        if not parser.has_section(CONFIG_SECTION):
            raise BadCommand('Error: %s missing %s configuration section' % \
                                 (config_file, CONFIG_SECTION))

        def get_or_raise(key):
            val = parser.get(CONFIG_SECTION, key)
            if not val:
                raise BadCommand(
                    'Error: %s %s configuration section is missing a '
                    'value for %s' % (config_file, CONFIG_SECTION, key))
            return val

        servers = get_or_raise('servers').split(' ')
        client_id = get_or_raise('id')
        run_worker(servers, client_id)
