# coding: utf-8

"""Fwf web framework.

RequestHandler: 请求处理基类.
Context: 所的请求处理类上下文.

"""

import rawio
import server


class RequestHandler(object):
    """Base web request handler.

    
    """

    def __init__(self, request):
        self.request = request


    def __call__(self, *args, **kwargs):
        # TEST
        self.finish()


    def finish(self):
        response = [b"HTTP/1.1 200 OK\r\n",
                    b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
                    b"Content-Type: text/plain\r\n",
                    b"Content-Length: 13\r\n\r\n",
                    b"Hello, %s!"]
        response = b"".join(response)
        self.request.connection.stream.write(response % "Guest",
                                             self.request.connection._on_finish)



class Context(object):
    def __init__(self):
        pass


    def __call__(self, request):
        response = RequestHandler(request)
        response()



if __name__ == "__main__":
    s = server.HTTPServer(Context())
    s.bind()
    rawio.RawIO.instance().loop()
