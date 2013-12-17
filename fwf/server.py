# coding: utf-8

"""A HTTP server.

"""

import time
import select
import socket
import errno
import logging
import urlparse

import fwf.rawio
import fwf.stream


class HTTPServer(object):
    def __init__(self, request_callback, io=None):
        self.io = io or fwf.rawio.RawIO.instance()
        self.request_callback = request_callback


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
            except socket.error as ex:
                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise

            try:
                stream = fwf.stream.Stream(conn, io=self.io)
                HTTPConnection(stream, self.request_callback, remote_ip=addr[0])
            except:
                logging.error("Error in connection.", exc_info=True)



class HTTPConnection(object):
    def __init__(self, stream, request_callback, remote_ip, keep_alive=False):
        self.stream = stream
        self.request_callback = request_callback
        self._keep_alive = False
        self._remote_ip = remote_ip
        self._keep_alive = keep_alive
        self._request = None
        self.stream.read("\r\n\r\n", self._on_headers)
        

    def _on_headers(self, data):
        request_line = data[:data.find("\r\n")]
        method, url, http_version = request_line.split()
        if not http_version.startswith("HTTP/"):
            raise Exception("Not HTTP protocol.")
        headers = HTTPHeaders.parse(data[data.find("\r\n"):])
        self._keep_alive = headers.get("Connection") == "keep-alive"
        self._request = HTTPRequest(self.stream,
                                    method,
                                    url=url,
                                    headers=headers,
                                    http_version=http_version,
                                    remote_ip=self._remote_ip,
                                    connection=self)

        content_length = headers.get("Content-Length")
        if content_length:
            content_length = int(content_length)
            if content_length > self.stream.max_buffer_size:
                raise Exception("Content-Length too long.")
            self.stream.read(content_length, self._on_request_body)

        self.request_callback(self._request)


    def _on_request_body(self, data):
        self._request.body = data


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



class HTTPRequest(object):
    def __init__(self, stream, method, url, headers, http_version, remote_ip, protocol=None, files=None, connection=None):
        self.stream = stream
        self.method = method
        self.url = url
        self.http_version = http_version
        self.remote_ip = remote_ip
        self.protocol = protocol or "http"
        self.headers = headers or HTTPHeaders()
        self.host = self.headers.get("Host") or "127.0.0.1"
        self.files = files or {}
        self.connection = connection

        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        self.path = path
        self.query =query
        self.params = {}
        self._start_time = time.time()


    def request_time(self):
        return time.time() - self._start_time



class HTTPResponse(object):
    def __init__(self, url):
        pass
