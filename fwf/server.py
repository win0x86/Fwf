# coding: utf-8

"""A HTTP server.

"""

import select
import socket
import errno
import logging

import rawio
import stream


class HTTPServer(object):
    def __init__(self, io=None):
        self.io = io or rawio.RawIO.instance()


    def bind(self, port=8888, address="", listen=128):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(0)
        self._socket.bind((address, port))
        self._socket.listen(listen)
        self.io.add_handler(self._socket.fileno(), self._handle_events, select.EPOLLIN)


    def _handle_events(self, fd, events):
        while True:
            try:
                conn, addr = self._socket.accept()
                conn.setblocking(0)
            except socket.error as ex:
                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise

            try:
                _stream = stream.Stream(conn, io=self.io)
                HTTPConnection(_stream)
            except:
                logging.error("Error in connection.", exc_info=True)



class HTTPConnection(object):
    def __init__(self, _stream):
        self.stream = _stream
        self._keep_alive = False
        self.stream.read("\r\n\r\n", self._on_headers)
        

    def _on_headers(self, data):
        # TODO Remove this.
        response = [b"HTTP/1.1 200 OK\r\n",
                    b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
                    b"Content-Type: text/plain\r\n",
                    b"Content-Length: 13\r\n\r\n",
                    b"Hello, %s!"]
        response = b"".join(response)
        request_line = data[:data.find("\r\n")]
        headers = HTTPHeaders.parse(data[data.find("\r\n"):])
        self._keep_alive = headers.get("Connection") == "keep-alive"
        
        self.stream.write(response % "Guest", self._on_finish)


    def _on_finish(self):
        if not self._keep_alive:
            self.stream.close()
        else:
            self.stream.read("\r\n\r\n", self._on_headers)



class HTTPHeaders(dict):
    @classmethod
    def parse(cls, headers):
        h = cls()
        for line in headers.splitlines():
            if line: h.parse_line(line)

        return h


    def parse_line(self, line):
        name, value = line.split(":", 1)
        self.add(name, value.strip())


    def add(self, name, value):
        self[name] = value
        


if __name__ == "__main__":
    server = HTTPServer()
    server.bind()
    rawio.RawIO.instance().loop()
