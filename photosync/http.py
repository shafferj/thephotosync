# Implement a scalable http client using pycurl
import time
import json
import pycurl
import urlparse
import urllib
import logging
from cStringIO import StringIO

log = logging.getLogger(__name__)

class File(object):

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path

    __unicode__ = __str__

    def __repr__(self):
        return repr(self.path)


class Request(object):

    def __init__(self, url, method="GET", params=None, headers=None):
        self.url = url
        self.method = method
        self.params = params or {}
        self.headers = headers or {}
        self.response = StringIO()


class Fetcher(object):
    def __init__(self, maxconns=5):
        self._queue = []
        self._curler = pycurl.CurlMulti()
        self._curler.handles = []

        for i in xrange(maxconns):
            c = pycurl.Curl()
            c.fp = None
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.MAXREDIRS, 5)
            c.setopt(pycurl.CONNECTTIMEOUT, 30)
            c.setopt(pycurl.TIMEOUT, 300)
            c.setopt(pycurl.NOSIGNAL, 1)
            self._curler.handles.append(c)

    def queue(self, request):
        self._queue.append(request)
        return self

    def run(self):

        processed = 0
        total = len(self._queue)

        freelist = self._curler.handles[:]
        while processed < total:

            while self._queue and freelist:
                request = self._queue.pop()

                post_fields = []
                for key, value in request.params.items():
                    if isinstance(value, File):
                        request.method = "POST"
                        field = (key, (c.FORM_FILE, value.path))
                    else:
                        field = (key, value)
                    post_fields.append(field)

                c = freelist.pop()
                c.setopt(c.WRITEFUNCTION, request.response.write)
                c.setopt(c.URL, request.url)
                c.setopt(c.VERBOSE, 1)

                if request.method == "POST":
                    c.setopt(c.HTTPPOST, post_fields)
                else:
                    c.setopt(c.URL, request.url+'?'+urllib.urlencode(request.params))

                c.request = request
                self._curler.add_handle(c)

            # run internal curl state machine
            while True:
                ret, num_handles = self._curler.perform()
                if ret != pycurl.E_CALL_MULTI_PERFORM:
                    break

            # Check for curl objects that have terminated
            while True:
                num_q, ok_list, err_list = self._curler.info_read()
                for c in ok_list:
                    processed += 1
                    self._curler.remove_handle(c)
                    freelist.append(c)

                for c, errno, errmsg in err_list:
                    processed += 1
                    self._curler.remove_handle(c)
                    freelist.append(c)

                if num_q == 0:
                    break

            self._curler.select(1.0)


if __name__ == '__main__':
    start = time.time()
    fetcher = Fetcher(30)
    requests = []
    for i in xrange(60, 90):
        request = Request('http://graph.facebook.com/481014%s'%i)
        requests.append(request)
        fetcher.queue(request)
    fetcher.run()


    for request in requests:
        print
        print request.url
        print request.response.getvalue()
    print "finished in", time.time()-start, "seconds"
