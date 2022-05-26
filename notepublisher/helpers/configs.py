import os


def load_config_from_json(filepath):
    import json
    # Pretend that we load the following JSON file:
    js = {}
    filepath = os.path.abspath(filepath)

    if (os.path.exists(filepath)):
        print('\tloading config settings from %s:' % filepath)
        with open(filepath, 'r') as cfgfile:
            js = json.load(fp=cfgfile)
    return js
