import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.error.ttypes as evernote_types
from session import EvernoteSession
from notepublisher import helpers
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
        # self.oauth_token = get_last_oauth_token()
        # self.user = self.client.get_user_store().getUser()
        # self.userPublicInfo = self.client.get_user_store().getPublicUserInfo(self.user.username)
        user = self.client.user_store.getPublicUserInfo(self.client.user.username)
        self.resourceUriPrefix = user.webApiUrlPrefix + "res"

    def filter_noteboooks_by_fact(self, fact, matchval):
        print("Filtering notebooks to %s matching '%s'..." % (fact, matchval))
        matched = {getattr(n, fact): n for n in self.client.notebooks.values() if
                   getattr(n, fact) and matchval in getattr(n, fact)}
        return matched

    def export_search(self):

        try:
            notebooks = {}

            if "--matchstack" in self.arguments and self.arguments["--matchstack"] is not None:
                notebooks = self.filter_noteboooks_by_fact('stack', self.arguments["--matchstack"])

            if "--matchnotebook" in self.arguments and self.arguments["--matchnotebook"] is not None:
                notebooks = self.filter_noteboooks_by_fact('name', self.arguments["--matchnotebook"])

            for key in notebooks:
                notebook = notebooks[key]

                notefilter = NoteStore.NoteFilter()

                if notebook is not None:
                    notefilter.notebookGuid = notebook.guid
                else:
                    notefilter.notebookGuid = self.client.default_notebook.guid

                # offset = 0;
                # pageSize = 10;
                # notes = [];
                # resultSpec = { "includeTitle": True, "includeNotebookGuid":True, "includeAttributes":True, "includeContentLength" :True }

                search_results = self.client.note_store.findNotes(self.client.token, notefilter, 0, 9999)
                for noteMeta in search_results.notes:
                    noteexp = NoteExport(client=self.client, output_dir=self.arguments["output"],
                                         metadata=noteMeta, notebook=notebook, tags=self.client.tags,
                                         resource_uri_prefix=self.resourceUriPrefix)
                    noteexp.export()

                # search_results = self.note_store.findNotesMetadata(self.client.token, notefilter, offset, pageSize, spec = resultSpec)
                # remaining = search_results.totalNotes()
                # while (remaining < search_results.getTotalNotes()):
                #     nextNotes = search_results.getNotes()
                #
                #         for noteMeta in nextNotes:
                #             html = None
                #             noteexp = NoteExport(client=self.client, user=self.user, metadata=noteMeta)
                #
                #
                #     remaining = search_results.totalNotes - (search_results.startIndex + notes.length)
                #     offset = offset + search_results.getNotesSize()

            print("Successfully published notes to %s" % self.arguments["output"])

        except evernote_types.EDAMSystemException as e:
            if e.errorCode == evernote_types.EDAMErrorCode.RATE_LIMIT_REACHED:
                print("Rate limit reached.  Retrying the request in %d seconds." % e.rateLimitDuration)
                import time
                time.sleep(int(e.rateLimitDuration) + 1)
                self.export_search()
            else:
                print("!!!!! Error:  Failed to access note via Evernote API.  Message:  %s" % e)
                exit(-1)
        except evernote_types.EDAMUserException as e:
            print("Invalid Evernote API request.  Please check the call parameters.  Message: %s" % e)
            exit(-1)
        except Exception as e:
            helpers.reraise_exception("!!!!! Error:  Failed to access note via Evernote API.  Message:", e)
            exit(-1)
