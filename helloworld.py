#!/usr/bin/env python
# coding: utf-8

"""Fwf Helloworld example.

"""

import logging

import fwf.rawio
import fwf.web
import fwf.server


class HelloWorldHandler(fwf.web.RequestHandler):
    def get(self):
        s = b"Hello world."
        response = [b"HTTP/1.1 200 OK\r\n",
                    b"Date: Mon, 1 Jan 2013 01:01:01 GMT\r\n",
                    b"Content-Type: text/plain\r\n",
                    b"Content-Length: %d\r\n\r\n" % len(s),
                    s]
        response = b"".join(response)

        self.finish(response)



def main():
    logging.getLogger().setLevel(logging.INFO)

    handlers = {"/": HelloWorldHandler}
    context = fwf.web.Context(handlers)
    s = fwf.server.HTTPServer(context)
    s.bind()
    fwf.rawio.RawIO.instance().loop()



if __name__ == "__main__":
    main()
