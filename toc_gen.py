#!/usr/bin/env python3
"""
Make Tables of Contents

Generates a Table of Contents for Markdown and HTML documents. Input and output
formats can be mixed and matched. The table can be output to STDOUT or written
to file.

It is also extensible to any additional format you might want to add by
subclassing the abstract base classes for parsing input files and generating
output tables.

This is non-production software that is somewhat fragile. User input is not
carefully validated. Suggested usage is in interactive workflows when editing
your own documents. Use at your own risk.
"""
import abc
import argparse
import os.path
import re
import sys
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from itertools import groupby
from typing import Callable
from typing import Optional

__version__ = '1.0.0'

HtmlTagAttrs = list[tuple[str, str]]


@dataclass
class TocEntry:
    depth: int
    heading: str
    link: str


class BaseSimpleDocumentParser(abc.ABC):
    """
    Abstract base class for parsing document headings into a collection of
    entries. A subclass of the BaseTocGenerator can use those entries to
    generate a table of contents string.
    """

    @abc.abstractmethod
    def parseFile(self, infile) -> list[TocEntry]:
        """
        Parse a file to create a list of TocEntries

        :param str infile: The file to parse.
        """
        raise NotImplementedError


class SimpleHtmlParser(HTMLParser, BaseSimpleDocumentParser):
    """
    A parser that will generate a list of TOC entries from heading nodes,
    (*e. g.*, '<h2>Foo</h2>', '<h3>Bar</h3>') in an HTML documet.

    :ivar entries: A list of TOC entries from the most recently parsed file.
    """
    entries: list[TocEntry]
    _depth: int
    _heading: str
    _link: str

    RE_HEADING = re.compile(r'^h(\d+)$', re.I)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reset()

    def _reset(self):
        self.entries = []
        self._resetTagVariables()

    def _resetTagVariables(self):
        self._in_heading_tag = False
        self._heading = ''

    def handle_starttag(self, tag, attrs):
        if not self._in_heading_tag and (h := self.RE_HEADING.match(tag)):
            self._in_heading_tag = True
            self._depth = int(h.group(1)) - 1
            for attr in attrs:
                if attr[0] == 'id':
                    self._link = attr[1]
                    break
            else:
                self._link = ''

    def handle_endtag(self, tag):
        if self._in_heading_tag and self.RE_HEADING.match(tag):
            self.entries.append(TocEntry(self._depth, self._heading, self._link))
            self._resetTagVariables()

    def handle_data(self, data):
        if self._in_heading_tag:
            self._heading += data.replace('\n', '')

    def parseFile(self, infile) -> list[TocEntry]:
        self._reset()
        with open(infile, 'rt') as fh:
            self.feed(fh.read())
        return self.entries


class SimpleMarkdownParser(BaseSimpleDocumentParser):
    """
    A parser that will create a list of TOC entries from heading lines
    (*e. g.*, '## Foo', '### Bar') in a Markdown document. Note that top level
    headings ('# Main title') will be ignored.
    """

    FENCE = '```'
    RE_CAPTURE = re.compile('^(#+)(.*)$')
    RE_HTML_COMMENT = re.compile(r'<!--.*?-->', flags=re.S)  # Non-greedy match
    RE_SPECIALS = re.compile(r'''[!@#$%^&*()+;:'"\[\]{}|\\<>,./?`~]''')

    def _openWithStrippedHtmlComments(self, filename: str) -> Iterator[str]:
        with open(filename) as f:
            yield from self.RE_HTML_COMMENT.sub('', f.read()).split('\n')

    def parseFile(self, infile) -> list[TocEntry]:
        in_fence = False
        links = defaultdict(int)
        entries = []

        for line in self._openWithStrippedHtmlComments(infile):
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

            entries.append(TocEntry(depth, heading, escape(link)))

        return entries


