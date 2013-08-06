# coding: utf-8

"""Fwf web framework.

RequestHandler: 请求处理基类.
Context: 所的请求处理类上下文.

"""

import time
import logging
import datetime

import rawio
import server


class RequestHandler(object):
    """Base web request handler.

    """
    def __init__(self, request):
        self.request = request


    def get(self, *args, **kwargs):
        raise NotImplementedError()


    def finish(self, data):
        logging.info("[%s] %s %s" %
                     (datetime.datetime.now(),
                      self.request.url, self.request_time()))
        self.request.connection.stream.write(data,
                                             self.request.connection._on_finish)


    def request_time(self):
        return ("%.4f ms" % (self.request.request_time() * 1000.0))



class Context(object):
    def __init__(self, handlers):
        self._handlers = handlers


    def __call__(self, request):
        response = self._handlers.get(request.url)
        if response:
            handle = response(request)
            getattr(handle, request.method.lower())()
        else:
            raise Exception("Not found.")
