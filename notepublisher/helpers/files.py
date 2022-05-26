#!/bin/python
# -*- coding: utf-8 -*-

import os
import datetime
from notepublisher.helpers.strings import xustr


def get_now_datestamp(fmt):
    now = datetime.datetime.now()
    ret = now.strftime(fmt)
    return ret


def setup_output_dir(folderpath):
    """ Creates the necessary folders in the path specified,
        including the actual folder we care about and any parents
        it needs.   Also handles expanding user paths ("~") and
        relative paths to their full absolute values.

        Returns the absolute path to the folder.
    """
    if not folderpath:
        raise AttributeError("Error: cannot setup output folder path.  No path specified.")

    if folderpath.__contains__("~"):
        folderpath = os.path.expanduser(folderpath)

    folderpath = os.path.abspath(folderpath)

    outputfolder = os.path.abspath(folderpath + "/")
    if not os.path.exists(outputfolder):
        os.makedirs(outputfolder)

    return outputfolder


def generate_output_name(prefix=None, basename=None, suffix=None, ext=None, include_data=False):
    if not ext:
        raise ValueError("Required file extension paramater was not set.")

    if suffix and basename and not basename.endswith("_"):
        suffix = "_" + xustr(suffix)
    else:
        suffix = ""

    if prefix and not prefix.endswith("_"):
        prefix = xustr(prefix) + "_"
    else:
        prefix = ""

    ret = prefix
    if include_data:
        ret += get_now_datestamp("%m-%d-%Y") + "_"

    ret += xustr(basename) + suffix + "." + ext

    return ret


def save_text_file(path=None, basename=None, ext="txt", textdata=None):
    """
        Writes a file to disk with the text passed.  If filepath is not specified, the filename will
        be <testname>_results.txt.
    :return: the path of the file
    """
    filepath = path
    try:
        file = generate_output_name(basename=basename, ext=ext)
        os.makedirs(path, exist_ok=True)

        filepath = os.path.join(path, file)
        with open(filepath, mode="w") as f:
            f.write(textdata)

        return filepath

    except Exception as e:
        from notepublisher import helpers
        helpers.reraise_exception(f'!!!!!! ERROR:  Failed to export file "{filepath}" due to error: {e}')


def export_html_file(path=None, basename=None, html=None):
    """
        Writes a file to disk with the HTML version of the test
        result report.  If filepath is not specified, the filename will
        be <testname>_results.html.
    :return: the path of the HTML file
    """
    return save_text_file(path=path, basename=basename, ext="html", textdata=html)
