#!/bin/python
# -*- coding: utf-8 -*-
import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

cli_usage = """
Usage:
  notepublisher.py [-c FILE] [-o DIR] [--matchstack=STRING] [--matchnotebook=STRING] [--formats=PATTERNS]
  notepublisher.py --version

Options:
  -h --help  show this help message and exit
  --version  show version and exit
  -v --verbose  print status messages
  -o DIR --output=DIR  output directory [default: ./]
  -c FILE --config=FILE  config settings directory [default: ./notepublisher.cfg]
  --matchstack=STRING  string to match stack names against when searching
  --matchnotebook=STRING  string to match notebook names against when searching
  --formats=PATTERNS   export notes to file formats which match these comma
                       separated patterns [default: html,enex]
"""

from docopt import docopt

def merge(dict_1, dict_2):
    """Merge two dictionaries.

    Values that evaluate to true take priority over falsy values.
    `dict_1` takes priority over `dict_2`.

    """
    return dict((unicode(key), dict_1.get(key) or dict_2.get(key))
                for key in set(dict_2) | set(dict_1))

def load_config_from_json(filepath):
    import json
    # Pretend that we load the following JSON file:
    js = {}
    filepath = os.path.abspath(filepath)

    if(os.path.exists(filepath)):
        print('\tloading config settings from %s:' % filepath)
        with open(filepath, 'r') as cfgfile:
            js = json.load(fp=cfgfile)
    return js


if __name__ == '__main__':
    arguments = docopt(cli_usage, version='0.1.1rc')

    json_config = {}
    if("--config" in arguments):
        json_config = load_config_from_json(arguments["--config"])

    # Arguments take priority over JSON:
    argresult = merge(json_config, arguments)

    from pprint import pprint
    print('\nArguments:')
    pprint(arguments)
    print('\nJSON config:')
    pprint(json_config)
    print('\nResult:')
    pprint(argresult)

    import exportnotebook
    export = exportnotebook.NotebooksExport(argresult)
    export.exportSearch()

    print (u"Successfully published notes to %s" % argresult["output"])