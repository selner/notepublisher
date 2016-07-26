#!/bin/python
# -*- coding: utf-8 -*-

__name__ = u"NotePublisher"
import os
import helpers
import datetime
import bs4 as BeautifulSoup
import mimetypes

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


PAGE_BASE_LAYOUT = u"""
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
<H1 id="note-heading" style=u"margin-bottom: 5px;"></H1>
<HR/><DIV id="note-content">%s</DIV>
</HTML>

"""

import requests

def getDirectory(dir):

    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def getNotebookDirectory(output_folder, notebook):
    notebookDirectory = os.path.join(output_folder, scrubPathPart(notebook.name, lowercase=False))
    return getDirectory(notebookDirectory)


class NoteExport(object):
    _note = None

    def __init__(self, client, outputFolder=None, resourceUriPrefix=None, noteMetadata=None, note=None, notebook=None, tags=None):
        self.resourceUriPrefix = resourceUriPrefix
        self._note = note
        self.oauth_token = client.token
        self.noteMetadata = noteMetadata
        self.notebook = notebook
        self.note_store = client.get_note_store()
        self.tags = tags
        self.output_folder = outputFolder
        self.note_resources_by_hash = {}

    @property
    def title(self):
        return self.noteMetadata.title

    @property
    def filename(self):
       return scrubPathPart(self.noteMetadata.title, lowercase=True)

    @property
    def note(self):
        if not self._note and self.noteMetadata:
            # self.note = self.note_store.getNote(guid=noteMetadata.guid, withContent=1, withResourcesData=1, withResourcesRecognition=0, withResourcesAlternateData=0)
            self._note = self.note_store.getNote(self.oauth_token, self.noteMetadata.guid, True, True, False, False)
        return self._note

    @note.setter
    def note(self, value):
        self._note = value


    def _getFilePathForResourceHashCode(self, resourceHash):

        resource = self.note_resources_by_hash[resourceHash]
        return self._getFilePathForResource(resource)


    def _getFilePathForResource(self, resource):

        # To display the Resource as part of the note's content, include an <en-media>
        # tag in the note's ENML content. The en-media tag identifies the corresponding
        # Resource using the MD5 hash.

        if "fileName" in resource.attributes.__dict__ and resource.attributes.__dict__["fileName"]:
            filename = resource.attributes.__dict__["fileName"]

        else:
            fileext = mimetypes.guess_extension(resource.mime, strict=False)
            if fileext is None:
                fileext = u"." + resource.mime.split(u"/")[1]
            if fileext.startswith(u'.jpe'):
                fileext = u".jpg"
            filename = u"%s%s" % (resource.guid, fileext)

        notebookDirectory = getNotebookDirectory(self.output_folder, self.notebook)
        noteResourceDir = getDirectory(os.path.join(notebookDirectory, (self.filename + u"-resources/")))
        file_path = os.path.join(noteResourceDir, filename)

        if len(file_path) > os.pathconf(self.output_folder, "PC_NAME_MAX"):
            file_path = os.path.join(noteResourceDir, unicode(os.path.splitext(filename)[0][0:8] + os.path.splitext(filename)[1]))

        return file_path

    def exportResources(self):
        try:
            if self.note.resources and self.note.resources.count > 0:
                for i in range(0, len(self.note.resources)):
                    resource = self.note.resources[i]

                    data = None
                    try:
                        if resource.data.body:
                            data = resource.data.body
                    except:
                        res_url = u"%s/%s" % (self.resourceUriPrefix, resource.guid)
                        try:
                            response = requests.post(url=res_url, auth = self.oauth_token )
                            data = response.content
                        except Exception, e:
                            print (u"!!!!! Error:  Failed download resource from Evernote.  URL: %s  Message:  %s" % (res_url, e.message))
                            continue


                    # calculate hashcode for media
                    md5 = hashlib.md5()
                    md5.update(data)
                    hashcode = md5.hexdigest()

                    file_path = self._getFilePathForResource(resource)
                    f = open(file_path, u"w")
                    f.write(data)
                    f.close()


                    self.note_resources_by_hash[hashcode] = resource
        except Exception, e:
            helpers.reRaiseException(u"Failed to export resource files for note %s.  Error:  " % self.note.title, e)

    def _addAttributeDivTag(self, soup, parentTag, heading, value):

        newdiv = soup.new_tag(u"div")
        newdiv["class"] = u"metafact"
        parentTag.append(newdiv)


        newSpan= soup.new_tag(u"span")
        newSpan["class"] = u"metafact heading"
        newSpan.string = heading
        newdiv.append(newSpan)

        newSpanVal = soup.new_tag(u"span")
        newSpanVal["class"] = u"metafact value"
        newSpanVal.string = value
        newdiv.append(newSpanVal)

        return parentTag

    def _insertMetadataFactsToHTML(self, soupNote):
        attr = self.note.attributes.__dict__
        if not soupNote.head:
            soupNote.body.insert_before(soupNote.new_tag(u'head'))

        parentDiv = soupNote.new_tag(u'div')
        parentDiv.attrs["id"]  = u"note-metadata"
        soupNote.body.append(parentDiv)

        # strFactsHTML = u""

        try:

            for key in attr:
                if attr[key] is not None and attr[key] != 0:
                    key = escape(unicode(key))
                    value = escape(unicode(attr[key]))
                    metatag = soupNote.new_tag(u'meta')
                    metatag.attrs['content'] = value
                    metatag.attrs['name'] = key
                    soupNote.head.append(metatag)

                    parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading=key, value=value)
        except Exception, e:
            helpers.reRaiseException(
                u"!!!!!! ERROR:  Failed to export metadata for note '$s' due to error: " % self.noteMetadata.title, e)

        try:
            tagNames = []
            for t in self.note.tags:
                tagNames.append(self.tags[t])
            if tagNames and tagNames.count() > 0:
                parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading=u"Tags", value=u", ".join(tagNames))
        except Exception:
            pass

        now = datetime.datetime.now()
        nowstr = now.strftime(u"%x %X")
        parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading=u"Exported", value=nowstr)
        # divNote.insert(0, divAttr)

        parentDiv = self._addAttributeDivTag(soup=soupNote, parentTag=parentDiv, heading=u"Notebook", value=self.notebook.name)
        # divNote.insert(0, divAttr)



        # parentDiv.insert_before(soupNote.body)
        #
        soupNote.body.append(parentDiv)

    def export(self):
        notebookDirectory = getNotebookDirectory(self.output_folder, self.notebook)
        outfilename = helpers.getOutFileName(basename=self.filename, ext=u"html")
        noteExportPath = os.path.join(notebookDirectory, outfilename)
        if not os.path.exists(noteExportPath):
        #
        #         mediaStore = enmltohtml.FileMediaStore(self.note_store, note.guid, noteResourceDir)
        #         html = enmltohtml.ENMLToHTML(content=note.content, pretty=True, header=False, media_store=mediaStore)
        #     except EvernoteTypes.EDAMSystemException, e:
        #         if e.errorCode == EvernoteTypes.EDAMErrorCode.RATE_LIMIT_REACHED:
        #             print "Rate limit reached.  Retry your request in %d seconds." % e.rateLimitDuration
        #         else:
        #             print "!!!!! Error:  Failed to access note via Evernote API.  Message:  %s" % (e.message)
        #         continue
        #     except EvernoteTypes.EDAMUserException, e:
        #         print "Invalid Evernote API request.  Please check the call parameters.  Message: %s" % (e.message)
        #         exit(-1)
        #     except Exception, e:
        #         print "!!!!! Error:  Failed to access note via Evernote API.  Message:  %s" % (e.message)
        #         exit(-1)
            soupNoteHTML = None
            soupExport = None
            soupENML = None

            try:
                if not self.note and self.noteMetadata:
                    # self.note = self.note_store.getNote(guid=noteMetadata.guid, withContent=1, withResourcesData=1, withResourcesRecognition=0, withResourcesAlternateData=0)
                    self.note = self.note_store.getNote(self.oauth_token, self.noteMetadata.guid, True, True, False, False)

                if self.note.resources:
                    try:
                        self.exportResources()
                    except Exception, e:
                        helpers.reRaiseException(u"Unable to export resources for note due to error:", e)


                soupExport = BeautifulSoup.BeautifulSoup(PAGE_BASE_LAYOUT, u"lxml", from_encoding=u"utf-8")
                soupExport.title.string = self.noteMetadata.title
                soupExport.h1.string = self.noteMetadata.title

                self._insertMetadataFactsToHTML(soupNote=soupExport)

                try:

                    soupNoteHTML = BeautifulSoup.BeautifulSoup(self.note.content, u"lxml", from_encoding=u"utf-8")
                    #
                    # resources = set(self.note.resources.all())
                    # print unicode(soupNoteHTML)
                    # for mediatag in soupNoteHTML.findAll('en-media'):
                    #     for res in resources:
                    #         if res.hash == mediatag['hash']:
                    #             mime_type = mediatag['type']
                    #             if mime_type.startswith('image/'):
                    #                 img = BeautifulSoup.Tag(soupENML, 'img')
                    #                 img['height'] = mediatag.get('height', 450)
                    #                 img['width'] = mediatag.get('width', 600)
                    #                 img['src'] = res.file.url
                    #                 mediatag.replaceWith(img)


                    all_media = soupNoteHTML.find_all(u'en-media')
                    for mediatag in all_media:
                        media_type = mediatag['type'].split(u"/")[0]
                        if media_type.lower() == u"image":
                            new_tag = soupNoteHTML.new_tag(u'img')
                            new_tag['src'] = self._getFilePathForResourceHashCode(resourceHash=mediatag["hash"])
                            mediatag.replace_with(new_tag)
                        else:
                            new_tag = soupNoteHTML.new_tag(u'div')
                            new_tag['class'] = u"document-heading"
                            new_tag.string = u"Attached document:  "

                            link_tag = soupNoteHTML.new_tag(u'a')
                            filepath = self._getFilePathForResourceHashCode(resourceHash=mediatag["hash"])
                            link_tag['href'] = filepath
                            link_tag['class'] = u"document-item"
                            link_tag['filetype'] = os.path.splitext(filepath)[1]

                            childspan = soupNoteHTML.new_tag(u'span')
                            childspan['class'] = u"fileCorner"
                            link_tag.string = u"%s" % os.path.basename(filepath)
                            link_tag.insert(0, new_child=childspan)
                            new_tag.insert(1, new_child=link_tag)

                            mediatag.replace_with(new_tag)

                except KeyError, e:
                    helpers.reRaiseException(u"!!!!!! ERROR:  Unable to find attachment %s to export for note:" % self.noteMetadata.title, e)
                    pass
                except Exception, e:
                    helpers.reRaiseException(u"!!!!!! ERROR:  Failed to export note '%s' due to error: " % self.noteMetadata.title, e)

                #                noteHtml = soupNoteHTML.prettify(formatter=u"html").encode(u'utf-8')

                tagContent = soupExport.find(id=u"note-content")
                import copy
                tagContent.replace_with(copy.copy(soupNoteHTML.body))
                exportHTML= soupExport.prettify(formatter=u"html").encode(u'utf-8')

                try:
                    outfile = helpers.export_html_file(path=notebookDirectory, basename=self.filename, html=exportHTML,
                                                       encoding='utf-8')
                    print(u"Published " + self.note.title + " to " + outfile)
                except (Exception, UnicodeEncodeError), e:
                    helpers.reRaiseException(u"!!!!!! ERROR:  Failed to export note '%s' due to error: " % self.noteMetadata.title, e)


            except Exception, e:
                helpers.reRaiseException(u"!!!!!! ERROR:  Failed to export note '%s' due to error:" % self.noteMetadata.title, e)

        else:
            print(u"Skipping previously exported note '%s'... " % (self.noteMetadata.title))
