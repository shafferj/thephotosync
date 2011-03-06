import flickrapi
import urllib
from pylons import session, app_globals as g

from photosync.lazy import lazy
from photosync.model import User

class FlickrAPI(flickrapi.FlickrAPI):

    def __init__(self, token=None):
        if not token:
            if 'flickr_token' in session:
                token = session.get('flickr_token')
            elif 'user_id' in session:
                user = User.get_current_user()
                if user and user.flickr_token:
                    session['flickr_token'] = user.flickr_token
                    session.save()
                    token = user.flickr_token

        super(FlickrAPI, self).__init__(g.FLICKR_API_KEY,
                                        g.FLICKR_API_SECRET,
                                        token=token,
                                        store_token=False)


class FlickrUser(FlickrAPI):

    @lazy
    def _checkToken(self):
        return self.auth_checkToken()[0]

    @lazy
    def _info(self):
        return self.people_getInfo(user_id=self.nsid)[0]

    username = lazy(lambda self: self._checkToken[2].get('username'))
    name = property(lambda self: self._checkToken[2].get('fullname'))
    nsid = lazy(lambda self: self._checkToken[2].get('nsid'))
    link = property(lambda self: self._info.find('profileurl').text)

    @lazy
    def profile_pic_url(self):
        iconserver = self._info.get('iconserver')
        if iconserver != '0':
            return 'http://farm%s.static.flickr.com/%s/buddyicons/%s.jpg' % (
                self._info.get('iconfarm'), iconserver, self.nsid)
        return 'http://www.flickr.com/images/buddyicon.jpg'

def get_authorization_url(perms=''):
    return FlickrAPI().web_login_url(perms=perms)


def get_url(token, **params):
    fk = FlickrAPI(token)
    params.setdefault('auth_token', fk.token_cache.token)
    params.setdefault('api_key', fk.api_key)
    params.setdefault('format', 'json')
    params.setdefault('nojsoncallback', '1')
    return "http://" + fk.flickr_host + fk.flickr_rest_form + '?' + fk.encode_and_sign(params)
