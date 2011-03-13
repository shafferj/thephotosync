import cgi

from paste.urlparser import PkgResourcesParser
from pylons import tmpl_context as c
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from photosync.lib.base import BaseController, render

class ErrorController(BaseController):
    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """
    def document(self):
        """Render the error document"""

        request = self._py_object.request
        resp = request.environ.get('pylons.original_response')
        c.error_code = cgi.escape(request.GET.get('code', str(resp.status_int)))
        c.error_message = literal(resp.body) or cgi.escape(request.GET.get('message', ''))

        return render('/error.mako')

        request = self._py_object.request
        resp = request.environ.get('pylons.original_response')
        content = literal(resp.body) or cgi.escape(request.GET.get('message', ''))
        c.error_code = cgi.escape(request.GET.get('code', str(resp.status_int)))
        c.error_message = content
        page = error_document_template % \
            dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                 code=cgi.escape(request.GET.get('code', str(resp.status_int))),
                 message=content)
        return page
