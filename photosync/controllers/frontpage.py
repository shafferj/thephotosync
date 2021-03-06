import logging
import flickrapi

import gdata

from pylons import request, response, session, tmpl_context as c, url
from pylons import app_globals as g
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync.model.meta import Session
from photosync import fb
from photosync import flickr
from photosync import picasa
from photosync.worker.tasks import FullSync
from photosync.model import SyncRecord, AsyncTask, User
from photosync.lazy import lazy

log = logging.getLogger(__name__)

class FrontpageController(BaseController):

    requires_logged_in_user = False

    def home(self):
        c.picasa_connect_url = picasa.get_authorization_url()
        c.flickr_connect_url = flickr.get_authorization_url()
        c.fb_connect_url = fb.get_authorization_url()
        c.fbuser = fb.GraphUser()
        c.picasa_user = None
        if session.get('picasa_token'):
            c.picasa_user = gdata.photos.service.PhotosService()
        c.flickr_user = None
        if session.get('flickr_token'):
            c.flickr_user = flickr.FlickrUser()

        tasks = AsyncTask.get_for_user(limit=2, type=FullSync.get_type()).all()
        c.tasks = tasks
        for task in reversed(tasks):
            if task.is_completed:
                c.last_task = task
            elif task.time_left:
                c.next_task = task
            else:
                c.current_task = task

        return render('/homepage.mako')

    def index(self):
        c.user = self.logged_in_user
        c.fb_connect_url = fb.get_authorization_url()
        c.flickr_connect_url = flickr.get_authorization_url()
        if self.logged_in_user:
            if self.logged_in_user.fb_access_token:
                c.fb_user = fb.GraphUser(
                    id=self.logged_in_user.fb_uid,
                    access_token=self.logged_in_user.fb_access_token)
            if self.logged_in_user.flickr_token:
                c.flickr_user = flickr.FlickrUser(
                    token=self.logged_in_user.flickr_token)
            if self.logged_in_user.flickr_token and self.logged_in_user.fb_access_token:
                c.tasks = AsyncTask.get_for_user(
                    limit=2,
                    type=FullSync.get_type()).all()
                c.sync_url = '/sync/full_sync'
                for task in c.tasks:
                    if task.is_completed:
                        c.last_task = task
                    elif task.time_left:
                        c.next_task = task
                    else:
                        c.current_task = task

            bytes_in, bytes_out = SyncRecord.get_bytes_transfered_by_user(self.logged_in_user.id)
            c.bytes_transferred = bytes_in/1024.**2

            # cost is $0.10 per GB transferred in and
            # $0.15 per GB transferred out
            c.cost = bytes_in/1024.**3 * 0.1 + bytes_out/1024.**3 * 0.15

        if c.tasks:
            return render('/homepage.mako')

        return render('/frontpage.mako')

        if session.get('user_id'):
            return self.home()
        else:
            c.fb_connect_url = fb.get_authorization_url([
                'user_photos',
                'publish_stream',
                'offline_access',
                ])
            # Return a rendered template
            return render('/frontpage.mako')
