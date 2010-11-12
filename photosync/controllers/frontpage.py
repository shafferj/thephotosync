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
from photosync.model import SyncRecord, AsyncTask

log = logging.getLogger(__name__)

class FrontpageController(BaseController):

    def home(self):
	c.picasa_connect_url = picasa.get_authorization_url()
        c.flickr_connect_url = flickr.get_authorization_url('write')
        c.fb_connect_url = fb.get_authorization_url([
                'user_photos',
                'publish_stream',
                'offline_access',
                ])
        c.fbuser = fb.GraphUser()
	c.picasa_user = None
	if session.get('picasa_token'):
	    c.picasa_user = gdata.photos.service.PhotosService() 
        c.flickr_user = None
        if session.get('flickr_token'):
            c.flickr_user = flickr.FlickrUser()

        c.tasks = AsyncTask.get_for_user()

        return render('/homepage.mako')

    def index(self):
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
