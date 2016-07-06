auth_token = "S=s1:U=92afd:E=15d0a871533:C=155b2d5e838:P=1cd:A=en-devtoken:V=2:H=597eae9b2b2e278a8fb160460e20c8d5"  # "your developer token"
from client import *

import evernote.edam.notestore.NoteStore as NoteStore
import os
import enmltohtml
import helpers
import datetime

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x


from bs4 import BeautifulSoup

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


def insertNoteInfoTagsForNote(note, notebook, soup):
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

    tagNames = client.get_note_store().getNoteTagNames(client.token, note.guid)
    if tagNames:
        tags = ", ".join(tagNames)
        subheaditems += divstrtemp % ("Tags", tags)

    divSoup = BeautifulSoup(subheaditems)
    soup.h1.insert_after(divSoup.body)

    return soup


OUTPUT_FOLDER = "/Users/bryan/Desktop/EvernoteExport"

# "https://sandbox.evernote.com/shard/s1/notestore"

def get_notebooks(client):
    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()
    return {n.name: n for n in notebooks}

def filter_noteboooks_by_stack(notebooks, matchString):
    stackbooks = {key: value for key, value in notebooks.items() if value.stack is not None and matchString in value.stack}
    return stackbooks



client = getDevClientInstance(auth_token)
note_store = client.get_note_store()
notebooks = get_notebooks(client)
stackbooks = filter_noteboooks_by_stack(notebooks, "Test")


for key in stackbooks:
    notebook = stackbooks[key]
    notebookDirectory = os.path.join(OUTPUT_FOLDER, notebook.name)
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

    noteList = note_store.findNotes(client.token, filter, 0, 9999)
    notes = []

    for note in noteList.notes:
        content = note_store.getNoteContent(note.guid)
        noteResourceDir = os.path.join(notebookDirectory, (note.title + "-resources/"))
        mediaStore = enmltohtml.FileMediaStore(note_store, note.guid, noteResourceDir)
        html = enmltohtml.ENMLToHTML(content=content, pretty=True, header=False, media_store=mediaStore)

        soup = BeautifulSoup(PAGE_BASE_LAYOUT)
        soup.title.string = note.title
        soup.h1.string = note.title
        soup = insertNoteInfoTagsForNote(note, notebook, soup)

        divNote = soup.find(id="end-note-content")

        soupNoteHTML = BeautifulSoup(html)

        for element in soupNoteHTML.body:
            divNote.insert_before(element)

        html = soup.prettify(formatter="html")

        outfile = helpers.export_html_file(path=notebookDirectory, basename=note.title, html=html, encoding=None)
        print "Published " + note.title + " to " + outfile
