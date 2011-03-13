"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons import app_globals as g
from pylons.controllers.util import abort, redirect
from pylons import url

from webob.exc import HTTPException, HTTPNotFound

from photosync.lazy import lazy
from photosync.model import User
from photosync.model.meta import Session

class BaseController(WSGIController):

    requires_logged_in_user = True


    @lazy
    def logged_in_user(self):
        return User.get_current_user()

    def __before__(self):
        if self.requires_logged_in_user and not self.logged_in_user:
            redirect(url('index'))

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            Session.remove()


class AdminController(BaseController):

    def __before__(self):
        admins = g.ADMIN_FB_UIDS.split()
        if str(self.logged_in_user.fb_uid) not in admins:
            raise HTTPNotFound()
