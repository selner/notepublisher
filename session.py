#!/bin/python
# -*- coding: utf-8 -*-
import evernote.edam.error.ttypes as EvernoteTypes
import evernote.edam.userstore.constants as UserStoreConstants
from evernote.api.client import EvernoteClient
import platform
import os
import sys

#######
#
# Enable caching of http requests through the requests package
# to reduce API hits on servers and rate limit issues
#
import requests
from cachecontrol import CacheControl
sess = requests.session()
cached_sess = CacheControl(sess)
#######

#######
#
# Debug logging of requests
#
import logging
import httplib2
httplib2.debuglevel = 4

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
req_log = logging.getLogger('requests.packages.urllib3')
req_log.setLevel(logging.DEBUG)
req_log.propagate = True

#######

EXEC_FILENAME = sys.argv[0]
BASE_EXEC_FILENAME = os.path.basename(EXEC_FILENAME).split(".")[0]
APP_STATE_DIR = os.path.join(os.path.expanduser(u'~'), "." + BASE_EXEC_FILENAME)
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
    request_token = client.get_request_token("http://localhost")

#    request_token = client.get_request_token(baseURI + '/oauth')
    authorization_url = client.get_authorize_url(request_token)
    #  => https://sandbox.evernote.com/OAuth.action?oauth_token=OAUTH_TOKEN
    # To obtain the access token
    #
    import webbrowser
    webbrowser.open_new(authorization_url)

    print("Your browser is opening the OAuth authorization for this client session.")
    response = input("Paste the URL after login here: ")
    vals = parse_query_string(response)

    access_token = client.get_access_token(
        request_token['oauth_token'],
        request_token['oauth_token_secret'],
        vals['oauth_verifier'])

    return access_token



def getLastOAuthToken():
    oauth_token = None
    if os.path.exists(TOKEN_FILEPATH):
        with open(TOKEN_FILEPATH, 'r') as token_file:
            oauth_token = token_file.read()
    return oauth_token

class EvernoteSession(object):
    _client = None
    _args = {}
    _notestore = None
    _userstore = None
    _notebooks = None
    _user = None
    _default_notebook = None
    _tags = None

    def __init__(self, **kwargs):
        self._args = kwargs

    @property
    def note_store(self):
        if not self._notestore:
            self._notestore = self.client.get_note_store()
        return self._notestore

    @property
    def user_store(self):
        if not self._userstore:
            self._userstore = self.client.get_user_store()
        return self._userstore

    @property
    def user(self):
        if not self._user:
            self._user = self.user_store.getUser()
        return self._user

    @property
    def client(self):
        if not self._client:
            self.connect(**self._args)
        return self._client

    @property
    def token(self):
        return self._client.token

    @property
    def notebooks(self):
        if not self._notebooks:
            self._notebooks = dict([(nb.guid, nb) for nb in self.note_store.listNotebooks()])
        return self._notebooks

    @property
    def notebooks_by_title(self):
        return dict([(nb.name, nb) for nb in self._notebooks])

    @property
    def default_notebook(self):
        if not self._default_notebook:
            self._default_notebook = self.note_store.defaultNotebook
        return self._default_notebook

    @property
    def tags(self):
        if not self._tags:
            self._tags = dict([(t.guid, t) for t in self.note_store.listTags()])
        return self._tags


    def connect(self, **kwargs):
        self._args = kwargs

        try:
            print(f'Getting client instance for Evernote...\n\tParameters = {kwargs}')
            oauth_token = getLastOAuthToken()
            if oauth_token:
                try:
                    self._client = EvernoteClient(token=oauth_token, sandbox=False)
                except:
                    self._client = None

            if self._client is None:

                if "consumer_key" in kwargs and "consumer_secret" in kwargs:
                    oauth_token = getProductionOauthToken(key=kwargs["consumer_key"],
                                                          secret=kwargs["consumer_secret"])
                elif "dev_auth_token" in kwargs:
                    if kwargs["dev_auth_token"] == "your developer token":
                        print("Please fill in your developer token")
                        print("To get a developer token, visit " \
                              "https://sandbox.evernote.com/api/DeveloperToken.action")
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

                self._client = EvernoteClient(token=oauth_token, sandbox=False)

                # save token file
                with open(TOKEN_FILEPATH, 'w') as token_file:
                    token_file.write("%s" % (oauth_token))

            platdetails = platform.platform(aliased=True, terse=False)
            plateuname = platform.uname()
            print ("NotePublisher is running on %s." % platdetails)
            version_ok = self.user_store.checkVersion(
                "NotePublisher " + platdetails,
                UserStoreConstants.EDAM_VERSION_MAJOR,
                UserStoreConstants.EDAM_VERSION_MINOR
            )
            print ("Is the Evernote API version up to date? ", version_ok)
            print ("")
            if not version_ok:
                exit(1)

            return self._client

        except EvernoteTypes.EDAMSystemException as e:
            if e.errorCode == EvernoteTypes.EDAMErrorCode.RATE_LIMIT_REACHED:
                print ("Rate limit reached.  Retrying the request in %d seconds." % e.rateLimitDuration)
                import time

                time.sleep(int(e.rateLimitDuration) + 1)

            else:
                print ("!!!!! Error:  Failed to access note via Evernote API.  Message:  %s" % e)
                exit(-1)
        except EvernoteTypes.EDAMUserException as e:
            print ("Invalid Evernote API request.  Please check the call parameters.  Message: %s" % e)
            exit(-1)

def getEvernoteClient(**kwargs):

    try:
        client = None

        print("Getting client instance for Evernote...\n\tParameters = " + kwargs)
        oauth_token = getLastOAuthToken()
        if oauth_token:
            try:
                client = EvernoteClient(token=oauth_token, sandbox=False)
            except:
                client = None

        if client is None:

            if "consumer_key" in kwargs and "consumer_secret" in kwargs:
                oauth_token = getProductionOauthToken(key=kwargs["consumer_key"], secret=kwargs["consumer_secret"])
            elif "dev_auth_token" in kwargs:
                if kwargs["dev_auth_token"] == "your developer token":
                    print("Please fill in your developer token")
                    print("To get a developer token, visit " \
                          "https://sandbox.evernote.com/api/DeveloperToken.action")
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

            # save token file
            with open(TOKEN_FILEPATH, 'w') as token_file:
                token_file.write("%s" % (oauth_token))

        user_store = client.get_user_store()
        platdetails = platform.platform(aliased=True, terse=False)
        plateuname = platform.uname()
        print ("NotePublisher is running on %s." % platdetails)
        version_ok = user_store.checkVersion(
            "NotePublisher " + platdetails,
            UserStoreConstants.EDAM_VERSION_MAJOR,
            UserStoreConstants.EDAM_VERSION_MINOR
        )
        print ("Is the Evernote API version up to date? ", version_ok)
        print ("")
        if not version_ok:
            exit(1)

        return client

    except EvernoteTypes.EDAMSystemException as e:
        if e.errorCode == EvernoteTypes.EDAMErrorCode.RATE_LIMIT_REACHED:
            print ("Rate limit reached.  Retrying the request in %d seconds." % e.rateLimitDuration)
            import time

            time.sleep(int(e.rateLimitDuration) + 1)

        else:
            print ("!!!!! Error:  Failed to access note via Evernote API.  Message:  %s" % e)
            exit(-1)
    except EvernoteTypes.EDAMUserException as e:
        print ("Invalid Evernote API request.  Please check the call parameters.  Message: %s" % e)
        exit(-1)

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


