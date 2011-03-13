import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync import fb
from photosync.model import User
from photosync.model.meta import Session

log = logging.getLogger(__name__)

class FbauthController(BaseController):

    requires_logged_in_user = False

    def index(self):
        code = request.GET.getone('code')
        nexturl = request.GET.getone('nexturl')
        if nexturl:
            # we are acting only as an auth server.
            # redirect to the server that wants the auth code
            redirect(nexturl+'?code=%s' % code)
            return
        token = fb.get_access_token(code)
        fbuser = fb.GraphUser(access_token=token)

        if session.get('user_id'):
            # a user is already logged in
            user = Session.query(User).filter_by(id=session.get('user_id')).first()
        else:
            # the user is not already logged in, let's see if they have
            # already created an account before
            user = Session.query(User).filter_by(fb_uid=fbuser.id).first()

        if user:
            # the user does have an account, let's update their auth token
            user.fb_uid = fbuser.id
            user.fb_access_token = token
            Session.commit()
        else:
            # the user does not have an account.  We need to create a new one
            # for them.
            user = User(fb_uid=fbuser.id,
                        fb_access_token=token)
            Session.add(user)
            Session.commit()
            user = Session.query(User).filter_by(fb_uid=fbuser.id).first()
            if not user:
                log.error("Failed to create user with fb_uid=%r", fbuser.id)

        if not user:
            log.error("Trying to log in, but couldn't get a user object. "
                      "user=%r code=%r token=%r fbuser=%r",
                      user, code, token, fbuser)

        session['user_id'] = user.id
        session['fb_access_token'] = token
        session.save()
        log.info("Logged in user %s %s: %s",
                 fbuser.first_name,
                 fbuser.last_name,
                 user)
        redirect(url('index'))

