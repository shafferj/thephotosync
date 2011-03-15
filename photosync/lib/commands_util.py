import os
import ConfigParser
import errno
import threading
import atexit
import logging
import subprocess
import time

import paste.fixture
import paste.registry
from paste.script.command import Command, BadCommand
from paste.script.serve import DaemonizeException
from paste.script.serve import LazyWriter
from paste.script.serve import live_pidfile, read_pidfile, _remove_pid_file
from paste.deploy import loadapp
from sqlalchemy import engine_from_config

from photosync.worker.run import run_worker
from photosync.model import init_model


class BaseCommand(Command):
    """Base class for making commands.

    This base class will read a config file and load up the regular execution
    environment of the app with proper access to mysql and other utilities.
    """


    CONFIG_SECTION = 'photosync:worker'
    requires_config_file = True
    takes_config_file = True

    parser = Command.standard_parser(simulate=True)

    min_args = 0
    group_name = 'photosync'

    default_verbosity = 2

    possible_subcommands = ()

    cmd = None
    restvars = []

    def command(self):
        if self.requires_config_file:
            if not self.args:
                raise BadCommand('You must give a config file')
            app_spec = self.args[0]
            if (len(self.args) > 1
                and self.args[1] in self.possible_subcommands):
                self.cmd = self.args[1]
                self.restvars = self.args[2:]
            else:
                self.cmd = None
                self.restvars = self.args[1:]
        else:
            app_spec = ""
            if (self.args
                and self.args[0] in self.possible_subcommands):
                self.cmd = self.args[0]
                self.restvars = self.args[1:]
            else:
                self.cmd = None
                self.restvars = self.args[:]

        self.logging_file_config(app_spec)

        config_name = 'config:%s' % app_spec
        here_dir = os.getcwd()

        parser = ConfigParser.ConfigParser()
        parser.read([app_spec])
        if not parser.has_section(self.CONFIG_SECTION):
            raise BadCommand('Error: %s missing %s configuration section' % \
                                 (app_spec, self.CONFIG_SECTION))
        self.config = dict(parser.items(self.CONFIG_SECTION, vars={'here':here_dir}))

        engine = engine_from_config(self.config, 'sqlalchemy.')
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

