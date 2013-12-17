# coding: utf-8

"""Fwf web framework.

RequestHandler: 请求处理基类.
Context: 所的请求处理类上下文.

"""

import re
import time
import logging
import datetime
import httplib
from traceback import format_exc
import rawio
import server

from fwf.util import gen_header_date
from fwf.template import Template, TemplateLoader


class RequestHandler(object):
    """Base web request handler.

    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self._headers = {}
        self._write = ""
        self._status_code = 200
        self.set_status(self._status_code)
        self.clean_headers()


    def head(self, *args, **kwargs):
        raise HTTPError(405)


    def get(self, *args, **kwargs):
        raise HTTPError(405)


    def post(self, *args, **kwargs):
        raise HTTPError(405)


    def finish(self, content):
        response = [b"%s" % self._response_line]
        response.extend([b"%s: %s" % (k, v) for k, v in  self._headers.iteritems()])
        response.append("Content-Length: %d" % len(content))
        response.append("")
        response.append(content)

        logging.info("[%s] %d %s %s" %(
                datetime.datetime.now(),
                self._status_code,
                self.request.url,
                self.request_time()))

        self.request.connection.stream.write(
            "\r\n".join(response),
            self.request.connection._on_finish)


    def request_time(self):
        return ("%.4f ms" % (self.request.request_time() * 1000.0))


    def set_header(self, name, value):
        self._headers[name] = value


    def clean_headers(self):
        self._headers = {}
        self._headers["Server"] = b"Fwf web server"
        self._headers["Content-Type"] = b"text/plain"
        self._headers["Date"] = gen_header_date()        


    def set_status(self, status_code):
        assert status_code in httplib.responses, "Response code is not in httplib.responses."
        self._status_code = status_code
        self._response_line = b"%s %d %s" % (
            self.request.http_version,
            status_code,
            httplib.responses[status_code])


    def write(self, content):
        self.finish(content)


    def view(self, template_name, **kwargs):
        loader = TemplateLoader(template_name, self.context._template_path)
        html = Template(template_name, loader.read()).generate(**kwargs)
        self.set_header("Content-Type", "text/html")
        self.finish(html)



class Context(object):
    def __init__(self, handlers, **settings):
        assert isinstance(handlers, dict), "Handler must be dict."
        self.settings = settings
        self._template_path = settings.get("template_path", ".")
        self.handlers = self._handle_url(handlers)


    def _handle_url(self, handlers):
        _handlers = {}
        
        for pattern, handle in handlers.iteritems():
            if pattern[-1] != "$":
                pattern += "$"
            _handlers[re.compile(pattern)] = handle

        return _handlers


    def __call__(self, request):
        try:
            args = []
            kwargs = {}
            handler = self._match_handler(request)
            if handler:
                h = handler(self, request)
                getattr(h, request.method.lower())(*args, **kwargs)
            else:
                NotFoundHandler(self, request).get()
        except HTTPError as ex:
            ErrorHandler(self, request).get(ex.status_code, ex.log_message or
                                      httplib.responses[ex.status_code])
        except Exception as ex:
            logging.error("Internal server error.", exc_info=ex)
            ErrorHandler(self, request).get(
                500, "{0} \n {1}".format(
                    httplib.responses[500],
                    self.settings.get("debug") and format_exc(ex) or ""))


    def _match_handler(self, request):
        host = request.host.lower().split(":")[0]
        for pattern in self.handlers:
            if pattern.match(request.url):
                return self.handlers[pattern]



class NotFoundHandler(RequestHandler):
    def get(self):
        raise HTTPError(404, httplib.responses[404])



class ErrorHandler(RequestHandler):
    def get(self, status_code, msg):
        self.set_status(status_code)
        self.finish(msg)



class HTTPError(Exception):
    def __init__(self, status_code, log_message=None):
        self.status_code = status_code
        self.log_message = log_message


    def __str__(self):
        message = "HTTP %d: %s" % (
            self.status_code,
            httplib.responses[self.status_code])
        if self.log_message:
            message += " ( %s )" % self.log_message

        return message
