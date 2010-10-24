import logging
import flickrapi

from pylons import request, response, session, tmpl_context as c, url
from pylons import app_globals as g
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync.model.meta import Session
from photosync import fb
from photosync import flickr

log = logging.getLogger(__name__)

class FrontpageController(BaseController):

    def home(self):
        f = flickr.FlickrAPI()
        c.flickr_connect_url = f.web_login_url(perms='write')
        c.fb_connect_url = fb.get_authorization_url(['user_photos'])
        c.fbuser = fb.GraphUser()
        if f.token:
            c.flickr_user = flickr.FlickrUser()
        return render('/homepage.mako')

    def index(self):
        if session.get('user_id'):
            return self.home()
        else:
            c.fb_connect_url = fb.get_authorization_url(['user_photos'])
            # Return a rendered template
            return render('/frontpage.mako')
