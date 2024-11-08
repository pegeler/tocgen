#!/usr/bin/env python3
"""
Make Tables of Contents

Generates a Table of Contents for Markdown and HTML documents. Input and output
formats can be mixed and matched. The table can be output to STDOUT or written
to file.

It is also extensible to any additional format you might want to add by
subclassing the abstract base classes for parsing input files and generating
output tables.

This is non-production software that is still under development. User input is
not carefully validated. Suggested usage is in interactive workflows when
editing your own documents. Use at your own risk.
"""
import abc
import argparse
import enum
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
from types import SimpleNamespace
from typing import Optional  # noqa
from typing import Protocol
from typing import Type

__version__ = '2.0.1'

HtmlTagAttrs = list[tuple[str, str]]


class OutputFormatExtension(enum.Enum):
    markdown = '.md'
    html = '.html'


@dataclass
class TocEntry:
    depth: int
    heading: str
    link: str


class DocumentParser(Protocol):
    """
    Interface for parsing document headings into a collection of entries.
    A subclass of the BaseTocGenerator can use those entries to generate a
    table of contents string.
    """

    @abc.abstractmethod
    def parseFile(self, infile) -> list[TocEntry]:
        """
        Parse a file to create a list of TocEntries

        :param str infile: The file to parse.
        """
        raise NotImplementedError


