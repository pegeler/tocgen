#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make Tables of Contents

Generates a Table of Contents for Markdown and HTML documents. The table will
be output to STDOUT or to file.

This is non-production software that is somewhat fragile. User input is not
carefully validated. Suggested usage is in interactive workflows when editing
your own documents. Use at your own risk.
"""
import abc
import argparse
from collections.abc import Iterator
from collections.abc import Iterable
from collections import Counter
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import os.path
import re
import sys

__version__ = '1.0.0'


@dataclass
class TocEntry:
    depth: int
    heading: str
    link: str


class BaseSimpleDocumentParser(abc.ABC):

    @abc.abstractmethod
    def parseFile(self, infile) -> list[TocEntry]:
        raise NotImplementedError


class SimpleHtmlParser(HTMLParser, BaseSimpleDocumentParser):
    headings: list[TocEntry]
    _depth: int
    _heading: str
    _link: str

    RE_HEADING = re.compile(r'^h(\d+)$', re.I)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.headings = []
        self._in_heading_tag = False
        self._heading = ''

    def handle_starttag(self, tag, attrs):
        if not self._in_heading_tag and (h := self.RE_HEADING.match(tag)):
            self._in_heading_tag = True
            self._depth = int(h.group(1)) - 1
            for attr in attrs:
                if attr[0] == 'id':
                    self._link = attr[1]
            else:
                self._link = ''

    def handle_endtag(self, tag):
        if self._in_heading_tag and self.RE_HEADING.match(tag):
            self._in_heading_tag = False
            self.headings.append(TocEntry(self._depth, self._heading, self._link))
            self._heading = ''

    def handle_data(self, data):
        if self._in_heading_tag:
            self._heading += data.replace('\n', '')

    def parseFile(self, infile) -> list[TocEntry]:
        with open(infile, 'rt') as fh:
            self.feed(fh.read())
        return self.headings


class SimpleMarkdownParser(BaseSimpleDocumentParser):
    FENCE = '```'
    RE_CAPTURE = re.compile('^(#+)(.*)$')
    RE_HTML_COMMENT = re.compile(r'<!--.*?-->', flags=re.S)  # Non-greedy match
    RE_SPECIALS = re.compile(r'''[!@#$%^&*()+;:'"\[\]{}|\\<>,./?`~]''')

    def _open_with_stripped_html_comments(self, filename: str) -> Iterator[str]:
        with open(filename) as f:
            yield from self.RE_HTML_COMMENT.sub('', f.read()).split('\n')

    def parseFile(self, infile) -> list[TocEntry]:
        in_fence = False
        links = Counter()
        headings = []

        for line in self._open_with_stripped_html_comments(infile):
            if line.startswith(self.FENCE):
                in_fence = not in_fence
                continue

            if in_fence or not (m := self.RE_CAPTURE.match(line)):
                continue

            depth = len(m.group(1)) - 2
            heading = m.group(2).strip()
            if depth < 0:
                sys.stderr.write(f'Top level headings are ignored. '
                                 f'Skipping {heading}\n')
                continue

            link = self.RE_SPECIALS.sub('', heading.lower().replace(' ', '-'))
            n_links = links[link]
            links[link] += 1
            if n_links:
                link = f'{link}-{str(n_links)}'

            headings.append(TocEntry(depth, heading, link))

        return headings


class BaseTocGenerator(abc.ABC):
    PARSERS = {
        '.md': SimpleMarkdownParser().parseFile,
        '.html': SimpleHtmlParser().parseFile,
    }

    def __init__(self, infile, indent=4, outfile=None):
        self.infile = infile
        self.indent = indent
        self.outfile = outfile

        _, ext = os.path.splitext(infile.lower())
        try:
            parser = self.PARSERS[ext]
        except KeyError:
            raise ValueError(f'Infile format {ext} not recognized')

        self.headings = parser(infile)

    def write(self):
        s = self.generateString()
        if self.outfile:
            with open(self.outfile, 'wt') as fh:
                fh.write(s + '\n')
        else:
            print(s)

    @abc.abstractmethod
    def generateString(self) -> str:
        raise NotImplementedError


class MarkdownTocGenerator(BaseTocGenerator):

    def generateString(self) -> str:
        lines = ['## Table of Contents', '']
        for heading in self.headings:
            pad = heading.depth * self.indent * " "
            lines.append(f'{pad}* [{heading.heading}](#{escape(heading.link)})')
        return '\n'.join(lines)


class HtmlTagGenerator:
    def __init__(self, tags: Iterable[str]):
        self.__dict__.update(**{t: self._htmlTagGenerator(t) for t in tags})

    @staticmethod
    def _htmlTagGenerator(tag):
        def html_tag(content, attrs=None):
            attr_gen = (f'{k}="{v}"' for k, v in attrs or ())
            return f'<{tag} {" ".join(attr_gen)}>' + content + f'</{tag}>'
        return html_tag


class HtmlTocGenerator(BaseTocGenerator):

    def generateString(self) -> str:
        ...

    _wrapInTag = HtmlTagGenerator(['h2', 'ul', 'li', 'a'])


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        '-i', '--indent',
        dest='indent',
        type=int,
        default=4,
        help='The width of indentation.')
    p.add_argument(
        '-f', '--format',
        dest='format',
        default='markdown',
        choices=['markdown', 'html'],
        help='The output format. (default: %(default)s)')
    p.add_argument(
        '-o', '--outfile',
        dest='outfile',
        help='A file to write output. Writes to STDOUT if not specified.')
    p.add_argument(
        'file',
        help='The input file.')

    return p.parse_args(argv)


def main():
    args = parse_args()
    match args.format:
        case 'markdown':
            toc_generator = MarkdownTocGenerator
        case 'html':
            toc_generator = HtmlTocGenerator
        case _:
            raise ValueError('Unknown format')

    toc_generator(args.file, args.indent, args.outfile).write()


if __name__ == "__main__":
    main()