class BaseTocGenerator(abc.ABC):
    """
    Abstract base class for generating a Table of Contents. Must be subclassed
    to generate a Table of Contents string for the corresponding output format.

    :cvar PARSERS: A dictionary of parsers for each input file format supported.
            The key is the extension and the value should be a subclass of
            BaseSimpleDocumentParser.
    """
    PARSERS: dict[str, Callable] = {
        '.md': SimpleMarkdownParser().parseFile,
        '.html': SimpleHtmlParser().parseFile,
    }

    def __init__(self, infile, indent=4, outfile=None):
        self.infile = infile
        self.indent = indent
        self.indent_str = indent * ' '
        self.outfile = outfile

        _, ext = os.path.splitext(infile.lower())
        try:
            parser = self.PARSERS[ext]
        except KeyError:
            raise ValueError(f'Infile format {ext} not recognized')

        self.entries = parser(infile)

    def write(self):
        """
        Write the Table of Contents to file or STDOUT.
        """
        s = self.generateString()
        if self.outfile:
            with open(self.outfile, 'wt') as fh:
                fh.write(s + '\n')
        else:
            print(s)

    @abc.abstractmethod
    def generateString(self) -> str:
        """
        Generate a Table of Contents string corresponding to the format.
        """
        raise NotImplementedError


class MarkdownTocGenerator(BaseTocGenerator):

    def generateString(self) -> str:
        lines = ['## Table of Contents', '']
        for entry in self.entries:
            pad = entry.depth * self.indent_str
            if entry.link:
                heading_str = f'[{entry.heading}](#{entry.link})'
            else:
                heading_str = entry.heading
            lines.append(f'{pad}* {heading_str}')
        return '\n'.join(lines)


class HtmlTagGenerator:
    """
    A variant of a SimpleNamespace that can be used to wrap strings in HTML
    tags. For example,

    >>> html_tags = HtmlTagGenerator(['h2', 'p', 'a'])
    >>> html_tags.h2('This is a heading')
    '<h2>This is a heading</h2>'
    >>> mylink = html_tags.a("mylink", attrs=[("href", "#somewhere-in-doc")])
    >>> html_tags.p(f'This is a link: {mylink}')
    '<p>This is a link: <a href="#somewhere-in-doc">mylink</a></p>'

    """
    # TODO: How do I type hint this? Modeled after SimpleNamespace.
    #   <https://docs.python.org/3/library/types.html#types.SimpleNamespace>

    def __init__(self, tags: Iterable[str]):
        """
        :param tags: The tags to be included. Accessed by dot notation.
        """
        self.__dict__.update(**{t: self.htmlTagGenerator(t) for t in tags})

    @staticmethod
    def htmlTagGenerator(tag):
        def html_tag(content, *, attrs=None, newline=False, indent=None):
            """
            :param str content: The content to be placed inside the tag.
            :param Optional[HtmlTagAttrs] attrs: The attributes to be inserted
                    into the tag.
            :param bool newline: Whether to add a newline between tags and
                    content.
            :param Optional[str] indent: Pad left the tags with this string.
            """
            attr_str = ' ' + ' '.join(f'{k}="{v}"' for k, v in attrs) if attrs else ''
            newline_str = '\n' if newline else ''
            indent_str = indent or ''
            return (indent_str +
                    f'<{tag}{attr_str}>' +
                    newline_str +
                    content +
                    newline_str +
                    indent_str +
                    f'</{tag}>')
        return html_tag


class HtmlTocGenerator(BaseTocGenerator):

    def generateString(self) -> str:
        return (self._wrapInTag.h2('Table of Contents') + '\n' +
                self._generateUlStr(self.entries, 0))

    def _generateUlStr(self, entries: list[TocEntry], depth: int) -> str:
        """
        Generate a string containing potentially nested unordered list (<ul>)
        nodes from a list of TOC entries.
        """
        output = []
        groups = groupby(entries, lambda x: x.depth == depth)
        for is_same_depth, entry_group in groups:
            if is_same_depth:
                for entry in entry_group:
                    li = self._wrapInTag.li(self._maybeWrapInLink(entry))
                    output.append((1 + depth) * self.indent_str + li)
            else:
                output.append(self._generateUlStr(entry_group, depth + 1))
        return self._wrapInTag.ul(
            '\n'.join(output), newline=True, indent=depth * self.indent_str)

    def _maybeWrapInLink(self, entry: TocEntry) -> str:
        """
        Create a string out of a TOC entry. If the entry contains a non-empty
        link attribute, it will be wrapped in an anchor tag (<a>).
        """
        if entry.link:
            attrs = [('href', f'#{entry.link}')]
            return self._wrapInTag.a(entry.heading, attrs=attrs)
        return entry.heading

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
