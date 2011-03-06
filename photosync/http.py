# Implement a scalable http client using pycurl
import re
import time
import json
import pycurl
import urlparse
import urllib
import logging
from cStringIO import StringIO

from photosync.lazy import lazy

log = logging.getLogger(__name__)

class File(object):

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return self.path

    __unicode__ = __str__

    def __repr__(self):
        return repr(self.path)

HEADERS_RE = re.compile(r"(?P<name>.*?): (?P<value>.*?)\r\n")

class Request(object):

    def __init__(self,
                 url,
                 method="GET",
                 params=None,
                 headers=None,
                 filename=None,
                 verbose=False):
        self.url = str(url)
        self.method = method
        self.params = params or {}
        self.headers = headers or {}
        self.filename = filename
        self.verbose = verbose

    @lazy
    def response(self):
        if self.filename:
            return open(self.filename, 'w')
        else:
            return StringIO()

    @lazy
    def response_headers(self):
        return StringIO()

    def read_headers(self):
        return dict(HEADERS_RE.findall(self.response_headers.getvalue()))

    def read_response(self):
        if self.filename:
            self.response.close()
            f = open(self.filename, 'r')
            result = f.read()
            f.close()
            return result
        else:
            return self.response.getvalue()


class JsonRequest(Request):

    def read_response(self):
        return json.loads(super(JsonRequest, self).read_response())


class Fetcher(object):
    def __init__(self, maxconns=5, progress_callback=None):
        self._requests = []
        self._queue = []
        self._curler = pycurl.CurlMulti()
        self._curler.handles = []
        self.progress_callback = progress_callback

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
        if request:
            self._queue.append(request)
        self._requests.append(request)
        return self

    def __iter__(self):
        for request in self._requests:
            yield request

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
                c.setopt(c.HEADERFUNCTION, request.response_headers.write)
                c.setopt(c.URL, str(request.url))
                c.setopt(c.VERBOSE, 1 if request.verbose else 0)
                if request.method == "HEAD":
                    c.setopt(c.NOBODY, 1)

                if request.method == "POST":
                    c.setopt(c.HTTPPOST, post_fields)
                else:
                    url = request.url
                    if request.params:
                        url += '?'+urllib.urlencode(request.params)
                    c.setopt(c.URL, url)

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
                if (err_list or ok_list) and self.progress_callback:
                    self.progress_callback(processed, total)
                if num_q == 0:
                    break

            self._curler.select(1.0)
        return self


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
        print request.read_response()
    print "finished in", time.time()-start, "seconds"
