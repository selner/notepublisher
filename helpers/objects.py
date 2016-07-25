#!/bin/python
# -*- coding: utf-8 -*-
from strings import xustr

class objdict(dict):
    """ objdict class allows access to its key's values as
        attributes such as objdict.key = True or the dict way
        objdict['key'] = True.

        objdefaultdict functions the same as objdict except that
        it simply returns "None" for any key value that is not
        present instead of raising an exception
    """

    def __init__(self, **kwargs):
        super(dict, self).__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def debugprint(self, label):
        print xustr(label) + unicode("debug print for objdict:\n")
        pp.pprint(self)
        print "\n"


class objdefaultdict(objdict):
    def __getattr__(self, name):
        try:
            return objdict.__getattr__(self, name)
        except AttributeError:
            return None