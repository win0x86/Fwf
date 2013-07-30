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
                    self._handlers[fd](fd, event)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except (OSError, IOError) as ex:
                    logging.error("IO Error.", exc_info=ex)
                except Exception as ex:
                    logging.error("IO Error.", exc_info=ex)


    def add_handler(self, fd, handler, events):
        self._handlers[fd] = handler
        self._epoll.register(fd, events | select.EPOLLERR)


    def modify_handler(self, fd, handler, events):
        self._epoll.modify(fd, events | select.EPOLLERR)


    def remove_handler(self, fd):
        self._handlers.pop(fd, None)

        try:
            self._epoll.unregister(fd)
        except (OSError, IOError):
            logging.error("Error removing fd from epoll", exc_info=True)



if __name__ == "__main__":
    import functools, errno
    io = IO.instance()
    response = [b"HTTP/1.1 200 OK\r\n",
            b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
            b"Content-Type: text/plain\r\n",
            b"Content-Length: 13\r\n\r\n",
            b"Hello, world!"]

    response = "".join(response)
    sockets = {}


    def callback(sock, fd, events):
        while True:
            try:
                print "accept, sockets:", sockets
                conn, addr = sock.accept()
                sockets[conn.fileno()] = conn
                io.add_handler(conn.fileno(), handle_connection, select.EPOLLIN)
                print "add accept sockets:", sockets
            except socket.error as ex:
                print "accept:", ex
                if ex[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return 
                raise
                print "[Main error]:", ex
                return
            conn.setblocking(0)
            handle_connection(fd, events)


    def handle_connection(fd, events, read_chunk_size=4096):
        # TODO fd error.
        if not sockets[fd]:
            logging.error("No sock, fd: %s" % fd)
            return

        if events & select.EPOLLIN:
            # read
            if fd != s.fileno():
                chunk = sockets[fd].recv(read_chunk_size)
                if not chunk:
                    io.remove_handler(fd)
                    sockets[fd].close()

        elif events & select.EPOLLOUT:
            # write
            num_bytes = sockets[fd].send(response)
            io.modify_handler(fd, select.EPOLLOUT)

        elif events & select.EPOLLERR:
            sockets[fd].close()
            print "[ENTER EPOLLERR]"
            return

        
    def handle_httpheader(data):
        print data


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(0)
    s.bind(("", 8888))
    s.listen(128)

    sockets[s.fileno()] = s
    cb = functools.partial(callback, s)
    io.add_handler(s.fileno(), cb, select.EPOLLIN)
    io.loop()
