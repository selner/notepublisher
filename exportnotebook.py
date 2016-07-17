#!/bin/python
# -*- coding: utf-8 -*-

__name__ = "NotePublisher"
import evernote.edam.notestore.NoteStore as NoteStore
import os
import enmltohtml
import helpers
import datetime
import bs4 as BeautifulSoup
from client import getEvernoteClient

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x

PAGE_BASE_LAYOUT = """
<HTML>
<HEAD>
<TITLE></TITLE>
<STYLE>

body {
	/* Font & Text */
	font-family: Times;
	font-size: 16px;
	font-style: normal;
	font-variant: normal;
	font-weight: normal;
	letter-spacing: normal;
	line-height: 16px;
	text-decoration: none;
	text-align: start;
	text-indent: 0px;
	text-transform: none;
	vertical-align: baseline;
	white-space: normal;
	word-spacing: 0px;

	/* Color & Background */
	background-attachment: scroll;
	background-color: rgb(255, 255, 255);
	background-image: none;
	background-position: 0% 0%;
	background-repeat: repeat;
	color: rgb(0, 0, 0);
}

h1 {


font-family: caecilia, times, serif;
font-size: 28px;
font-stretch: normal;
font-style: normal;
font-variant: normal;
font-weight: 300;
line-height: 32px;
vertical-align: baseline;
color: #2DBE60;
}

#note-content {
    color: #383838;
    font-family: gotham, helvetica, arial, sans-serif;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
}

.metafact-heading {
    margin-right: 8px;
    color: #878787;
    -webkit-font-smoothing: antialiased;
    font-family: gotham, helvetica, arial, sans-serif;
    font-size: 11px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metafact {
    color: #4a4a4a;
    -webkit-font-smoothing: antialiased;
    font-family: gotham, helvetica, arial, sans-serif;
    font-size: 13px;
    font-weight: 400;
    -webkit-font-smoothing: antialiased;
    font-family: gotham, helvetica, arial, sans-serif;
    font-size: 11px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-right: 15px;
}
</STYLE>
</HEAD>
<BODY>
<H1 style="margin-bottom: 5px;"></H1>
<HR/><DIV id="note-content"><DIV id="end-note-content"></DIV></DIV>
<!-- exported by pyEvernotePublish --></BODY>
</HTML>

"""


class NotebooksExport(object):

    def __init__(self, arguments=None):
        self.arguments = arguments


        self.client = getEvernoteClient(**arguments)

    def insertNoteInfoTagsForNote(self, note, notebook, soup):
        properties = ""
        attr = note.attributes.__dict__
        if not soup.head:
            soup.body.insert_before(soup.new_tag('head'))

        divstrtemp = "<div style=\"white-space: no-wrap; display: inline-flex; margin-right: 15px;\"><span class=\"metafact-heading\">%s</span><span class=\"metafact\">%s</span></div>\n"

        subheaditems = ""
        for key in attr:
            if attr[key] is not None and attr[key] != 0:
                metatag = soup.new_tag('meta')
                metatag.attrs['content'] = escape(str(attr[key]))
                metatag.attrs['name'] = escape(str(key))
                soup.head.append(metatag)

                subheaditems += divstrtemp % (str(key), str(attr[key]))

        subheaditems += divstrtemp % ("Notebook", notebook.name)

        now = datetime.datetime.now()
        nowstr= now.strftime("%x %X")
        subheaditems += divstrtemp % ("Exported", nowstr)

        tagNames = self.client.get_note_store().getNoteTagNames(self.client.token, note.guid)
        if tagNames:
            tags = ", ".join(tagNames)
            subheaditems += divstrtemp % ("Tags", tags)

        divSoup = BeautifulSoup.BeautifulSoup(subheaditems)
        soup.h1.insert_after(divSoup.body)

        return soup


    def get_notebooks(self):
        note_store = self.client.get_note_store()
        notebooks = note_store.listNotebooks()
        return {n.name: n for n in notebooks}

    def filter_noteboooks_by_stack(self, notebooks, matchString):
        print "Filtering notebooks to memebers of stack '%s'..." % (matchString)
        stackbooks = {key: value for key, value in notebooks.items() if value.stack is not None and matchString in value.stack}
        return stackbooks


    def exportStack(self, stackstr):


        notebooks = self.get_notebooks()
        stackbooks = self.filter_noteboooks_by_stack(notebooks, stackstr)

        note_store = self.client.get_note_store()
        for key in stackbooks:
            notebook = stackbooks[key]
            notebookDirectory = os.path.join(self.arguments["output"], notebook.name)
            if not os.path.exists(notebookDirectory):
                os.makedirs(notebookDirectory)

            filter = NoteStore.NoteFilter()

            if notebook is not None:
                filter.notebookGuid = notebook.guid
            else:
                filter.notebookGuid = note_store.defaultNotebook.guid

            # for tag in tags:
            #    if tag.name.find("test") >= 0:
            #        filter.tagGuids = [tag.guid]
            #        break

            noteList = note_store.findNotes(self.client.token, filter, 0, 9999)
            notes = []

            for note in noteList.notes:
                content = note_store.getNoteContent(note.guid)
                noteResourceDir = os.path.join(notebookDirectory, (note.title + "-resources/"))
                mediaStore = enmltohtml.FileMediaStore(note_store, note.guid, noteResourceDir)
                html = enmltohtml.ENMLToHTML(content=content, pretty=True, header=False, media_store=mediaStore)

                soup = BeautifulSoup.BeautifulSoup(PAGE_BASE_LAYOUT)
                soup.title.string = note.title
                soup.h1.string = note.title
                soup = self.insertNoteInfoTagsForNote(note, notebook, soup)

                divNote = soup.find(id="end-note-content")

                soupNoteHTML = BeautifulSoup.BeautifulSoup(html)

                for element in soupNoteHTML.body:
                    divNote.insert_before(element)

                html = soup.prettify(formatter="html")

                outfile = helpers.export_html_file(path=notebookDirectory, basename=note.title, html=html, encoding=None)
                print "Published " + note.title + " to " + outfile
