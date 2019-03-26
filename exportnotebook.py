#!/bin/python
# -*- coding: utf-8 -*-

__name__ = "NotePublisher"
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.error.ttypes as EvernoteTypes
from session import EvernoteSession
import helpers
from exportnote import NoteExport
try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x


class NotebooksExport(object):

    def __init__(self, arguments=None):
        self.arguments = arguments
        self.client = EvernoteSession()
        self.client.connect(**arguments)

        # self.note_store = self.client.note_store
        # self.oauth_token = getLastOAuthToken()
        # self.user = self.client.get_user_store().getUser()
        # self.userPublicInfo = self.client.get_user_store().getPublicUserInfo(self.user.username)
        self.resourceUriPrefix = "%sres" % self.client.user_store.getPublicUserInfo(self.client.user.username).webApiUrlPrefix

    def filter_noteboooks_by_fact(self, fact, matchString):
        print (u"Filtering notebooks to %s matching '%s'..." % (fact, matchString))
        matched = {getattr(n, fact): n for n in self.client.notebooks.values() if getattr(n, fact) and matchString in getattr(n, fact) }
        return matched

    def exportSearch(self):

        try:
            notebooks = {}

            if "--matchstack" in self.arguments and self.arguments["--matchstack"] is not None:
                notebooks = self.filter_noteboooks_by_fact('stack', self.arguments["--matchstack"])

            if "--matchnotebook" in self.arguments and self.arguments["--matchnotebook"] is not None:
                notebooks =  self.filter_noteboooks_by_fact('name', self.arguments["--matchnotebook"])

            for key in notebooks:
                notebook = notebooks[key]

                filter = NoteStore.NoteFilter()

                if notebook is not None:
                    filter.notebookGuid = notebook.guid
                else:
                    filter.notebookGuid = self.client.default_notebook.guid

                # offset = 0;
                # pageSize = 10;
                # notes = [];
                # resultSpec = { "includeTitle": True, "includeNotebookGuid":True, "includeAttributes":True, "includeContentLength" :True }

                allNoteResults = self.client.note_store.findNotes(self.client.token, filter, 0, 9999)
                for noteMeta in allNoteResults.notes:
                    noteexp = NoteExport(client=self.client, outputFolder=self.arguments["output"], noteMetadata=noteMeta, notebook=notebook, tags=self.client.tags, resourceUriPrefix=self.resourceUriPrefix)
                    noteexp.export()

                # allNoteResults = self.note_store.findNotesMetadata(self.client.token, filter, offset, pageSize, spec = resultSpec)
                # remaining = allNoteResults.totalNotes()
                # while (remaining < allNoteResults.getTotalNotes()):
                #     nextNotes = allNoteResults.getNotes()
                #
                #         for noteMeta in nextNotes:
                #             html = None
                #             noteexp = NoteExport(client=self.client, user=self.user, noteMetadata=noteMeta)
                #
                #
                #     remaining = allNoteResults.totalNotes - (allNoteResults.startIndex + notes.length)
                #     offset = offset + allNoteResults.getNotesSize()


        except EvernoteTypes.EDAMSystemException, e:
            if e.errorCode == EvernoteTypes.EDAMErrorCode.RATE_LIMIT_REACHED:
                print (u"Rate limit reached.  Retrying the request in %d seconds." % e.rateLimitDuration)
                import time
                time.sleep(int(e.rateLimitDuration) + 1)
                self.exportSearch()
            else:
                print (u"!!!!! Error:  Failed to access note via Evernote API.  Message:  %s" % unicode(e))
                exit(-1)
        except EvernoteTypes.EDAMUserException, e:
            print (u"Invalid Evernote API request.  Please check the call parameters.  Message: %s" % unicode(e))
            exit(-1)
        except Exception, e:
            helpers.reRaiseException(u"!!!!! Error:  Failed to access note via Evernote API.  Message:", e)
            exit(-1)


