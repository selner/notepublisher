#!/bin/python
# -*- coding: utf-8 -*-


def reRaiseException(prefixmsg="", exception=None):
    raise type(exception)(u"{} {}".format(prefixmsg, exception))

