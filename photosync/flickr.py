import flickrapi
from pylons import session, app_globals as g

from photosync.lazy import lazy

class FlickrAPI(flickrapi.FlickrAPI):

    def __init__(self, token=None):
        if not token:
            token = session.get('flickr_token')
        super(FlickrAPI, self).__init__(g.FLICKR_API_KEY,
                                        g.FLICKR_API_SECRET,
                                        token=token,
                                        store_token=False)


class FlickrUser(FlickrAPI):

    @lazy
    def _checkToken(self):
        return self.auth_checkToken()

    username = lazy(lambda self: self._checkToken[0][2].get('username'))
    nsid = lazy(lambda self: self._checkToken[0][2].get('nsid'))
