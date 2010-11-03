import json
import StringIO
import logging
import urllib
import urllib2
import pycurl
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


class File(object):

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path

    __unicode__ = __str__

    def __repr__(self):
        return repr(self.path)


class Graph(object):

    def __init__(self, access_token=None, cache=True):
        if not access_token:
            if 'fb_access_token' in session:
                access_token = session['fb_access_token']
            elif 'user_id' in session:
                user = User.get_current_user()
                if user and user.fb_access_token:
                    session['fb_access_token'] = user.fb_access_token
                    session.save()
                    access_token = user.fb_access_token

        self.access_token = access_token
        self.cache = cache
        self._cache = {}

    def get_url(self, path):
        return get_graph_url(path, {'access_token':self.access_token})

    def get(self, path):
        result = self._cache.get(path)

        if not result:
            log.info("Loading %s", path)
            result = json.loads(urllib2.urlopen(self.get_url(path)).read())
            if self.cache:
                self._cache[path] = result
        return result

    def post(self, path, data):
        log.info("Posting data to %s: %r", path, data)
        response = urllib2.urlopen(self.get_url(path), urllib.urlencode(data))
        result = json.loads(response.read())
        return result

    def post_file(self, path, data):
        log.info("Posting data to %s: %r", path, data)
        c = pycurl.Curl()
        post_fields = []
        for key, value in data.items():
            if isinstance(value, File):
                field = (key, (c.FORM_FILE, value.path))
            else:
                field = (key, value)
            post_fields.append(field)

        c.setopt(c.URL, self.get_url(path))
        c.setopt(c.HTTPPOST, post_fields)
        c.setopt(c.VERBOSE, 1)
        response = StringIO.StringIO()
        c.setopt(c.WRITEFUNCTION, response.write)
        c.perform()
        c.close()
        result = json.loads(response.getvalue())
        return result


class GraphEndpoint(Graph):

    @classmethod
    def from_data(cls, access_token, data):
        instance = cls(access_token)
        instance._cache[instance.path] = data
        instance.path = '/%s' % data['id']
        return instance

    path = None

    data = property(lambda self: self.get(self.path))

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__)


class GraphObject(GraphEndpoint):

    _id = None
    id = property(lambda self: self._id or self.data['id'])

    def __init__(self, id=None, access_token=None, cache=True):
        super(GraphEndpoint, self).__init__(access_token=access_token,
                                            cache=cache)
        if id:
            self._id = id
            self.path = '/%s' % id


class GraphObjectList(GraphEndpoint):

    object_class = None

    def __len__(self):
        return len(self.data['data'])

    def __iter__(self):
        for data in self.data['data']:
            yield self.object_class.from_data(self.access_token, data)

    def __getitem__(self, index):
        return self.object_class.from_data(self.access_token, self.data['data'][index])


class GraphUser(GraphObject):

    path = '/me'

    first_name = property(lambda self: self.data['first_name'])
    last_name  = property(lambda self: self.data['last_name'])

    albums     = lazy(lambda self: GraphAlbums())


class GraphAlbum(GraphObject):

    name       = property(lambda self: self.data['name'])
    link       = property(lambda self: self.data['link'])
    count      = property(lambda self: self.data['count'])

    photos     = lazy(lambda self: GraphPhotos(self.id))


class GraphAlbums(GraphObjectList):

    path = '/me/albums'
    object_class = GraphAlbum

    def add(self, name, description):
        result = self.post(self.path, {'name':name,
                                       'description':description})
        if result.get('id'):
            return GraphAlbum(id=result.get('id'), access_token=self.access_token)
        return None


class GraphPhoto(GraphObject):

    link       = property(lambda self: self.data['link'])
    picture    = property(lambda self: self.data['picture'])


class GraphPhotos(GraphObjectList):

    object_class = GraphPhoto

    def __init__(self, album_id):
        super(GraphPhotos, self).__init__()
        self.path = '/%s/photos' % album_id

    def add(self, filename, message):
        result = self.post_file(self.path, {'source':File(filename),
                                            'message':message})
        if result.get('id'):
            return GraphPhoto(id=result.get('id'), access_token=self.access_token)
        return None
