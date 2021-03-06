Before you begin
================

PhotoSync syncs photos between a number of different services.
In order to gain api access to these services you'll have to
register for accounts and setup developer applications and collect
api keys.

Facebook: https://www.facebook.com/developers/createapp.php

Flickr: http://www.flickr.com/services/apps/create/apply/


Setting up an ubuntu development box
====================================

You need to install lots of stuff that you might not have::

  sudo apt-get install python-dev git-core build-essential libmysqlclient-dev
  sudo apt-get install nginx
  sudo apt-get install mysql-server python-pycurl libcurl3 beanstalkd

Now you can check out the repo::

  git clone https://pcardune@github.com/pcardune/photosync.git

Install eazy_install if you don't have it already::

  cd photosync
  sudo python ez_setup.py

Create and activate a virtual environment::

  sudo easy_install virtualenv
  virtualenv env
  source env/bin/activate

Setup the photosync code::

  python setup.py develop

Setup an empty DB called photosync::

  mysql -u root -p
  > create database photosync;

Create a configuration file using the helper script.  You will be asked
to enter information like api keys::

  paster make-config photosync development.ini

Run a script to create all the required tables::

  paster setup-app development.ini

Now you can start the server::

  paster serve development.ini

If you want to test running the server behind nginx, you can look at
a sample configuration file in nginx.conf.sample

Next you'll need to set up beanstalkd, a simple queue that manages the syncing
tasks.  Edit `/etc/default/beanstalkd` and uncomment the line that says
START=yes.  It should look something like this::

  ## Defaults for the beanstalkd init script, /etc/init.d/beanstalkd on
  ## Debian systems. Append ``-b /var/lib/beanstalkd'' for persistent
  ## storage.
  BEANSTALKD_LISTEN_ADDR=0.0.0.0
  BEANSTALKD_LISTEN_PORT=11300
  DAEMON_OPTS="-l $BEANSTALKD_LISTEN_ADDR -p $BEANSTALKD_LISTEN_PORT"

  ## Uncomment to enable startup during boot.
  START=yes

Then start the beanstalk with::

  sudo /etc/init.d/beanstalkd start

Now you should be able to browse to the server, link your flickr and facebook
accounts, and queue up some photo syncing.

To run the workers, use::

  paster runworker development.ini