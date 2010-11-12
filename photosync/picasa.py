import json
import StringIO
import logging
import urllib
import urllib2
import pycurl
import urlparse

import gdata.photos.service
import gdata.media
import gdata.geo


from pylons import session, request, url, app_globals as g
from pylons import url
from photosync.uri import URI
from photosync.lazy import lazy

log = logging.getLogger(__name__)


def get_auth_redirect_url():
    return g.BASE_URL + url('picasa_auth_redirect')

def get_authorization_url(scope=[]):
      next = get_auth_redirect_url() 
      scope = 'http://picasaweb.google.com/data/'
      secure = False
      session = True
      gd_client = gdata.photos.service.PhotosService()
      return gd_client.GenerateAuthSubURL(next, scope, secure, session);

