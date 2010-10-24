import json
import logging
import urllib
import urllib2
import urlparse

from pylons import session, request, url, app_globals as g
from pylons import url
from photosync.uri import URI
from photosync.lazy import lazy

log = logging.getLogger(__name__)


def get_graph_url(path, args):
    if 'access_token' in args or 'client_secret' in args:
        protocol = 'https://'
    else:
        protocol = 'http://'

    return ''.join([protocol,
                    g.FB_GRAPH_ENDPOINT,
                    path,
                    '?',
                    urllib.urlencode(args),
                    ])

def get_auth_redirect_url():
    return g.BASE_URL + url('fb_auth_redirect')

def get_authorization_url(scope=[]):
    return get_graph_url('/oauth/authorize',
                         {'client_id':g.FB_APP_ID,
                          'redirect_uri':get_auth_redirect_url(),
                          'scope':','.join(scope)})

def get_access_token(code):
    url = get_graph_url('/oauth/access_token',
                        {'client_id':g.FB_APP_ID,
                         'redirect_uri':get_auth_redirect_url(),
                         'client_secret':g.FB_APP_SECRET,
                         'code':code})
    log.info("Sending request to url %s", url);
    try:
        response = urllib2.urlopen(url)
        return urlparse.parse_qs(response.read())['access_token'][0]
    except urllib2.URLError, e:
        log.error("got url error %r", e);
        return None


class Graph(object):

    def __init__(self, access_token=None, cache=True):
        if not access_token:
            access_token = session.get('fb_access_token')
        self.access_token = access_token
        self.cache = cache
        self._cache = {}

    def get_url(self, path):
        return get_graph_url(path, {'access_token':self.access_token})

    def get(self, path):
        result = self._cache.get(path)

        if not result:
            result = json.loads(urllib2.urlopen(self.get_url(path)).read())
            if self.cache:
                self._cache[path] = result
        return result


class GraphObject(Graph):

    @classmethod
    def from_data(cls, access_token, data):
        instance = cls(access_token)
        instance._cache[instance.path] = data
        return instance

    path = None

    data = property(lambda self: self.get(self.path))

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__)


class GraphUser(GraphObject):

    path = '/me'

    id         = property(lambda self: self.data['id'])
    first_name = property(lambda self: self.data['first_name'])
    last_name  = property(lambda self: self.data['last_name'])

    albums     = lazy(lambda self: GraphAlbums())


class GraphAlbums(GraphObject):

    path = '/me/albums'

    def __len__(self):
        return len(self.data['data'])

    def __iter__(self):
        for data in self.data['data']:
            yield GraphAlbum.from_data(self.access_token, data)


class GraphAlbum(GraphObject):

    id         = property(lambda self: self.data['id'])
    name       = property(lambda self: self.data['name'])
    link       = property(lambda self: self.data['link'])

