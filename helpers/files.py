#!/bin/python
# -*- coding: utf-8 -*-

import os
import codecs
import datetime
from strings import xustr

def getDatetimeForFileName(fmt):
    now = datetime.datetime.now()
    ret = now.strftime(fmt)
    return ret


def setupOutputFolder(folderpath):
    """ Creates the necessary folders in the path specified,
        including the actual folder we care about and any parents
        it needs.   Also handles expanding user paths ("~") and
        relative paths to their full absolute values.

        Returns the absolute path to the folder.
    """
    if not folderpath:
        raise AttributeError("Error: cannot setup output folder path.  No path specified.")

    if unicode(folderpath).__contains__("~"):
        folderpath = os.path.expanduser(folderpath)

    folderpath = os.path.abspath(folderpath)

    outputfolder = os.path.abspath(folderpath + "/")
    if not os.path.exists(outputfolder):
        os.makedirs(outputfolder)

    return outputfolder


def getOutFileName(prefix=None, basename=None, suffix=None, ext=None, fIncludeDate=False):
    if not ext:
        raise ValueError("Required file extension paramater was not set.")

    if suffix and basename and not unicode(basename).endswith("_"):
        suffix = "_" + xustr(suffix)
    else:
        suffix = ""

    if prefix and not prefix.endswith("_"):
        prefix = xustr(prefix) + "_"
    else:
        prefix = ""

    ret = prefix
    if fIncludeDate:
        ret += getDatetimeForFileName("%m-%d-%Y") + "_"

    ret += xustr(basename) + suffix + "." + ext

    return ret


def save_text_file(path=None, basename=None, ext="txt", textdata=None, encoding='utf-8'):
    """
        Writes a file to disk with the text passed.  If filepath is not specified, the filename will
        be <testname>_results.txt.
    :return: the path of the file
    """

    file = getOutFileName(basename=basename, ext=ext)
    try:
        os.mkdir(path)
    except:
        pass

    filepath = os.path.join(path, file)

    f = codecs.open(filepath, encoding=encoding, mode='w+')

    f.write(textdata)
    f.close()

    return filepath


def export_html_file(path=None, basename=None, html=None, encoding='utf-8'):
    """
        Writes a file to disk with the HTML version of the test
        result report.  If filepath is not specified, the filename will
        be <testname>_results.html.
    :return: the path of the HTML file
    """
    return save_text_file(path=path, basename=basename, ext="html", textdata=html, encoding=encoding)
