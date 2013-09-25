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

import rawio
import server

from fwf.util import gen_header_date


class RequestHandler(object):
    """Base web request handler.

    """
    def __init__(self, request):
        self.request = request
        self._headers = {}
        self._write = ""
        self._status_code = 200
        self.set_status(self._status_code)


    def get(self, *args, **kwargs):
        raise HTTPError(405)

    
    def post(self, *args, **kwargs):
        raise HTTPError(405)


    def finish(self, data):
        response = [b"%s" % self._response_line]
        response.extend([b"%s: %s" % (k, v) for k, v in  self._headers.iteritems()])
        response.append("Content-Length: %d" % len(data))
        response.append("")
        response.append(data)

        logging.info("[%s] %d %s %s" %(
                datetime.datetime.now(),
                self._status_code,
                self.request.url,
                self.request_time()))

        self.request.connection.stream.write("\r\n".join(response),
                                             self.request.connection._on_finish)


    def request_time(self):
        return ("%.4f ms" % (self.request.request_time() * 1000.0))


    def _generate_headers(self):
        self._headers["Server"] = b"Fwf web server"
        self._headers["Content-Type"] = b"text/plain"
        self._headers["Date"] = gen_header_date()


    def set_status(self, status_code):
        assert status_code in httplib.responses, "Response code not in responses."
        self._generate_headers()
        self._status_code = status_code
        self._response_line = b"%s %d %s" % (
            self.request.http_version,
            status_code,
            httplib.responses[status_code])



class Context(object):
    def __init__(self, handlers, **settings):
        assert isinstance(handlers, dict), "Handlers must be dict."
        self.settings = settings
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
                h = handler(request)
                getattr(h, request.method.lower())(*args, **kwargs)
            else:
                NotFoundHandler(request).get()
        except HTTPError as ex:
            ErrorHandler(request).get(ex.status_code, ex.log_message or
                                      httplib.responses[status_code])
        except Exception as ex:
            logging.error("Internal server error.", exc_info=ex)
            ErrorHandler(request).get(500, httplib.responses[500])


    def _match_handler(self, request):
        host = request.host.lower().split(":")[0]
        for pattern in self.handlers:
            if pattern.match(request.url):
                return self.handlers[pattern]



class NotFoundHandler(RequestHandler):
    def get(self):
        self.set_status(404)
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
