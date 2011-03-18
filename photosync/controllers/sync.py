import os
import logging
import urllib2
import tempfile
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync import fb
from photosync import flickr
from photosync.worker import tasks
from photosync.model.meta import Session
from photosync.model import SyncRecord, AsyncTask

log = logging.getLogger(__name__)


class SyncController(BaseController):

    def long_ping(self):
        tasks.LongPing.submit(int(request.GET.getone('seconds')))
        redirect(url('index'))

    def full_sync(self):
        tasks.FullSync.run_for_user_now(self.logged_in_user.id)
        redirect(url('index'))

    def status(self):
        last = AsyncTask.get_for_user(type=tasks.FullSync.get_type(),
                                      limit=1).first()

        data = None
        if last:
            if last.time_left:
                data = None
            else:
                data = dict((attr, getattr(last, attr))
                            for attr in
                            ('total_units','completed_units','status_data'))

        return json.dumps(data)
