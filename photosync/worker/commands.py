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

CONFIG_SECTION = 'photosync:worker'

class RunWorkerCommand(Command):
    """Start a beanstalk worker

    Example::

        $ paster runworker development.ini

    """
    summary = __doc__.splitlines()[0]
    usage = '\n' + __doc__

    takes_config_file = 1
    requires_config_file = True

    min_args = 0
    group_name = 'photosync'

    parser = Command.standard_parser(simulate=True)

    parser.add_option('--daemon',
                      dest="daemon",
                      action="store_true",
                      help="Run in daemon (background) mode")

    parser.add_option('--pid-file',
                      dest='pid_file',
                      metavar='FILENAME',
                      help=("Save PID to file (default to worker.pid if "
                            "running in daemon mode)"))
    parser.add_option('--log-file',
                      dest='log_file',
                      metavar='LOG_FILE',
                      help="Save output to the given log file (redirects stdout)")

    parser.add_option('--user',
                      dest='set_user',
                      metavar="USERNAME",
                      help="Set the user (usually only possible when run as root)")
    parser.add_option('--group',
                      dest='set_group',
                      metavar="GROUP",
                      help="Set the group (usually only possible when run as root)")
    parser.add_option('--stop-daemon',
                      dest='stop_daemon',
                      action='store_true',
                      help=('Stop a daemonized server (given a PID file, or '
                            'default worker.pid file)'))

    parser.add_option('--status',
                      action='store_true',
                      dest='show_status',
                      help="Show the status of the (presumably daemonized) server")

    parser.add_option('-q',
                      action='count',
                      dest='quiet',
                      default=0,
                      help=("Do not load logging configuration from the "
                            "config file"))

    default_verbosity = 2

    possible_subcommands = ('start', 'stop', 'restart', 'status')
    def command(self):
        """Main command that starts the worker."""
        if self.options.stop_daemon:
            return self.stop_daemon()

        if not hasattr(self.options, 'set_user'):
            # Windows case:
            self.options.set_user = self.options.set_group = None
        # @@: Is this the right stage to set the user at?
        self.change_user_group(
            self.options.set_user, self.options.set_group)

        if self.requires_config_file:
            if not self.args:
                raise BadCommand('You must give a config file')
            app_spec = self.args[0]
            if (len(self.args) > 1
                and self.args[1] in self.possible_subcommands):
                cmd = self.args[1]
                restvars = self.args[2:]
            else:
                cmd = None
                restvars = self.args[1:]
        else:
            app_spec = ""
            if (self.args
                and self.args[0] in self.possible_subcommands):
                cmd = self.args[0]
                restvars = self.args[1:]
            else:
                cmd = None
                restvars = self.args[:]

        config_name = 'config:%s' % app_spec
        here_dir = os.getcwd()

        if cmd == 'status' or self.options.show_status:
            return self.show_status()
        if cmd == 'restart' or cmd == 'stop':
            result = self.stop_daemon()
            if result:
                if cmd == 'restart':
                    print "Could not stop daemon; aborting"
                else:
                    print "Could not stop daemon"
                return result
            if cmd == 'stop':
                return result


        # setup default daemon options
        if getattr(self.options, 'daemon', False):
            if not self.options.pid_file:
                self.options.pid_file = 'worker.pid'
            if not self.options.log_file:
                self.options.log_file = 'worker.log'

        # Ensure the log file is writeable
        if self.options.log_file:
            try:
                writeable_log_file = open(self.options.log_file, 'a')
            except IOError, ioe:
                msg = 'Error: Unable to write to log file: %s' % ioe
                raise BadCommand(msg)
            writeable_log_file.close()

        # Ensure the pid file is writeable
        if self.options.pid_file:
            try:
                writeable_pid_file = open(self.options.pid_file, 'a')
            except IOError, ioe:
                msg = 'Error: Unable to write to pid file: %s' % ioe
                raise BadCommand(msg)
            writeable_pid_file.close()

        # daemonize if necessary
        if getattr(self.options, 'daemon', False):
            try:
                self.daemonize()
            except DaemonizeException, ex:
                if self.verbose > 0:
                    print str(ex)
                return

        if self.options.pid_file:
            self.record_pid(self.options.pid_file)

        if self.options.log_file:
            stdout_log = LazyWriter(self.options.log_file, 'a')
            sys.stdout = stdout_log
            sys.stderr = stdout_log
            logging.basicConfig(stream=stdout_log)

        if not self.options.quiet:
            # Configure logging from the config file
            self.logging_file_config(app_spec)

        parser = ConfigParser.ConfigParser()
        parser.read([app_spec])
        if not parser.has_section(CONFIG_SECTION):
            raise BadCommand('Error: %s missing %s configuration section' % \
                                 (app_spec, CONFIG_SECTION))
        config = dict(parser.items(CONFIG_SECTION, vars={'here':here_dir}))

        def get_or_raise(key):
            if key not in config:
                raise BadCommand(
                    'Error: %s %s configuration section is missing a '
                    'value for %s' % (app_spec, CONFIG_SECTION, key))
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
        pool_size = config.get('pool_size')

        #TODO: make this configuration system suck less
        from photosync.worker import job
        job.DEFAULT_TUBE = config.get(
            'photosync.default_beanstalk_tube', job.DEFAULT_TUBE)
        job.DEFAULT_BEANSTALK = config.get(
            'photosync.default_beanstalk', job.DEFAULT_BEANSTALK)

        if pool_size:
            pool_size = int(pool_size)
        run_worker(host, port, tubes, pool_size)


    def daemonize(self):
        pid = live_pidfile(self.options.pid_file)
        if pid:
            raise DaemonizeException(
                "Daemon is already running (PID: %s from PID file %s)"
                % (pid, self.options.pid_file))

        if self.verbose > 0:
            print 'Entering daemon mode'
        pid = os.fork()

        if pid:
            # The forked process also has a handle on resources, so we
            # *don't* want proper termination of the process, we just
            # want to exit quick (which os._exit() does)
            os._exit(0)
        # Make this the session leader
        os.setsid()

        # Fork again for good measure!
        pid = os.fork()
        if pid:
            os._exit(0)

        # @@: Should we set the umask and cwd now?

        import resource  # Resource usage information.
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = MAXFD
        # Iterate through and close all file descriptors.
        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:  # ERROR, fd wasn't open to begin with (ignored)
                pass

        if (hasattr(os, "devnull")):
            REDIRECT_TO = os.devnull
        else:
            REDIRECT_TO = "/dev/null"
        os.open(REDIRECT_TO, os.O_RDWR)  # standard input (0)
        # Duplicate standard input to standard output and standard error.
        os.dup2(0, 1)  # standard output (1)
        os.dup2(0, 2)  # standard error (2)


    def record_pid(self, pid_file):
        pid = os.getpid()
        if self.verbose > 1:
            print 'Writing PID %s to %s' % (pid, pid_file)
        f = open(pid_file, 'w')
        f.write(str(pid))
        f.close()
        atexit.register(_remove_pid_file, pid, pid_file, self.verbose)

    def stop_daemon(self):
        pid_file = self.options.pid_file or 'worker.pid'
        if not os.path.exists(pid_file):
            print 'No PID file exists in %s' % pid_file
            return 1
        pid = read_pidfile(pid_file)
        if not pid:
            print "Not a valid PID file in %s" % pid_file
            return 1
        pid = live_pidfile(pid_file)
        if not pid:
            print "PID in %s is not valid (deleting)" % pid_file
            try:
                os.unlink(pid_file)
            except (OSError, IOError), e:
                print "Could not delete: %s" % e
                return 2
            return 1
        for j in range(10):
            if not live_pidfile(pid_file):
                break
            import signal
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
        else:
            print "failed to kill process %s" % pid
            return 3
        if os.path.exists(pid_file):
            os.unlink(pid_file)
        return 0

    def show_status(self):
        pid_file = self.options.pid_file or 'worker.pid'
        if not os.path.exists(pid_file):
            print 'No PID file %s' % pid_file
            return 1
        pid = read_pidfile(pid_file)
        if not pid:
            print 'No PID in file %s' % pid_file
            return 1
        pid = live_pidfile(pid_file)
        if not pid:
            print 'PID %s in %s is not running' % (pid, pid_file)
            return 1
        print 'Worker running in PID %s' % pid
        return 0

    def change_user_group(self, user, group):
        if not user and not group:
            return
        import pwd, grp
        uid = gid = None
        if group:
            try:
                gid = int(group)
                group = grp.getgrgid(gid).gr_name
            except ValueError:
                import grp
                try:
                    entry = grp.getgrnam(group)
                except KeyError:
                    raise BadCommand(
                        "Bad group: %r; no such group exists" % group)
                gid = entry.gr_gid
        try:
            uid = int(user)
            user = pwd.getpwuid(uid).pw_name
        except ValueError:
            try:
                entry = pwd.getpwnam(user)
            except KeyError:
                raise BadCommand(
                    "Bad username: %r; no such user exists" % user)
            if not gid:
                gid = entry.pw_gid
            uid = entry.pw_uid
        if self.verbose > 0:
            print 'Changing user to %s:%s (%s:%s)' % (
                user, group or '(unknown)', uid, gid)
        if gid:
            os.setgid(gid)
        if uid:
            os.setuid(uid)

def _remove_pid_file(written_pid, filename, verbosity):
    current_pid = os.getpid()
    if written_pid != current_pid:
        # A forked process must be exiting, not the process that
        # wrote the PID file
        return
    if not os.path.exists(filename):
        return
    f = open(filename)
    content = f.read().strip()
    f.close()
    try:
        pid_in_file = int(content)
    except ValueError:
        pass
    else:
        if pid_in_file != current_pid:
            print "PID file %s contains %s, not expected PID %s" % (
                filename, pid_in_file, current_pid)
            return
    if verbosity > 0:
        print "Removing PID file %s" % filename
    try:
        os.unlink(filename)
        return
    except OSError, e:
        # Record, but don't give traceback
        print "Cannot remove PID file: %s" % e
    # well, at least lets not leave the invalid PID around...
    try:
        f = open(filename, 'w')
        f.write('')
        f.close()
    except OSError, e:
        print 'Stale PID left in file: %s (%e)' % (filename, e)
    else:
        print 'Stale PID removed'
