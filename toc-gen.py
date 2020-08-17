#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Make Tables of Contents """
import re
from collections import Counter
from html import escape


def make_md_toc(file_name='README.md'):
    """ A quick and dirty TOC generator for markdown documents """

    # Initialize variables
    in_fence = False
    links = Counter()

    # Regex patterns
    re_fence = re.compile('^```')
    re_capture = re.compile('^(#+)(.*)$')
    re_html_comment = re.compile(r'<!--.*?-->', flags=re.S)

    f = open(file_name).read()
    f = re_html_comment.sub('', f)

    # Print main heading
    print('## Table of Contents\n')

    # Find all headings and add them to the TOC
    for line in f.split('\n'):

        # Find out if we are in a code fence
        if re_fence.match(line):
            in_fence = not in_fence
            continue

        # Ignore octothorps inside code fences
        if not in_fence:
            m = re_capture.match(line)

            if m:
                level = len(m.group(1))
                indent = (level - 2) * "    "
                heading = m.group(2).strip()
                link = heading.lower().replace(' ', '-')
                link = re.sub(r'''[!@#$%^&*()+;:'"\[\]{}|\\<>,./?`~]''', '', link)

                # Keep a count of headings of the same name
                n_links = links[link]
                links[link] += 1

                # If link already exists, append a number
                if n_links:
                    link = link + '-' + str(n_links)

                # Print entry
                print('{}* [{}](#{})'.format(indent, heading, escape(link)))


if __name__ == "__main__":
    import sys

    make_md_toc(sys.argv[-1])
