#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""Export OFFO German hyphenation rules  to thrax file"""

import sys
import os
import re
import argparse
import zipfile
import xml
import xml.sax
import xml.etree.ElementTree as ET


class HyphenMin:
    """Abstraction of hyphen minimum parameters."""
    def __init__(self, root: ET.Element):
        elem = root.find('hyphen-min')
        if elem is not None:
            self.before = self.get_int_attribute(elem, 'before')
            self.after = self.get_int_attribute(elem, 'after')
    
    def get_int_attribute(self, elem: ET.Element, attr: str):
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
        xmldata = offozip.read('offo-hyphenation/hyph/de.xml')
    root = ET.fromstring(xmldata.decode('iso-8859-1'))
    hyphen_min = HyphenMin(root)
    exceptions = Exceptions(root)
    patterns = Patterns(root)
    return hyphen_min, exceptions, patterns


def convert_to_symbols(s: str) -> str:
    """Convert input characters to symbols."""
    return s.replace('ä', 'A').replace('ö', 'O').replace('ü', 'U').replace('å', 'N').replace('ß', 'S')


def thraxified_context(ctx: str) -> str:
    if len(ctx) >= 5 and ctx.startswith('[BOS]'):
        bos = '"[BOS]" '
        ctx = ctx[5:]
    else:
        bos = ''
    if len(ctx) >= 5 and ctx.endswith('[EOS]'):
        eos = ' "[EOS]"'
        ctx = ctx[:-5]
    else:
        eos = ''
    syms = []
    for c in ctx:
        if c == '-':
            syms.append('hyph')
        else:
            syms.append('"{}".symtab'.format(c))
    if ctx == '':
        syms.append('""')
    return bos + ' '.join(syms) + eos


def save_thrax_file(args: argparse.Namespace, hm: HyphenMin, ex: Exceptions, pt: Patterns):
    # Split patterns so they contain only one hyphenation point and order them by ascending priority
    rewrites = [[] for i in range(10)]
    #digits = [0] * 10
    for pattern in pt.patterns:
        pattern = convert_to_symbols(pattern)
        last_pos = len(pattern)-1
        last_letter_pos = None
        for i in range(last_pos, -1, -1):
            if pattern[i].isalpha():
                last_letter_pos = i
                break
        min_hyph_pos = 0
        alpha_index = 0
        if pattern[0] == '.':
            for i in range(len(pattern)):
                if pattern[i].isalpha():
                    if alpha_index < hm.before:
                        alpha_index += 1
                    else:
                        min_hyph_pos = i
                        break
        max_hyph_pos = last_pos
        alpha_index = 0
        if pattern[last_pos] == '.':
            for i in range(last_pos, -1, -1):
                if pattern[i].isalpha():
                    if alpha_index < hm.after:
                        alpha_index += 1
                    else:
                        max_hyph_pos = i
                        break
        hyphpoints = [(i, int(c)) for i, c in enumerate(pattern) if c.isdigit()]
        for point, point_value in hyphpoints:
            lctx = []
            rctx = []
            for i in range(point):
                c = pattern[i]
                if c.isdigit():
                    continue
                if c == '.':
                    lctx.append('[BOS]')
                else:
                    lctx.append(c)
                    if i < point - 1 and i >= min_hyph_pos:
                        lctx.append('-')
            for i in range(point+1, len(pattern)):
                c = pattern[i]
                if c.isdigit():
                    continue
                if c == '.':
                    rctx.append('[EOS]')
                else:
                    rctx.append(c)
                    if i < last_letter_pos and i < max_hyph_pos:
                        rctx.append('-')
            #print('{} {} {}'.format(''.join(lctx), pattern[point], ''.join(rctx)))
            rewrites[point_value].append((''.join(lctx), ''.join(rctx)))
        #digits[sum(c.isdigit() for c in pattern)] += 1
    #print(digits)
    #print(rewrites)
    #for l in rewrites:
    #    print(len(l))
    print('symtab = SymbolTable[\'hyph-de.sym\'];', file=args.thraxfile)
    print('ConvIn = StringFile[\'hyph-de-in.tsv\', \'utf8\', symtab];', file=args.thraxfile)
    print('ConvOut = StringFile[\'hyph-de-out.tsv\', symtab, \'byte\'];', file=args.thraxfile)
    print('', file=args.thraxfile)
    print('hyph = "-".symtab ?;', file=args.thraxfile)
    print('sigma = StringFile[\'hyph-de-sigma.txt\', symtab];', file=args.thraxfile)
    print('sigmastar = sigma*;', file=args.thraxfile)
    print('export HYPHENATE = Optimize[ConvIn @', file=args.thraxfile)
    for priority, contexts in enumerate(rewrites):
        for lctx, rctx in contexts:
            rewrite = '"-": ""' if priority % 2 == 0 else '"": "-"'
            lcs = thraxified_context(lctx)
            rcs = thraxified_context(rctx)
            print('    CDRewrite[{}, {}, {}, sigmastar] @'.format(rewrite, lcs, rcs), file=args.thraxfile)
    print('    ConvOut];', file=args.thraxfile)


def main():
    argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('offofile', type=argparse.FileType('rb'), help='Zip archive of OFFO hyphenations')
    argparser.add_argument('thraxfile', type=argparse.FileType('w', encoding='utf-8'), help='Resulting OpenGRM Thrax source')
    args = argparser.parse_args()
    hyphen_min, exceptions, patterns = load_offo_file(args)
    save_thrax_file(args, hyphen_min, exceptions, patterns)


if __name__ == "__main__":
    main()
