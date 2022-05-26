import lxml.etree as etree
from lxml.etree import XML, XSLT, parse
import re
import html.entities

TEMPLATE = """
    <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
        <xsl:template match="/">

            <my_tag>
                <xsl:value-of select="/outer/inner/text()" />
            </my_tag>

        </xsl:template>
    </xsl:stylesheet>
"""

DATA = """
    <outer>
        <inner>Hello World</inner>
    </outer>
"""

_entities_re = re.compile(r"&(\w+);")


def resolve_entities(s):
    # Replace all &nbsp; entities with their unicode equivalents
    return _entities_re.sub(
        lambda m: html.entities.entitydefs.get(m.group(1), m.group(1)), s
    )


def transform_enml(content, outfile):
    # from xul.xsl import build_xsl_transform, xml_transformer
    # from xul.cmd.xp import XMLParser
    # from xul.cmd.transform import print_function
    # from xul.ppxml import pp_xml, prettyprint

    TRANSFORMFILE = "./enml2html.xslt"

    #
    # transformer = build_xsl_transform(TRANSFORMFILE)
    # parser = XMLParser()
    #
    # result = xml_transformer(content, transformer, parser)
    #
    # prettyprint(result)
    # exit()
    enml_parser = etree.ETCompatXMLParser(load_dtd=False, no_network=True, resolve_entities=False, recover=True)
    data = parse(content, parser=enml_parser)

    with open(TRANSFORMFILE, "r") as fp:
        template = fp.read()

    transform = XSLT(XML(template, parser=enml_parser))

    result = transform(data)

    with open(outfile + ".html", "w") as fpout:
        fpout.write(result)

    return result


def find_all_tags(fp, tags, progress_callback=None):
    parser = etree.XMLPullParser(("start", "end"))
    root = None
    while True:
        chunk = fp.read(1024 * 1024)
        if not chunk:
            break
        parser.feed(chunk)
        for event, el in parser.read_events():
            if event == "start" and root is None:
                root = el
            if event == "end" and el.tag in tags:
                yield el.tag, el
            root.clear()
        if progress_callback is not None:
            progress_callback(len(chunk))


def wrap_outer_enex(title, body):
    return f'<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE en-export SYSTEM \"http://xml.evernote.com/pub/evernote-export3.dtd\">\n<en-export export-date=\"20161017T021119Z\" application=\"NotePublisher\"><note>\n<title>{title}</title>\n<content><![CDATA[{body}]]></content>\n</note>\n</en-export>'
