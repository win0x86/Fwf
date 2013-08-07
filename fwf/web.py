# coding: utf-8

"""Fwf web framework.

RequestHandler: 请求处理基类.
Context: 所的请求处理类上下文.

"""

import time
import logging
import datetime
import httplib

import rawio
import server


gen_date = lambda: time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())


class RequestHandler(object):
    """Base web request handler.

    """
    def __init__(self, request):
        self.request = request
        self._headers = {}
        self.set_back(200)


    def get(self, *args, **kwargs):
        raise NotImplementedError()


    def finish(self, data):
        response = [b"%s" % self._response_line]
        response.extend([b"%s: %s" % (k, v) for k, v in  self._headers.iteritems()])
        response.append("Content-Length: %d" % len(data))
        response.append("")
        response.append(data)

        logging.info("[%s] %s %s" %
                     (datetime.datetime.now(),
                      self.request.url, self.request_time()))

        self.request.connection.stream.write("\r\n".join(response),
                                             self.request.connection._on_finish)


    def request_time(self):
        return ("%.4f ms" % (self.request.request_time() * 1000.0))


    def _generate_headers(self):
        self._headers["Server"] = b"Fwf web server"
        self._headers["Content-Type"] = b"text/plain"
        self._headers["Date"] = gen_date()


    def set_back(self, state_code):
        self._generate_headers()
        assert state_code in httplib.responses, "Response code not in responses."
        self._response_line = b"%s %d %s" % (self.request.http_version,
                                            state_code,
                                            httplib.responses[state_code])



class AsyncRequestHandler(object):
    """Asynchronous Request Handler.

    Use yield to implement coroutine.
    
    """
    pass



class Context(object):
    def __init__(self, handlers):
        self._handlers = handlers


    def __call__(self, request):
        try:
            response = self._handlers.get(request.url)
            if response:
                handle = response(request)
                getattr(handle, request.method.lower())()
            else:
                NotFoundHandler(request).get()
        except Exception as ex:
            logging.error("Internal server error.", exc_info=True)
            ErrorHandler(request).get()



class NotFoundHandler(RequestHandler):
    def get(self):
        self.set_back(404)
        self.finish(httplib.responses[404])



class ErrorHandler(RequestHandler):
    def get(self):
        self.set_back(500)
        self.finish(httplib.responses[500])
