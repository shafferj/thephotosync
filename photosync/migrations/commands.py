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

from photosync.migrations import scripts
from photosync.lib.commands_util import BaseCommand


class RunMigrationCommand(BaseCommand):
    """Run a migration script

    Example::

        $ paster migrate development.ini some_migration

    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    parser = Command.standard_parser(simulate=True)
    parser.add_option('--list',
                      dest='list_scripts',
                      action='store_true',
                      help="List available migration scripts")

    def command(self):
        """Main command that starts the migration."""
        super(RunMigrationCommand, self).command()

        if self.options.list_scripts:
            self.list_scripts()
            return

        if not self.restvars:
            raise BadCommand("You must specify a migration script to run")

        script = self.restvars[0]

        if not hasattr(scripts, script):
            raise BadCommand("The migration script %s does not exist" % script)

        migrator = getattr(scripts, script)
        migrator()


    def list_scripts(self):
        print "Available migration scripts:"
        for script_name in scripts.__all__:
            script = getattr(scripts, script_name)
            doc = script.__doc__ or ""
            print "  ", script_name, "\t", doc.splitlines()[0] if doc else ""
