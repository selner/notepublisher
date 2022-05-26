#!/bin/python
# -*- coding: utf-8 -*-


def reraise_exception(prefixmsg="", exception=None):
    raise Exception(f'{prefixmsg} {exception}')
