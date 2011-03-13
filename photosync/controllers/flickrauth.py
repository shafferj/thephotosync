import logging

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from photosync.lib.base import BaseController, render
from photosync.flickr import FlickrAPI
from photosync.model.meta import Session
from photosync.model import User

log = logging.getLogger(__name__)

class FlickrauthController(BaseController):

    def index(self):
        flickr = FlickrAPI()
        token = flickr.get_token(request.GET.getone('frob'))

        session['flickr_token'] = token
        session.save()

        flickr = FlickrAPI(token)
        result = flickr.auth_checkToken()
        nsid = result[0][2].get('nsid')

        if session.get('user_id'):
            # a user is already logged in
            user = Session.query(User).filter_by(id=session.get('user_id')).first()
        else:
            # the user is not already logged in, let's see if they have
            # already created an account before
            user = Session.query(User).filter_by(flickr_nsid=nsid).first()

        if user:
            user.flickr_nsid = nsid
            user.flickr_token = token
            Session.commit()
        else:
            # the user does not have an account.  We need to create a new one
            # for them.
            user = User(flickr_nsid=nsid, flickr_token=token)
            Session.add(user)
            Session.commit()
            user = Session.query(User).filter_by(flickr_nsid=nsid).first()

        session['user_id'] = user.id
        session['flickr_token'] = token
        session.save()
        log.info("Logged in user %s", user)
        redirect(url('index'))
