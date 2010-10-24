import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync.model.meta import Session
from photosync import fb

log = logging.getLogger(__name__)

class FrontpageController(BaseController):

    def index(self):
        if 'fb_access_token' in session:
            c.fbuser = fb.GraphUser()
            return render('/homepage.mako')
        else:
            c.fb_connect_url = fb.get_authorization_url(['user_photos'])
            # Return a rendered template
            return render('/frontpage.mako')
