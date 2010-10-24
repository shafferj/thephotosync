import urlparse

class URI(object):

#    def __new__(self, uri):
#        if isinstance(uri, URI):
#            return uri

    def __init__(self, uri):
        uri = urlparse.urlparse(uri)
        self.scheme = uri.scheme
        self.path = uri.path
        self.netloc = uri.netloc
        self.params = uri.params
        self.query = uri.query

    def setPath(self, path):
        self.path = path
        return self
