import evernote.edam.userstore.constants as UserStoreConstants
from evernote.api.client import EvernoteClient


import json
import codecs

def getClientInstance(fileAuthKeys):
    f = codecs.open(fileAuthKeys, mode='r')
    clientKeys = json.load(fp=f)

    if "consumer_key" in clientKeys and "consumer_secret" in clientKeys:
        return getOauthClientInstance(key=clientKeys["consumer_key"], secret=clientKeys["consumer_secret"])
    elif "dev_auth_token" in clientKeys:
        return getDevClientInstance(auth_token=clientKeys["dev_auth_token"])

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


def getDevClientInstance(auth_token= "your developer token"):
    # Real applications authenticate with Evernote using OAuth, but for the
    # purpose of exploring the API, you can get a developer token that allows
    # you to access your own Evernote account. To get a developer token, visit
    # https://sandbox.evernote.com/api/DeveloperToken.action
    if auth_token == "your developer token":
        print "Please fill in your developer token"
        print "To get a developer token, visit " \
            "https://sandbox.evernote.com/api/DeveloperToken.action"
        exit(1)

    # Initial development is performed on our sandbox server. To use the production
    # service, change sandbox=False and replace your
    # developer token above with a token from
    # https://www.evernote.com/api/DeveloperToken.action
    client = EvernoteClient(token=auth_token, sandbox=True)

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

    return client




def getOauthClientInstance(key, secret, sandbox=True):
    client = EvernoteClient(
        consumer_key=key,
        consumer_secret=secret,
        sandbox=sandbox # Default: True
    )
    if sandbox:
        baseURI = "https://sandbox.evernote.com"
    else:
        baseURI = "https://www.evernote.com"
    request_token = client.get_request_token('http://localhost')

    # request_token = client.get_request_token(baseURI + '/oauth')
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

    client = EvernoteClient(token=access_token)

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

    return client

