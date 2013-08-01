# coding: utf-8

"""Socket stream.

处理接入的socket流
TODO: 减少stream处理逻辑.

"""

import socket
import select
import errno
import logging

import rawio


class Stream(object):
    def __init__(self, sock, io=None, max_buffer_size=104857600, read_chunk_size=4096, response_txt=""):
        self.sock = sock
        self._response_txt = response_txt
        self._read_buffer = ""
        self._write_buffer = ""
        self.io = io or rawio.RawIO.instance()
        self.max_buffer_size = max_buffer_size
        self.read_chunk_size = read_chunk_size
        self._read_callback = None
        self._write_callback = None
        self.io.add_handler(self.sock.fileno(), self._handle_events, select.EPOLLERR)


    def _handle_events(self, fd, event):
        if event & select.EPOLLIN:
            self._handle_read()

        elif event & select.EPOLLOUT:
            self._handle_write()

        elif event & select.EPOLLHUP:
            self.close()
            self.remove_handler(fd)

        #state = select.EPOLLERR
        #if self._read_buffer:
        #    self.io.modify_handler(self.sock.fileno(), select.EPOLLIN)


    def write(self, data, callback=None):
        self._write_buffer += data
        self.io.modify_handler(self.sock.fileno(), select.EPOLLOUT)
        self._write_callback = callback


    def _handle_write(self):
        while self._write_buffer:
            try:
                # TODO 处理response写入和是否长连接, 关闭socket.
                num_bytes = self.sock.send(self._write_buffer)
                self._write_buffer = self._write_buffer[num_bytes:]

                if not self._write_buffer and self._write_callback:
                    pass
                    # self.io.remove_handler(self.sock.fileno())
            except socket.error as ex:
                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    break
                else:
                    logging.error("Write error on %d:%d" %
                                  self.sock.fileno(), ex)
                    return

        if self._write_callback:
           self._write_callback() 


    def _handle_read(self):
        # TODO 1. 接收数据大小限制
        # TODO 2. 处理HTTP请求生成response
        try:
            data = self.sock.recv(self.read_chunk_size)
        except socket.error as ex:
            if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                return
            else:
                logging.error("Read error.", exc_info=ex)
                self.close()
                return

        if not data:
            self.close()
            return
        self._read_buffer += data
        self._read_callback(self._read_buffer)
        # self.io.modify_handler(self.sock.fileno(), select.EPOLLOUT)


    def read(self, delimiter, callback):
        assert not self._read_callback, "Already reading."
        loc = self._read_buffer.find(delimiter)
        if loc != -1:
            callback(self._consume(loc + len(delimiter)))
            return
        self._read_callback = callback
        self._read_delimiter = delimiter
        self.io.modify_handler(self.sock.fileno(), select.EPOLLIN)


    def _consume(self, loc):
        result = self._read_buffer[:loc]
        self._read_buffer = self._read_buffer[loc:]
        return result


    def close(self):
        if self.sock is not None:
            self.io.remove_handler(self.sock.fileno())
            self.sock.close()
            self.sock = None



if __name__ == "__main__":
    import functools
    response = [b"HTTP/1.1 200 OK\r\n",
                b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
                b"Content-Type: text/plain\r\n",
                b"Content-Length: 13\r\n\r\n",
                b"Hello, %s!"]
    response = b"".join(response)

    
    def on_read(stream, data):
        print "recv:", data
        try:
            name = None
            lst = data.split()
            name = lst[1][1:]
        except:
            pass

        if not name: name = "Guest"
        on_write_complete = functools.partial(stream.close)
        stream.write(response % name, on_write_complete)


    io = rawio.RawIO.instance()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(("", 8888))
    s.listen(128)

    
    def handle_server(fd, events):
        while True:
            try:
                conn, addr = s.accept()
                conn.setblocking(0)
            except socket.error as ex:
                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise

            try:
                stream = Stream(conn, response_txt=response)
                _on_read = functools.partial(on_read, stream)
                stream.read("\r\n\r\n", _on_read)
            except:
                logging.error("Error in connection.", exc_info=True)


    io.add_handler(s.fileno(), handle_server, select.EPOLLIN)
    io.loop()
