This file is for you to describe the photosync application. Typically
you would include information such as the information below:

Installation and Setup
======================

Install ``photosync`` using easy_install::

    easy_install photosync

Make a config file as follows::

    paster make-config photosync config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Then you are ready to go.


Setting up an ubuntu development box
====================================

You need to install lots of stuff:

  sudo apt-get install python-dev git-core build-essential libmysqlclient-dev
  sudo apt-get install mysql-server python-pycurl libcurl3 beanstalkd

Now you can check out the repo:

  git clone https://pcardune@github.com/pcardune/photosync.git

Install eazy_install if you don't have it already:

  cd photosync
  sudo python ez_setup.py

Create and activate a virtual environment.

  sudo easy_install virtualenv
  virtualenv env
  source env/bin/activate

Setup the photosync code

  python setup.py develop

Setup an empty DB called photosync

  mysql -u root -p
  > create database photosync;

Run a script to create all the required tables:

  paster setup-app development.ini

Now you can start the server:

  paster serve development.ini