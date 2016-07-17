import evernote.edam.userstore.constants as UserStoreConstants
from evernote.api.client import EvernoteClient


import json
import codecs
import os
import sys

EXEC_FILENAME = sys.argv[0]
BASE_EXEC_FILENAME = os.path.basename(EXEC_FILENAME).split(".")[0]
APP_STATE_DIR = os.path.join(os.path.expanduser('~'), BASE_EXEC_FILENAME)
if not os.path.exists(APP_STATE_DIR):
    os.makedirs(APP_STATE_DIR)
TOKEN_FILEPATH = os.path.join(APP_STATE_DIR, BASE_EXEC_FILENAME + ".t")

def getProductionOauthToken(key, secret):
    client = EvernoteClient(
        consumer_key=key,
        consumer_secret=secret,
        sandbox=False
    )
    baseURI = "https://www.evernote.com"
    request_token = client.get_request_token('http://localhost')

#    request_token = client.get_request_token(baseURI + '/oauth')
    authorization_url = client.get_authorize_url(request_token)
    #  => https://sandbox.evernote.com/OAuth.action?oauth_token=OAUTH_TOKEN
    # To obtain the access token
    #
    import webbrowser
    webbrowser.open_new(authorization_url)

    print("Your browser is opening the OAuth authorization for this client session.")
    response = raw_input("Paste the URL after login here: ")
    vals = parse_query_string(response)

    access_token = client.get_access_token(
        request_token['oauth_token'],
        request_token['oauth_token_secret'],
        vals['oauth_verifier'])

    return access_token



def getEvernoteClient(**kwargs):
    client = None

    print "Getting client instance for Evernote...\n\tParameters = " + str(kwargs)
    oauth_token = None
    if os.path.exists(TOKEN_FILEPATH):
        with open(TOKEN_FILEPATH, 'r') as token_file:
            oauth_token = token_file.read()

        try:
            client = EvernoteClient(token=oauth_token, sandbox=False)
        except:
            client = None

    if client is None:

        if "consumer_key" in kwargs and "consumer_secret" in kwargs:
            oauth_token = getProductionOauthToken(key=kwargs["consumer_key"], secret=kwargs["consumer_secret"])
        elif "dev_auth_token" in kwargs:
            if kwargs["dev_auth_token"] == "your developer token":
                print "Please fill in your developer token"
                print "To get a developer token, visit " \
                      "https://sandbox.evernote.com/api/DeveloperToken.action"
                exit(1)

                oauth_token = kwargs["dev_auth_token"]

        # authorization_keys_path = kwargs.get('authorization_keys_path')
        # if authorization_keys_path is None:
        #     oauth_token = EvernoteClient(**kwargs)
        # else:
        #     f = codecs.open(authorization_keys_path, mode='r')
        #     clientKeys = json.load(fp=f)
        #
        #     if "consumer_key" in clientKeys and "consumer_secret" in clientKeys:
        #         oauth_token = getProductionOauthToken(key=clientKeys["consumer_key"], secret=clientKeys["consumer_secret"])
        #     elif "dev_auth_token" in clientKeys:
        #         if clientKeys["dev_auth_token"] == "your developer token":
        #             print "Please fill in your developer token"
        #             print "To get a developer token, visit " \
        #                   "https://sandbox.evernote.com/api/DeveloperToken.action"
        #             exit(1)
        #
        #             oauth_token = clientKeys["dev_auth_token"]

        client = EvernoteClient(token=oauth_token, sandbox=False)

        user_store = client.get_user_store()

        version_ok = user_store.checkVersion(
            "Evernote EDAMTest (Python)",
            UserStoreConstants.EDAM_VERSION_MAJOR,
            UserStoreConstants.EDAM_VERSION_MINOR
        )
        print "Is my Evernote API version up to date? ", str(version_ok)
        print ""
        if not version_ok:
            exit(1)

        # save token file
        with open(TOKEN_FILEPATH, 'w') as token_file:
            token_file.write("%s" % (oauth_token))

    return client

def parse_query_string(authorize_url):
    """ Simple function for extracting the OAuth parameters from an URL
    """
    uargs = authorize_url.split('?')
    vals = {}
    if len(uargs) == 1:
        raise Exception('Invalid Authorization URL')
    for pair in uargs[1].split('&'):
        key, value = pair.split('=', 1)
        vals[key] = value
    return vals


