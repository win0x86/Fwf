# coding: utf-8

"""Socket stream.

处理接入的socket流
TODO: 减少stream处理逻辑.

"""

import socket
import select
import errno
import logging

import fwf.rawio


class Stream(object):
    def __init__(self, sock, io=None, max_buffer_size=104857600, read_chunk_size=4096):
        self.sock = sock
        self.sock.setblocking(False)
        self.io = io or fwf.rawio.RawIO.instance()
        self.max_buffer_size = max_buffer_size
        self.read_chunk_size = read_chunk_size
        self._read_buffer = ""
        self._write_buffer = ""
        self._read_delimiter = None
        self._read_callback = None
        self._write_callback = None
        self._state = select.EPOLLERR
        self.io.add_handler(self.sock.fileno(), self._handle_events, self._state)

    def _add_io_state(self, state):
        if not self._state & state:
            self._state = self._state | state
            self.io.modify_handler(self.sock.fileno(), self._state)


    def _handle_events(self, fd, event):
        if event & select.EPOLLIN:
            self._handle_read()

        if event & select.EPOLLOUT:
            self._handle_write()

        if event & select.EPOLLERR:
            self.close()
            return

        if not self.sock: return
        
        state = select.EPOLLERR
        if self._read_delimiter:
            state |= select.EPOLLIN
        if self._write_buffer:
            state |= select.EPOLLOUT
        if state != self._state:
            self._state = state
            self.io.modify_handler(self.sock.fileno(), self._state)


    def _handle_write(self):
        while self._write_buffer:
            try:
                num_bytes = self.sock.send(self._write_buffer)
                self._write_buffer = self._write_buffer[num_bytes:]
            except socket.error as ex:
                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                    break
                else:
                    logging.error("Write error on %d:%d" %
                                  self.sock.fileno(), ex)
                    return
                
        if not self._write_buffer and self._write_callback:
            self._write_callback()
            self._write_callback = None


    def write(self, data, callback=None):
        self._write_buffer += data
        self._add_io_state(select.EPOLLOUT)
        self._write_callback = callback


    def _handle_read(self):
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
        if len(self._read_buffer) > self.max_buffer_size:
            logging.error("Reached maximum read buffer size")
            self.close()
            return

        loc = self._read_buffer.find(self._read_delimiter)
        if loc != -1:
            delimiter_len = len(self._read_delimiter)
            self._read_callback(self._consume(loc + delimiter_len))
            self._read_callback = None
            

    def read(self, delimiter, callback):
        assert not self._read_callback, "Already reading."
        loc = self._read_buffer.find(delimiter)
        if loc != -1:
            callback(self._consume(loc + len(delimiter)))
            return
        self._read_callback = callback
        self._read_delimiter = delimiter
        self._add_io_state(select.EPOLLIN)


    def _consume(self, loc):
        result = self._read_buffer[:loc]
        self._read_buffer = self._read_buffer[loc:]
        return result


    def close(self):
        if self.sock is not None:
            self.io.remove_handler(self.sock.fileno())
            self.sock.close()
            self.sock = None
