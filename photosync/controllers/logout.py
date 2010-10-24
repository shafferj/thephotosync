import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render

log = logging.getLogger(__name__)

class LogoutController(BaseController):

    def index(self):
        session.clear()
        session.save()
        redirect(url('index'))
