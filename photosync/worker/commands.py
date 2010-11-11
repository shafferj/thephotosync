import os
import ConfigParser

import paste.fixture
import paste.registry
from paste.script.command import Command, BadCommand
from paste.deploy import loadapp
from sqlalchemy import engine_from_config

from photosync.worker.run import run_worker
from photosync.model import init_model

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
        config = dict(parser.items(CONFIG_SECTION, vars={'here':here_dir}))

        def get_or_raise(key):
            if key not in config:
                raise BadCommand(
                    'Error: %s %s configuration section is missing a '
                    'value for %s' % (config_file, CONFIG_SECTION, key))
            return config[key]

        engine = engine_from_config(config, 'sqlalchemy.')
        init_model(engine)

        # Load the wsgi app first so that everything is initialized right
        wsgiapp = loadapp(config_name, relative_to=here_dir)
        test_app = paste.fixture.TestApp(wsgiapp)

        # Query the test app to setup the environment
        tresponse = test_app.get('/_test_vars')
        request_id = int(tresponse.body)

        # Restore the state of the Pylons special objects
        # (StackedObjectProxies)
        paste.registry.restorer.restoration_begin(request_id)



        host, port = get_or_raise('server').split(':')
        tubes = config.get('tubes')
        tubes = tubes.split(' ') if tubes else ()
        run_worker(host, port, tubes)
