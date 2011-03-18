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

def utf8(val):
    return unicode(val).encode('utf-8')

def get_graph_url(path, args=None):
    args = args or {}
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
    auth_server = getattr(g, 'FB_AUTH_SERVER', None)
    if auth_server:
        return u'%s/fb/auth_redirect?nexturl=%s/fb/auth_redirect' % (
            auth_server, g.BASE_URL)
    else:
        return u'%s/fb/auth_redirect' % g.BASE_URL

def get_authorization_url(scope=['user_photos',
                                 'publish_stream',
                                 'offline_access',]):
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
    log.debug("Sending request to url %s", url);
    try:
        response = urllib2.urlopen(url)
        return urlparse.parse_qs(response.read())['access_token'][0]
    except urllib2.URLError, e:
        log.error("Failed to get access token for code %r: %s", code, e.read())
        return None


def get_privacy_options():
    return (
        ('FB_DEFAULT','My default setting on Facbeook'),
        ('EVERYONE','Everyone'),
        ('ALL_FRIENDS','Friends Only'),
        ('NETWORKS_FRIENDS','Friends and Networks'),
        ('FRIENDS_OF_FRIENDS','Friends of Friends'),
        ('ONLY_ME','Only Me'))

def get_privacy_api_value(privacy):
    if privacy == 'ONLY_ME':
        return {'value':'CUSTOM',
                'friends':'SELF'}
    elif privacy in ('FB_DEFAULT', None):
        return None

    return {'value':privacy}


class File(object):

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path

    __unicode__ = __str__

    def __repr__(self):
        return repr(self.path)

class GraphException(Exception):
    pass

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

        if not access_token:
            raise GraphException("Failed to get access token and none provided")
        self.access_token = access_token
        self.cache = cache
        self._cache = {}

    def get_url(self, path):
        return get_graph_url(path, {'access_token':self.access_token})

    def get(self, path):
        result = self._cache.get(path)

        if not result:
            log.debug("Loading %s", path)
            try:
                result = json.loads(urllib2.urlopen(self.get_url(path)).read())
            except urllib2.HTTPError, e:
                log.warn("Failed to load %s: %s", self.get_url(path), e.read())
                result = None
            else:
                if self.cache:
                    self._cache[path] = result
        return result

    def post(self, path, data):
        log.debug("Posting data to %s: %r", path, data)
        try:
            response = urllib2.urlopen(self.get_url(path), urllib.urlencode(data))
        except urllib2.HTTPError, e:
            log.error("Failed to load %s: %s", self.get_url(path), e.read())
            return None
        return json.loads(response.read())

    def post_file(self, path, data):
        log.debug("Posting data to %s: %r", path, data)
        c = pycurl.Curl()
        post_fields = []
        for key, value in data.items():
            if isinstance(value, File):
                field = (key, (c.FORM_FILE, value.path))
            else:
                try:
                    field = (key, utf8(value))
                except Exception, e:
                    log.error("Could not convert %s to ascii", value)
                    log.exception(e)
            post_fields.append(field)

        try:
            c.setopt(c.URL, self.get_url(utf8(path)))
        except TypeError, e:
            log.error("Invalid url %s for pycurl url option", self.get_url(path))
            raise
        c.setopt(c.HTTPPOST, post_fields)
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
        return '<%s %s %r>' % (self.__class__.__name__,
                               self.path,
                               self._cache.get(self.path))


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
    name  = property(lambda self: self.data['name'])
    link  = property(lambda self: self.data['link'])
    profile_pic_url = property(lambda self: get_graph_url('/%s/picture' % self.id))

    albums     = lazy(lambda self: GraphAlbums(access_token=self.access_token))


class GraphAlbum(GraphObject):

    name       = property(lambda self: self.data['name'])
    link       = property(lambda self: self.data['link'])
    count      = property(lambda self: self.data['count'])

    photos     = lazy(lambda self: GraphPhotos(self.id, access_token=self.access_token))


class GraphAlbums(GraphObjectList):

    path = '/me/albums'
    object_class = GraphAlbum

    def add(self, name, description, privacy=None):
        params = {'name':name,
                  'description':description}
        privacy = get_privacy_api_value(privacy)
        if privacy:
            params['privacy'] = json.dumps(privacy)
        result = self.post(self.path, params)
        if result and result.get('id'):
            return GraphAlbum(id=result.get('id'), access_token=self.access_token)
        return None


class GraphPhoto(GraphObject):

    link       = property(lambda self: self.data['link'])
    picture    = property(lambda self: self.data['picture'])


class GraphPhotos(GraphObjectList):

    object_class = GraphPhoto

    def __init__(self, album_id, access_token=None):
        super(GraphPhotos, self).__init__(access_token=access_token)
        self.path = '/%s/photos' % album_id

    def add(self, filename, message):
        result = self.post_file(self.path, {'source':File(filename),
                                            'message':message})
        if result.get('id'):
            return GraphPhoto(id=result.get('id'), access_token=self.access_token)
        return None
