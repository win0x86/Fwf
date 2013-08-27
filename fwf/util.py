# coding: utf-8

"""Utility

"""

import time


def gen_header_date():
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
