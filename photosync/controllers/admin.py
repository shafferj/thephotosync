import os
import logging
import urllib2
import tempfile
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import AdminController, render
from photosync import fb
from photosync import flickr
from photosync.worker import tasks
from photosync.model.meta import Session
from photosync.model import SyncRecord, AsyncTask, User

class AdminController(AdminController):

    def stats(self):
        c.user_count = Session.query(User).count()
        c.sync_count = Session.query(SyncRecord).count()
        c.async_tasks_count = Session.query(AsyncTask).count()
        return render('/admin/stats.mako')

    def index(self):
        return render('/admin/index.mako')
