# coding: utf-8

"""Utility

"""

import time


def gen_header_date():
    """RFC1123 Date format.
    """
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
