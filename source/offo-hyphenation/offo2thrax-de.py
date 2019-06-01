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
import itertools


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


def save_thrax_file(args: argparse.Namespace, hm: HyphenMin, ex: Exceptions, pt: Patterns):
    # Write the alphabet
    print('ascii_letter = Optimize["a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" |', file=args.thraxfile)
    print('                        "n" | "o" | "p" | "q" | "r" | "s" | "t" | "u" | "v" | "w" | "x" | "y" | "z"];', file=args.thraxfile)
    print('letter = Optimize[ascii_letter | "A" | "O" | "U" | "N" | "S"];', file=args.thraxfile)
    print('sigma = Optimize[letter | "-" | "."];', file=args.thraxfile)
    # Write lowercase converter
    print('to_lowercase = Optimize[(ascii_letter | "ä".utf8 | "ö".utf8 | "ü".utf8 | "å".utf8 | "ß".utf8 |', file=args.thraxfile)
    print('                ("A": "a") | ("B": "b") | ("C": "c") | ("D": "d") | ("E": "e") | ("F": "f") |', file=args.thraxfile)
    print('                ("G": "g") | ("H": "h") | ("I": "i") | ("J": "j") | ("K": "k") | ("L": "l") |', file=args.thraxfile)
    print('                ("M": "m") | ("N": "n") | ("O": "o") | ("P": "p") | ("Q": "q") | ("R": "r") |', file=args.thraxfile)
    print('                ("S": "s") | ("T": "t") | ("U": "u") | ("V": "v") | ("W": "w") | ("X": "x") |', file=args.thraxfile)
    print('                ("Y": "y") | ("Z": "z") |', file=args.thraxfile)
    print('                ("Ä".utf8: "ä".utf8) | ("Ö".utf8: "ö".utf8) | ("Ü".utf8: "ü".utf8) | ("Å".utf8: "å".utf8))*];', file=args.thraxfile)
    # Write the converters from and to UTF-8
    print('from_utf8 = Optimize[(ascii_letter | ("ä".utf8: "A") | ("ö".utf8: "O") | ("ü".utf8: "U") | ("å".utf8: "N") | ("ß".utf8: "S"))*];', file=args.thraxfile)
    print('to_utf8 = Optimize[(ascii_letter | "-" | ("A": "ä".utf8) | ("O": "ö".utf8) | ("U": "ü".utf8) | ("N": "å".utf8) | ("S": "ß".utf8))*];', file=args.thraxfile)
    # Write the rewriting patterns
    def convert_to_ascii(s: str) -> str:
        return s.replace('ä', 'A').replace('ö', 'O').replace('ü', 'U').replace('å', 'N').replace('ß', 'S')
    def split_string_by_digit(s: str) -> list:
        l = []
        for c in s:
            if c.isdigit():
                l.append(c)
            else:
                if l and not l[-1][-1].isdigit():
                    l[-1] += c
                else:
                    l.append(c)
        return l
    def scored_rewrite(score: int) -> str:
        return '("-": "" <-{}>)?'.format(score) if score % 2 == 0 else '("": "-" <-{}>)'.format(score)
    def print_patterns_partition(rule_name: str, p: list):
        rule_start = rule_name + ' = Optimize['
        rule_body = ' |\n'.join(p)
        rule_end = '];'
        print('\n'.join([rule_start, rule_body, rule_end]), file=args.thraxfile)
    rewritten_patterns = []
    for pattern in pt.patterns:
        ss = split_string_by_digit(convert_to_ascii(pattern))
        l = [scored_rewrite(int(c)) if c.isdigit() else '"{}"'.format(c) for c in ss]
        #if ss[0].isdigit():  # Workaround against double hyphens
        #    l.insert(0, 'letter')
        rewritten_patterns.append('    {}'.format(' '.join(l)))
    # We must partition the patterns, because Thrax (v. 1.2.9) hit the limit at around 5000 patterns
    patterns_middle = int(len(rewritten_patterns) / 2)
    print_patterns_partition('patterns1', rewritten_patterns[:patterns_middle])
    print_patterns_partition('patterns2', rewritten_patterns[patterns_middle:])
    print('patterns = Optimize[patterns1 | patterns2];', file=args.thraxfile)
    # Define rules for adding and removing word boundaries
    print('add_bounds = Optimize[("": ".") sigma+ ("": ".")];', file=args.thraxfile)
    print('remove_bounds = Optimize[(".": "") sigma+ (".": "")];', file=args.thraxfile)
    # Define rules for hyphenation boundaries (at least 2 characters from word boundaries)
    print('remh = ("-": "")?;', file=args.thraxfile)
    print('min_hyphen = Optimize["." remh letter remh letter sigma+ letter remh letter remh "."];', file=args.thraxfile)
    print('reduce_hyphens = CDRewrite["-"+: "-", "", "", sigma*];', file=args.thraxfile)
    # Write exceptions
    print('exceptions = Optimize[(("backen": "bak-ken") | ("bettuch": "bett-tuch")) <-100>];', file=args.thraxfile)
    # Concatenate everything
    print('export HYPHENATE = Optimize[to_lowercase @ from_utf8 @ ', file=args.thraxfile)
    print('    ((add_bounds @ (patterns | sigma)* @ reduce_hyphens @ min_hyphen @ remove_bounds) | exceptions) @', file=args.thraxfile)
    print('    to_utf8];', file=args.thraxfile)


def main():
    argparser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument('offofile', type=argparse.FileType('rb'), help='Zip archive of OFFO hyphenations')
    argparser.add_argument('thraxfile', type=argparse.FileType('w', encoding='utf-8'), help='Resulting OpenGRM Thrax source')
    args = argparser.parse_args()
    hyphen_min, exceptions, patterns = load_offo_file(args)
    save_thrax_file(args, hyphen_min, exceptions, patterns)


if __name__ == "__main__":
    main()
