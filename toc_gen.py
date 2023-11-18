#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make Tables of Contents

Generates a Table of Contents for Markdown documents.
The table will be output to STDOUT.
"""
import argparse
from collections.abc import Iterator
from collections.abc import Iterable
from collections import Counter
from dataclasses import dataclass
from html import escape
import re
import sys

__version__ = '1.0.0'


@dataclass
class TocEntry:
    depth: int
    heading: str
    link: str


class BaseTocGenerator:

    def __init__(self, infile, indent=4, outfile=None):
        self.infile = infile
        self.indent = indent
        self.outfile = outfile

    def write(self):
        s = self.generateString()
        if self.outfile:
            with open(self.outfile, 'wt') as fh:
                fh.write(s + '\n')
        else:
            print(s)

    def generateString(self) -> str:
        raise NotImplementedError


class MarkdownTocGenerator(BaseTocGenerator):
    FENCE = '```'
    RE_CAPTURE = re.compile('^(#+)(.*)$')
    RE_HTML_COMMENT = re.compile(r'<!--.*?-->', flags=re.S)  # Non-greedy match
    RE_SPECIALS = re.compile(r'''[!@#$%^&*()+;:'"\[\]{}|\\<>,./?`~]''')

    def __init__(self, infile='README.md', indent=4, outfile=None):
        super().__init__(infile, indent, outfile)
        self.headings = self._parseFile(infile)

    def generateString(self) -> str:
        lines = ['## Table of Contents', '']
        for heading in self.headings:
            pad = heading.depth * self.indent * " "
            lines.append(f'{pad}* [{heading.heading}](#{escape(heading.link)})')
        return '\n'.join(lines)

    def _open_with_stripped_html_comments(self, filename: str) -> Iterator[str]:
        with open(filename) as f:
            yield from self.RE_HTML_COMMENT.sub('', f.read()).split('\n')

    def _parseFile(self, infile) -> list[TocEntry]:
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


class HtmlTagGenerator:
    def __init__(self, tags: Iterable[str]):
        self.__dict__.update(**{t: self._htmlTagGenerator(t) for t in tags})

    @staticmethod
    def _htmlTagGenerator(tag):
        def html_tag(content):
            return f'<{tag}>' + content + f'</{tag}>'
        return html_tag


class HtmlTocGenerator(BaseTocGenerator):
    # TODO: complete implementation

    def __init__(self, infile, indent=4, outfile=None):
        super().__init__(infile, indent, outfile)
        self.html_tags = HtmlTagGenerator(['h2', 'ul', 'li'])
        ...


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        '-i', '--indent',
        dest='indent',
        type=int,
        default=4,
        help='The width of indentation.')
    p.add_argument(
        # TODO: derive from extension?
        '-f', '--format',
        dest='format',
        default='markdown',
        choices=['markdown', 'html'],
        help='The format of the document. (default: %(default)s)')
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
