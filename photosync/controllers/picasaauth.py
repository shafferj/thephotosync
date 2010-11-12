import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync.model.meta import Session
from photosync.model import User
 
import cgi

import gdata.photos.service
import gdata.media
import gdata.geo


log = logging.getLogger(__name__)

class PicasaauthController(BaseController):

    def index(self):
	gd_client = gdata.photos.service.PhotosService()
	#token = request.GET.getone('token')
	parameters = cgi.FieldStorage()
	token = parameters['token']
	gd_client.auth_token = token
	gd_client.UpgradeToSessionToken()

        session['picasa_token'] = token
        session.save()

        if session.get('user_id'):
            # a user is already logged in
            user = Session.query(User).filter_by(id=session.get('user_id')).first()
        else:
            # the user is not already logged in, let's see if they have
            # already created an account before
            user = Session.query(User).filter_by(picasa_token=token).first()

        if user:
            user.picasa_token = token
            Session.commit()
        else:
            # the user does not have an account.  We need to create a new one
            # for them.
            user = User(picasa_token=token)
            Session.add(user)
            Session.commit()
            user = Session.query(User).filter_by(picasa_token=picasa_token).first()

        session['user_id'] = user.id
        session['picasa_token'] = token
        session.save()
        log.info("Logged in user %s", user)
        redirect(url('index'))

