#!/bin/python
# -*- coding: utf-8 -*-

__name__ = "NotePublisher"
import os
import helpers
import datetime
import bs4 as BeautifulSoup
import mimetypes
from base64 import b64encode

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x
import hashlib


def scrubPathPart(pathpart, lowercase=False):
    assert (pathpart)

    for c in r'[]/\;,><&*:%=+@!#^()|?^':
        pathpart = pathpart.replace(c, u'')

    pathpart = pathpart.replace(u' ', u'_')

    if lowercase:
        pathpart = pathpart.lower()

    return pathpart


PAGE_BASE_LAYOUT = """
<HTML>
<HEAD>
<!-- exported by Note Publisher - https://github.com/selner/NotePublisher --></BODY>
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

.document-heading{
    color: #4a4a4a;
    font-family: gotham, helvetica, arial, sans-serif;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
}

.metafact {
    white-space: no-wrap;
    display: inline-flex;
    margin-right: 15px;
}
.metafact .heading {
    margin-right: 8px;
    color: #878787;
    -webkit-font-smoothing: antialiased;
    font-family: gotham, helvetica, arial, sans-serif;
    font-size: 11px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.metafact .value {
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
}

body {
  padding: 3em;
}

.document-item {
  display: block;
  margin: 1.5em 0 2.5em 0;
  position: relative;
  padding-left: 45px;
  color: #4a4a4a;
}
.document-item::before {
  position: absolute;
  width: 29px;
  height: 34px;
  left: 0;
  top: -7px;
  content: '';
  border: solid 1px #878787;
}
.document-item::after {
  content: 'file';
  content: attr(filetype);
  left: -4px;
  padding: 0px 2px;
  text-align: right;
  line-height: 1.3;
  position: absolute;
  background-color: #28a956;
  color: #fff;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  top: 10px;
}
.document-item .fileCorner {
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 12px 0 0 11px;
  border-color: white transparent transparent #878787;
  position: absolute;
  top: -8px;
  left: 22px;
}

</STYLE>
</HEAD>
<BODY>
<H1 id="note-heading" style="margin-bottom: 5px;"></H1>
<HR/><DIV id="note-content">%s</DIV>
</HTML>

"""

import requests


