import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync import fb
from photosync.model import User
from photosync.model.meta import Session
log = logging.getLogger(__name__)

class FbauthController(BaseController):

    def index(self):
        code = request.GET.getone('code')
        token = fb.get_access_token(code)
        fbuser = fb.GraphUser(token)

        user = Session.query(User).filter_by(fb_uid=fbuser.id).first()
        if not user:
            user = User(fbuser.id)
            Session.add(user)
            Session.commit()
            user = Session.query(User).filter_by(fb_uid=fbuser.id).first()

        session['logged_in'] = user.id
        session['user_id'] = user.id
        session['fb_access_token'] = token
        session.save()
        log.info("Logged in user %s %s: %s",
                 fbuser.first_name,
                 fbuser.last_name,
                 user)
        redirect(url('index'))

