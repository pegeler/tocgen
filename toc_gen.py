#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Make Tables of Contents

Generates a Table of Contents for Markdown documents.
The table will be output to STDOUT.
"""
import argparse
from collections.abc import Iterator
from collections import Counter
from html import escape
import re


FENCE = '```'

# Regex patterns
RE_CAPTURE = re.compile('^(#+)(.*)$')
RE_HTML_COMMENT = re.compile(r'<!--.*?-->', flags=re.S)  # Non-greedy match
RE_SPECIALS = re.compile(r'''[!@#$%^&*()+;:'"\[\]{}|\\<>,./?`~]''')


def make_md_toc(infile='README.md', indent=4):
    """
    A Table of Contents generator for Markdown documents

    :param str infile: The input file.
    :param int indent: The width of indentation.
    """
    in_fence = False
    links = Counter()

    print('## Table of Contents\n')

    for line in _open_with_stripped_html_comments(infile):
        if line.startswith(FENCE):
            in_fence = not in_fence
            continue

        if not in_fence and (m := RE_CAPTURE.match(line)):
            level = len(m.group(1))
            pad = (level - 2) * indent * " "
            heading = m.group(2).strip()
            link = RE_SPECIALS.sub('', heading.lower().replace(' ', '-'))

            # Keep a count of headings of the same name
            n_links = links[link]
            links[link] += 1

            # ...and if link already exists, append a number
            if n_links:
                link = link + '-' + str(n_links)

            # Print entry
            print(f'{pad}* [{heading}](#{escape(link)})')


def _open_with_stripped_html_comments(file_name: str) -> Iterator[str]:
    with open(file_name) as f:
        yield from RE_HTML_COMMENT.sub('', f.read()).split('\n')


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        '-i', '--indent',
        dest='indent',
        type=int,
        default=4,
        help='The width of indentation.',
    )
    p.add_argument(
        'file',
        help='The input file.',
    )

    return p.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    make_md_toc(args.file, args.indent)
