# coding: utf-8

"""A HTTP server.

"""


class HTTPServer(object):
    def __init__(self, port, address="", listen=128):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(0)
        self._socket.listen(listen)


    def bind(self, port, address=""):
        self._socket.bind((address, port))
