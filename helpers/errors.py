#!/bin/python
# -*- coding: utf-8 -*-


def reRaiseException(prefixmsg="", exception=None):
    newmsg = unicode(prefixmsg) + u" " + unicode(exception)
    raise type(exception)(newmsg)

