#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Export OFFO hyphenation rules of specified language to thrax file"""

import sys
import os
import re
import argparse
import zipfile
import xml
import xml.sax
import xml.etree.ElementTree as ET


# The configuration dictionary replace
CONFIG = {}


class Language:
    """Abstraction of a language."""
    def __init__(self, *args, **kwargs):
        raise NotImplementedError('Please derive your language form class Language')


class GermanLanguage(Language):
    def __init__(self):
        self.name = 'de'
        self.xml_charset = 'iso-8859-1'
        self.symbols = 'abcdefghijklmnopqrstuvwxyzAOUNS.-'
        self.inconv = {
            'A': 'a',
            'a': 'a',
            'Ä': 'A',
            'ä': 'A',
            'Ö': 'O',
            'ö': 'O',
            'Ü': 'U',
            'ü': 'U',
            'ß': 'S',
            '.': '.',
            '-': '-'
        }
        # Register itself
        CONFIG[self.name] = self


class HyphenMin:
    """Abstraction of hyphen minimum parameters."""
    def __init__(self, root: ET.Element):
        elem = root.find('hyphen-min')
        if elem is not None:
            self.before = self.get_attribute(elem, 'before')
            self.after = self.get_attribute(elem, 'after')
    
    def get_attribute(self, elem: ET.Element, attr: str):
        return int(elem.get(attr)) if attr in elem.attrib else None


class Hyphen:
    """Abstraction of a TeX hyphen, with all properties."""
    def __init__(self, pre=None, post=None, no=None):
        self.pre = pre
        self.post = post
        self.no = no

    def __repr__(self):
        return '<hyphen pre={} post={} no={} />'.format(self.pre, self.post, self.no)


class Exceptions:
    """Abstraction for all hyphenation exceptions."""
    def __init__(self, root: ET.Element):
        self.entries = []
        elem = root.find('exceptions')
        if elem is not None:
            rawtext = ET.tostring(elem).decode('utf-8')
            # A good Python XML SAX example: https://www.tutorialspoint.com/python3/python_xml_processing.htm
            parser = xml.sax.make_parser()
            parser.setFeature(xml.sax.handler.feature_namespaces, 0)
            exceptions_handler = ExceptionsHandler(self)
            xml.sax.parseString(rawtext, exceptions_handler)
            #print(self.entries)

    def add_entry(self, hyph_word: list):
        self.entries.append(hyph_word)


class ExceptionsHandler(xml.sax.ContentHandler):
    """SAX handler for the whole exceptions element."""
    def __init__(self, exceptions):
        self.exceptions = exceptions
        self.found_exceptions = False
        self.current_word = []

    def getAttribute(self, attributes, name):
        return attributes[name] if name in attributes else None

    def startElement(self, tag, attributes):
        if tag == 'hyphen':
            if not self.found_exceptions:
                raise xml.sax.SAXException('Found tags not with exceptions tag')
            pre = self.getAttribute(attributes, 'pre')
            post = self.getAttribute(attributes, 'post')
            no = self.getAttribute(attributes, 'no')
            self.current_word.append(Hyphen(pre=pre, post=post, no=no))
        elif tag == 'exceptions':
            self.found_exceptions = True

    def characters(self, content):
        syllables = content.split('-')
        for sy in syllables:
            if sy != '\n':
                self.current_word.append(sy)
            elif self.current_word:
                self.exceptions.add_entry(self.current_word)
                self.current_word = []


class Patterns:
    """Abstraction of patterns."""
    def __init__(self, root: ET.Element):
        elem = root.find('patterns')
        self.patterns = elem.text.split()


def load_offo_file(args: argparse.Namespace) -> tuple:
    with zipfile.ZipFile(args.offofile) as offozip:
        xmldata = offozip.read('offo-hyphenation/hyph/{}.xml'.format(args.language))
    root = ET.fromstring(xmldata.decode(CONFIG[args.language]['xml-charset']))
    hyphen_min = HyphenMin(root)
    exceptions = Exceptions(root)
    patterns = Patterns(root)
    return hyphen_min, exceptions, patterns


def save_thrax_file(args: argparse.Namespace, hm: HyphenMin, ex: Exceptions, pt: Patterns):
    # Split patterns so they contain only one hyphenation point and order them by ascending priority
    for pattern in pt.patterns:
        print(pattern)


def main():
    argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('offofile', type=argparse.FileType('rb'), help='Zip archive of OFFO hyphenations')
    argparser.add_argument('language', help='language name')
    argparser.add_argument('thraxfile', type=argparse.FileType('w', encoding='utf-8'), help='Resulting OpenGRM Thrax source')
    args = argparser.parse_args()
    if args.language not in CONFIG:
        print('Language "{}" is not configured'.format(args.language), file=sys.stderr)
        print('Please consult CONFIG dictionary at the top of the executed script', file=sys.stderr)
        sys.exit(1)
    hyphen_min, exceptions, patterns = load_offo_file(args)
    save_thrax_file(args, hyphen_min, exceptions, patterns)


if __name__ == "__main__":
    main()
