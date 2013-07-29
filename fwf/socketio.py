# coding: utf-8

"""Socket IO.

Use linux/epoll(level-triggered), only support linux.

###!!!Warning!!!###
Copy from tornado.

"""

import time
import select
import socket
import logging


class IO(object):
    def __init__(self):
        self._epoll = select.epoll()
        self._handlers = {}
        self._events = {}


    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()

        return cls._instance


    def loop(self, poll_timeout=0.1):
        while True:
            try:
                events = self._epoll.poll(poll_timeout)
            except Exception as ex:
                logging.error("IO Error.", exc_info=ex)

            self._events.update(events)
            
            while self._events:
                fd, event = self._events.popitem()

                try:
                    import pdb; pdb.set_trace()
                    self._handlers[fd](fd, event)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except (OSError, IOError) as ex:
                    logging.error("IO Error", exc_info=ex)
                except Exception as ex:
                    logging.error("IO Error", exc_info=ex)
            

    def add_handler(self, fd, handler, events):
        self._handlers[fd] = handler
        self._epoll.register(fd, events | select.EPOLLERR)
        


if __name__ == "__main__":
    import functools, errno
    io = IO.instance()

    def callback(sock, fd, events):
        while True:
            try:
                conn, addr = sock.accept()
            except socket.error as ex:
                if ex[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                    raise
                print "[Main error]:", ex
                return
            conn.setblocking(0)
            handle_connection(sock, conn, addr, fd, events)
            

    def handle_connection(sock, conn, addr, fd, events, read_chunk_size=4096):
        # TODO handle epoll event.
        if not sock:
            logging.error("No sock, fd: %s" % fd)
            return

        if events & select.EPOLLIN:
            # read
            pass


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(("", 8888))
    s.listen(128)
    
    cb = functools.partial(callback, s)
    io.add_handler(s.fileno(), cb, select.EPOLLIN)
    io.loop()
