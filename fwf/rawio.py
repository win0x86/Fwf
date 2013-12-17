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
    def __init__(self):
        self._epoll = select.epoll()
        self._handlers = {}


    @classmethod
    def instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()

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
                    self._handlers[fd](fd, event)
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
        try:
            if fd in self._handlers:
                self._handlers.pop(fd)
            self._epoll.unregister(fd)
        except (OSError, IOError):
            logging.error("Error removing fd from epoll", exc_info=True)
