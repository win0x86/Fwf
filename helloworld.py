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



class Test403Handler(fwf.web.RequestHandler):
    def get(self):
        raise fwf.web.HTTPError(403, "Not allow.")



def main():
    port = 8888
    logging.getLogger().setLevel(logging.INFO)

    handlers = {
        "/": HelloWorldHandler,
        "/403": Test403Handler,
        "/500": TestErrorHandler,
        }

    context = fwf.web.Context(handlers, debug=True)
    s = fwf.server.HTTPServer(context)
    s.bind(port=port)
    logging.info("Listen on %d ..." % port)
    fwf.rawio.RawIO.instance().loop()



if __name__ == "__main__":
    main()
