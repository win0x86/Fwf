#!/usr/bin/env python
# coding: utf-8

"""Fwf IO(socket io loop).

Use linux/epoll(level-triggered), only support linux.


"""

import time
import select
import socket
import errno
import logging


class RawIO(object):
    def __init__(self, response=b""):
        self._epoll = select.epoll()
        self._handlers = {}
        self._listen_fds = {}
        self._requests = {} # 请求内容
        self._responses = {} # 响应的内容
        self._response_txt = response


    @classmethod
    def instance(cls, response):
        if not hasattr(cls, "_instance"):
            cls._instance = cls(response)

        return cls._instance


    def loop(self, poll_timeout=0.1):
        while True:
            events = []
            try:
                events = self._epoll.poll(poll_timeout)
            except Exception as ex:
                logging.error("IO Error.", exc_info=ex)

            for fd, event in events:
                try:
                    if fd in self._listen_fds:
                        conn, addr = self._listen_fds[fd].accept()
                        conn.setblocking(0)
                        self.add_handler(conn.fileno(), conn, select.EPOLLIN)
                        self._handlers[conn.fileno()] = conn
                        self._requests[conn.fileno()] = b""
                        self._responses[conn.fileno()] = self._response_txt

                    elif event & select.EPOLLIN:
                        while True:
                            # TODO 1. 接收数据大小限制
                            # TODO 2. 处理HTTP请求生成response
                            try:
                                data = self._handlers[fd].recv(1024)
                                self._requests[fd] += data
                                if not data: break
                            except socket.error as ex:
                                if ex.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                                    break
                                else:
                                    logging.error("Read error.", exc_info=ex)
                                    
                        self.modify_handler(fd, select.EPOLLOUT)

                    elif event & select.EPOLLOUT:
                        # TODO 处理response写入和是否长连接, 关闭socket.
                        num_bytes = self._handlers[fd].send(
                            self._responses[fd])
                        self._responses[fd] = self._responses[fd][num_bytes:]

                        if not self._responses[fd]:
                            self._handlers[fd].shutdown(socket.SHUT_RDWR)
                            self.remove_handler(fd)

                    elif event & select.EPOLLHUP:
                        self._handlers[fd].close()
                        self.remove_handler(fd)

                except (KeyboardInterrupt, SystemExit):
                    logging.info("Exit.")
                except (OSError, IOError) as ex:
                    logging.error("IO Error.", exc_info=ex)
                except Exception as ex:
                    logging.error("IO Error.", exc_info=ex)


    def add_handler(self, fd, handler, events):
        self._handlers[fd] = handler
        self._epoll.register(fd, events | select.EPOLLERR)


    def modify_handler(self, fd, events):
        self._epoll.modify(fd, events | select.EPOLLERR)


    def remove_handler(self, fd):
        self._handlers.pop(fd, None)

        try:
            self._epoll.unregister(fd)
        except (OSError, IOError):
            logging.error("Error removing fd from epoll", exc_info=True)


    def add_listen_fd(self, sock):
        if sock.fileno() not in self._listen_fds:
            self._listen_fds[sock.fileno()] = sock



if __name__ == "__main__":
    # Run web server like this:
    #
    # $ python rawio.py
    #
    
    response = [b"HTTP/1.1 200 OK\r\n",
            b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
            b"Content-Type: text/plain\r\n",
            b"Content-Length: 13\r\n\r\n",
            b"Hello, world!"]

    response = b"".join(response)
    io = RawIO.instance(response=response)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(("", 8888))
    s.listen(128)
    io.add_listen_fd(s)

    io.add_handler(s.fileno(), s, select.EPOLLIN)
    io.loop()
