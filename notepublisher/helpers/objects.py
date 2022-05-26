#!/bin/python
# -*- coding: utf-8 -*-
from notepublisher.helpers.strings import xustr


class ObjDict(dict):
    """ ObjDict class allows access to its key's values as
        attributes such as ObjDict.key = True or the dict way
        ObjDict['key'] = True.

        ObjDefaultDict functions the same as ObjDict except that
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
        print(xustr(label) + "debug print for ObjDict:\n")
        print(self)
        print("\n")


class ObjDefaultDict(ObjDict):
    def __getattr__(self, name):
        try:
            return ObjDict.__getattr__(self, name)
        except AttributeError:
            return None