class SimpleHtmlParser(HTMLParser, DocumentParser):
    """
    A parser that will generate a list of TOC entries from heading nodes,
    (*e. g.*, ``<h2>Foo</h2>``, ``<h3>Bar</h3>``) in an HTML document.

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
            for name, value in attrs:
                if name == 'id':
                    self._link = f'#{value}'
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


class SimpleMarkdownParser(DocumentParser):
    """
    A parser that will create a list of TOC entries from heading lines
    (*e. g.*, ``## Foo``, ``### Bar``) in a Markdown document. Note that top
    level headings (``# Main title``) will be ignored.
    """
    FENCE = '```'
    RE_CAPTURE = re.compile('^(#+)(.*)$')
    RE_HTML_COMMENT = re.compile(r'<!--.*?-->', flags=re.S)  # Non-greedy match
    RE_SPECIALS = re.compile(r'''[!@#$%^&*()+;:'"\[\]{}|\\<>,./?`~]''')
    RE_CUSTOM_ID = re.compile(r'''(.*?)\s*\{(#.+?)}''')

    def __init__(self, *, use_custom_anchors=False):
        self.use_custom_anchors = use_custom_anchors

    def _openWithStrippedHtmlComments(self, filename: str) -> Iterator[str]:
        with open(filename) as f:
            yield from self.RE_HTML_COMMENT.sub('', f.read()).split('\n')

    def _deriveLinkFromHeading(self, heading, links):
        link = self.RE_SPECIALS.sub('', heading.lower().replace(' ', '-'))
        links[link] += 1
        if n_links := links[link] - 1:
            link = f'{link}-{str(n_links)}'
        return f'#{escape(link)}'

    def parseFile(self, infile) -> list[TocEntry]:
        in_fence = False
        links: dict[str, int] = defaultdict(int)
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

            if (self.use_custom_anchors
                    and (m := self.RE_CUSTOM_ID.match(heading))):
                heading, link = m.groups()
            else:
                link = self._deriveLinkFromHeading(heading, links)

            entries.append(TocEntry(depth, heading, link))

        return entries


def parse_file(infile: str, **kwargs) -> list[TocEntry]:
    parser: DocumentParser

    _, ext = os.path.splitext(infile.lower())
    match ext:
        case ".md" | ".rmd":
            use_custom_anchors = kwargs.get("use_custom_anchors", False)
            parser = SimpleMarkdownParser(use_custom_anchors=use_custom_anchors)
        case ".html" | ".htm" | ".xhtml":
            parser = SimpleHtmlParser()
        case _:
            raise ValueError("Infile format not supported")

    return parser.parseFile(infile)


class BaseTocGenerator(abc.ABC):
    """
    Abstract base class for generating a Table of Contents. Must be subclassed
    to generate a Table of Contents string for the corresponding output format.
    """

    def __init__(self, entries, indent=4, outfile=None):
        self.entries = entries
        self.indent = indent
        self.indent_str = indent * ' '
        self.outfile = outfile

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
                heading_str = f'[{entry.heading}]({entry.link})'
            else:
                heading_str = entry.heading
            lines.append(f'{pad}* {heading_str}')
        return '\n'.join(lines)


class HtmlTagGenerator(SimpleNamespace):
    """
    A variant of a SimpleNamespace that can be used to wrap strings in HTML
    tags. For example,

    >>> html_tags = HtmlTagGenerator(['h2', 'p', 'a'])
    >>> html_tags.h2('This is a heading')
    '<h2>This is a heading</h2>'
    >>> mylink = html_tags.a("mylink", attrs=[("href", "#somewhere-in-doc")])
    >>> html_tags.p(f'This is a link: {mylink}')
    '<p>This is a link: <a href="#somewhere-in-doc">mylink</a></p>'

    The instance is callable, resulting in a closure that can then be called
    to wrap strings with the tag provided. Additional tags can also be defined
    on the fly by using dot notation. Examples,

    >>> html_tags('ol')(html_tags.li('one') + html_tags.li('two'))
    '<ol><li>one</li><li>two</li></ol>'

    """
    def __init__(self, tags: Iterable[str]):
        """
        :param tags: The tags to be included. Accessed by dot notation.
        """
        super().__init__(**{t: self(t) for t in tags})

    def __getattr__(self, item):
        f = self(item)
        self.__setattr__(item, f)
        return f

    def __call__(self, tag: str):

        def html_tag(content: str,
                     *,
                     attrs: HtmlTagAttrs | None = None,
                     newline: bool = False,
                     indent: str | None = None):
            """
            :param content: The content to be placed inside the tag.
            :param attrs: The attributes to be inserted into the tag.
            :param newline: Whether to add a newline between tags and content.
            :param indent: Pad left the tags with this string.
            """
            attr_str = ' ' + ' '.join(f'{k}="{v}"' for k, v in attrs) \
                if attrs else ''
            newline_str = '\n' if newline else ''
            indent_str = indent or ''
            return (indent_str + f'<{tag}{attr_str}>' + newline_str +
                    content + newline_str +
                    indent_str + f'</{tag}>')  # yapf: disable

        return html_tag


_wrapInTag = HtmlTagGenerator(['h2', 'ul', 'li', 'a'])


class HtmlTocGenerator(BaseTocGenerator):

    def generateString(self) -> str:
        return (_wrapInTag.h2('Table of Contents') + '\n' +
                self._generateUlStr(self.entries, 0))

    def _generateUlStr(self, entries: Iterable[TocEntry], depth: int) -> str:
        """
        Generate a string containing potentially nested unordered list
        (``<ul>``) nodes from a list of TOC entries.
        """
        output = []
        groups = groupby(entries, lambda x: x.depth == depth)
        for is_same_depth, entry_group in groups:
            if is_same_depth:
                for entry in entry_group:
                    li = _wrapInTag.li(self._maybeWrapInLink(entry))
                    output.append((1 + depth) * self.indent_str + li)
            else:
                output.append(self._generateUlStr(entry_group, depth + 1))
        return _wrapInTag.ul(
            '\n'.join(output), newline=True, indent=depth * self.indent_str)

    @staticmethod
    def _maybeWrapInLink(entry: TocEntry) -> str:
        """
        Create a string out of a TOC entry. If the entry contains a non-empty
        link attribute, it will be wrapped in an anchor tag (``<a>``).
        """
        if entry.link:
            attrs = [('href', entry.link)]
            return _wrapInTag.a(entry.heading, attrs=attrs)
        return entry.heading


def parse_args(argv=None):
    # yapf: disable
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
        default='markdown',  # using string for default in help entry
        type=OutputFormatExtension.__getitem__,
        metavar=f'{{{",".join([ext.name for ext in OutputFormatExtension])}}}',
        choices=list(OutputFormatExtension),
        help='The output format. (default: %(default)s)')
    p.add_argument(
        '-c', '--use-custom-anchors',
        dest='use_custom_anchors',
        action='store_true',
        help='Activates extended Markdown syntax support for custom heading '
             'anchors. For example, "## Introduction {#intro}" will result in '
             'the heading text "Introduction" and the anchor link "#intro". '
             'Ignored if the input file is not ".md" extension.')
    p.add_argument(
        '-o', '--outfile',
        dest='outfile',
        help='A file to write output. Writes to STDOUT if not specified.')
    p.add_argument(
        'infile',
        help='The input file.')
    # yapf: enable
    return p.parse_args(argv)


TOC_GENERATORS: dict[OutputFormatExtension, Type[BaseTocGenerator]] = {
    OutputFormatExtension.markdown: MarkdownTocGenerator,
    OutputFormatExtension.html: HtmlTocGenerator,
}


def main():
    args = parse_args()
    entries = parse_file(**args.__dict__)

    toc_generator = TOC_GENERATORS[args.format]
    toc_generator(entries, indent=args.indent, outfile=args.outfile).write()


if __name__ == "__main__":
    main()