def getDirectory(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def _getNotebookExportDirectory(output_folder, notebook, typeSubfolder = ""):
    if typeSubfolder:
        output_folder = os.path.join(output_folder, typeSubfolder)

    notebookDirectory = output_folder

    if notebook.stack:
        notebookstack = scrubPathPart(notebook.stack, lowercase=False)
        notebookDirectory = os.path.join(notebookDirectory, notebookstack)

    notebookname = scrubPathPart(notebook.name, lowercase=False)
    notebookDirectory = os.path.join(notebookDirectory, notebookname)

    return getDirectory(notebookDirectory)


class NoteExport(object):
    _note = None
    _notebook = None
    _client = None
    
    def __init__(self, client, outputFolder=None, resourceUriPrefix=None, noteMetadata=None, note=None, notebook=None,
                 tags=None, formats=[]):
        self._client = client
        self.resourceUriPrefix = resourceUriPrefix
        self._note = note
        self.oauth_token = client.token
        self.noteMetadata = noteMetadata
        self._notebook = notebook
        self.tags = tags
        self.output_folder = outputFolder
        self.note_resources_by_hash = {}
        self.formats = formats

    @property
    def client(self):
        return self._client

    @property
    def notestore(self):
        return self._client.note_store

    @property
    def notebook(self):

        return self._notebook

    @property
    def title(self):
        return self.noteMetadata.title

    @property
    def filename(self):
        return scrubPathPart(self.noteMetadata.title, lowercase=True)

    @property
    def note(self):
        if not self._note and self.noteMetadata:
            try:
                # self.note = self.note_store.getNote(guid=noteMetadata.guid, withContent=1, withResourcesData=1, withResourcesRecognition=0, withResourcesAlternateData=0)
                self._note = self.client.note_store.getNote(self.oauth_token, self.noteMetadata.guid, True, True, False, False)
            except Exception as e:
                helpers.reRaiseException(f'!!!!!! ERROR:  Failed to export note {self.noteMetadata.title} due to error: {e}')

        return self._note

    @note.setter
    def note(self, value):
        self._note = value


    def _getFilePathForResource(self, resource, output_parent_folder):

        # To display the Resource as part of the note's content, include an <en-media>
        # tag in the note's ENML content. The en-media tag identifies the corresponding
        # Resource using the MD5 hash.

        if "fileName" in resource.attributes.__dict__ and resource.attributes.__dict__["fileName"]:
            filename = resource.attributes.__dict__["fileName"]

        else:
            fileext = mimetypes.guess_extension(resource.mime, strict=False)
            if fileext is None:
                fileext = "." + resource.mime.split("/")[1]
            if fileext.startswith(u'.jpe'):
                fileext = ".jpg"
            filename = "%s%s" % (resource.guid, fileext)

        noteResourceDir = getDirectory(os.path.join(output_parent_folder, (self.filename + "-resources/")))
        file_path = os.path.join(noteResourceDir, filename)

        if len(file_path) > os.pathconf(self.output_folder, "PC_NAME_MAX"):
            file_path = os.path.join(noteResourceDir,
                                     os.path.splitext(filename)[0][0:8] + os.path.splitext(filename)[1])

        return file_path

    def export(self):

        try:

            output_folder = _getNotebookExportDirectory(self.output_folder, self.notebook, "enex")

            if self.formats == [] or "enex" in self.formats:
                self._export_enex(self.note)

            if self.formats == [] or "html" in self.formats:
                self.xmltransform()
                self._export_html(self.note)

        except Exception as e:
            print(f'Unable to save note {self.note.title} due to error:  {e}')
            pass

    def _addAttributeDivTag(self, soup, parentTag, heading, value):

        newdiv = soup.new_tag("div")
        newdiv["class"] = "metafact"
        parentTag.append(newdiv)

        newSpan = soup.new_tag("span")
        newSpan["class"] = "metafact heading"
        newSpan.string = heading
        newdiv.append(newSpan)

        newSpanVal = soup.new_tag("span")
        newSpanVal["class"] = "metafact value"
        newSpanVal.string = value
        newdiv.append(newSpanVal)

        return parentTag

    def _insertMetadataFactsToHTML(self, soupNote):
        attr = self.note.attributes.__dict__
        if not soupNote.head:
            soupNote.body.insert_before(soupNote.new_tag(u'head'))

        parentDiv = soupNote.new_tag(u'div')
        parentDiv.attrs["id"] = "note-metadata"
        soupNote.body.append(parentDiv)

        # strFactsHTML = ""

        try:
            for key in attr:
                if attr[key] is not None and attr[key] != 0:
                    key = escape(key)
                    value = escape(attr[key])
                    metatag = soupNote.new_tag(u'meta')
                    metatag.attrs['content'] = value
                    metatag.attrs['name'] = key
                    soupNote.head.append(metatag)

                    parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading=key, value=value)
        except Exception as e:
            helpers.reRaiseException(
                "!!!!!! ERROR:  Failed to export metadata for note '$s' due to error: " % self.noteMetadata.title, e)

        try:
            tagNames = []
            for t in self.note.tags:
                tagNames.append(self.tags[t])
            if tagNames and tagNames.count > 0:
                parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading="Tags",
                                                     value=", ".join(tagNames))
        except Exception:
            pass

        now = datetime.datetime.now()
        nowstr = now.strftime("%x %X")
        parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading="Exported", value=nowstr)
        # divNote.insert(0, divAttr)

        parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading="Notebook",
                                             value=self.notebook.name)
        # divNote.insert(0, divAttr)



        # parentDiv.insert_before(soupNote.body)
        #
        soupNote.body.append(parentDiv)

        return soupNote

    def _wrap_outer_enex(self, title, body):
        return f'<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE en-export SYSTEM \"http://xml.evernote.com/pub/evernote-export3.dtd\">\n<en-export export-date=\"20161017T021119Z\" application=\"NotePublisher\"><note>\n<title>{title}</title>\n<content><![CDATA[{body}]]></content>\n</note>\n</en-export>'

    def _export_enex(self, note):
        output_folder = _getNotebookExportDirectory(self.output_folder, self.notebook, "enex")

        try:
            enex_content = self.client.note_store.getNoteContent(self.oauth_token, self.noteMetadata.guid)

            # get resources of the note
            noteExport = self.note
            enexContent = f'<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE en-export SYSTEM \"http://xml.evernote.com/pub/evernote-export3.dtd\">\n<en-export export-date=\"20161017T021119Z\" application=\"NotePublisher\">\n' \
                          '<note>\n<title>{self._note.title}</title>\n<content><![CDATA[{noteExport.content}]]></content>\n'
            import re
            if noteExport.resources:
                for r in noteExport.resources:

                    resource = self.notestore.getResource(r.guid, True, False, True, False)
                    filepath = os.path.join(self.output_folder, f'resource_{r.guid}')
                    with open(filepath, 'wb') as out_file:
                        from shutil import copyfileobj
                        out_file.write(resource.data.body)
                    resbody = b64encode(resource.data.body)
                    xml = '\n<resource>\n<data encoding="base64">' + resbody.decode() + '</data>\n<mime>' + resource.mime + '</mime>\n</resource>'
                    enexContent = enexContent + xml
            enexContent = enexContent + "\n</note>\n</en-export>"

            outfile = helpers.save_text_file(path=output_folder, ext='enex', basename=self.filename,
                                             textdata=enex_content, encoding='utf-8')
            print("Published " + note.title + " to " + outfile)

        except Exception as e:
            helpers.reRaiseException(f'!!!!!! ERROR:  Failed to export note \'{ note.title }\' due to error:  {e}')

    def _downloadResource(self, resource, filepath=None):
        url = f'{self.resourceUriPrefix}/{resource.guid}'

        if not filepath:
            filepath = os.path.join(self.output_folder, f'resource{resource.guid}')


        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
        try:
            if resource.data.body:
                data = resource.data.body
        except:
            res_url = self.resourceUriPrefix + resource.guid
            try:
                response = requests.post(url=res_url, auth=self.oauth_token)
                data = response.content
            except Exception as e:
                print(e)
                from helpers import reRaiseException
                reRaiseException(e)
                # print(f'!!!!! Error:  Failed download resource from Evernote.  URL: {res_url}  Message:  {e}')

        response = requests.post(url=url, auth=self.oauth_token)
        if response.code == 200:
            data = response.content
            with open(filepath, 'wb') as out_file:
                from shutil import copyfileobj
                copyfileobj(data, out_file)
        else:
            raise Exception(f'Unable to download {url} to {filepath}:  {response}')

    def _exportResourcesForHTML(self, note, output_parent_folder):
        if note is None:
            note = self.note
        note_resources_by_hash = {}

        try:
            if note.resources and len(note.resources) > 0:
                for i in range(0, len(note.resources)):
                    resource = note.resources[i]

                    data = None
                    try:
                        if resource.data.body:
                            data = resource.data.body
                    except:
                        res_url = self.resourceUriPrefix + resource.guid
                        try:
                            response = requests.post(url=res_url, auth=self.oauth_token)
                            data = response.content
                        except Exception as e:
                            print (f'!!!!! Error:  Failed download resource from Evernote.  URL: {res_url}  Message:  {e}')
                            continue

                    # calculate hashcode for media
                    md5 = hashlib.md5()
                    md5.update(data)
                    hashcode = md5.hexdigest()

                    file_path = self._getFilePathForResource(resource, output_parent_folder)
                    f = open(file_path, "w")
                    f.write(data)
                    f.close()

                    note_resources_by_hash[hashcode] = resource
                return note_resources_by_hash

        except Exception as e:
            helpers.reRaiseException("Failed to export resource files for note %s.  Error:  " % self.note.title, e)

    def _export_html(self, note):

        try:
            output_folder = _getNotebookExportDirectory(self.output_folder, self.notebook, "html")
            resourcesByHash = {}
            if note.resources:
                try:
                    resourcesByHash = self._exportResourcesForHTML(note, output_folder)
                except Exception as e:
                    helpers.reRaiseException("Unable to export resources for note due to error:", e)

            soupExport = BeautifulSoup.BeautifulSoup(PAGE_BASE_LAYOUT, "lxml")
            soupExport.title.string = self.noteMetadata.title
            soupExport.h1.string = self.noteMetadata.title

            try:

                soupNoteHTML = BeautifulSoup.BeautifulSoup(note.content, "lxml")
                soupNoteHTML = self._insertMetadataFactsToHTML(soupNote=soupNoteHTML)

                # resources = set(self.note.resources.all())
                # print unicode(soupNoteHTML)
                # for mediatag in soupNoteHTML.findAll('en-media'):
                #     for res in resources:
                #         if res.hash == mediatag['hash']:
                #             mime_type = mediatag['type']
                #             if mime_type.startswith('image/'):
                #                 img = BeautifulSoup.Tag(soupNoteHTML, 'img')
                #                 img['height'] = mediatag.get('height', 450)
                #                 img['width'] = mediatag.get('width', 600)
                #                 img['src'] = res.file.url
                #                 mediatag.replaceWith(img)
                #

                all_media = soupNoteHTML.find_all(u'en-media')
                for mediatag in all_media:
                    media_type = mediatag['type'].split("/")[0]
                    if media_type.lower() == "image":
                        new_tag = soupNoteHTML.new_tag(u'img')
                        new_tag['src'] = self._getFilePathForResource(resourcesByHash[mediatag["hash"]], output_folder)
                        mediatag.replace_with(new_tag)
                    # elif media_type.lower() != "image":
                    #     new_tag = soupNoteHTML.new_tag(u'img')
                    #     new_tag['src'] = self._getFilePathForResource(resourcesByHash[mediatag["hash"]])
                    #     mediatag.replace_with(new_tag)
                    #
                    # if media_type.lower() != "image":
                    else:
                        new_tag = soupNoteHTML.new_tag(u'div')
                        new_tag['class'] = "document-heading"
                        new_tag.string = "Attached document:  "

                        link_tag = soupNoteHTML.new_tag(u'a')
                        filepath = self._getFilePathForResource(resourcesByHash[mediatag["hash"]], output_folder)
                        link_tag['href'] = filepath
                        link_tag['class'] = "document-item"
                        link_tag['filetype'] = os.path.splitext(filepath)[1]

                        childspan = soupNoteHTML.new_tag(u'span')
                        childspan['class'] = "fileCorner"
                        link_tag.string = "%s" % os.path.basename(filepath)
                        link_tag.insert(0, new_child=childspan)
                        new_tag.insert(1, new_child=link_tag)

                        mediatag.replace_with(new_tag)

                tagContent = soupExport.find(id="note-content")
                import copy
                tagContent.replace_with(copy.copy(soupNoteHTML.body))

                try:
                    exportHTML = soupExport.prettify(formatter="html").encode(u'utf-8')
                    outfile = helpers.export_html_file(path=output_folder, basename=self.filename,
                                                       html=exportHTML, encoding='utf-8')
                    print("Published " + self.note.title + " to " + outfile)
                except UnicodeEncodeError as e:
                    helpers.reRaiseException("!!!!!! ERROR:  Failed to export note '%s' due to error: " % self.noteMetadata.title, e)

            except KeyError as e:
                helpers.reRaiseException(
                    "!!!!!! ERROR:  Unable to find attachment %s to export for note:" % self.noteMetadata.title, e)
                pass
        except Exception as e:
            helpers.reRaiseException(
                "!!!!!! ERROR:  Failed to export note '%s' due to error: " % self.noteMetadata.title, e)

