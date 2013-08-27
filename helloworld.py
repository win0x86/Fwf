#!/usr/bin/env python
# coding: utf-8

"""Fwf Helloworld example.

"""

import time
import logging

import fwf.rawio
import fwf.web
import fwf.server


class HelloWorldHandler(fwf.web.RequestHandler):
    def get(self):
        s = b"Hello world."
        self.finish(s)



class TestErrorHandler(fwf.web.RequestHandler):
    def get(self):
        s = "Test error handler."
        raise Exception(s)
        self.finish(s)



def main():
    logging.getLogger().setLevel(logging.INFO)

    handlers = {
        "/": HelloWorldHandler,
        "/500": TestErrorHandler,
        }

    context = fwf.web.Context(handlers)
    s = fwf.server.HTTPServer(context)
    s.bind()
    fwf.rawio.RawIO.instance().loop()



if __name__ == "__main__":
    main()
