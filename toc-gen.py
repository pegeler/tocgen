#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2019 Spectrum Health
# Licensed under GPL-3
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
    rx_fence = re.compile('^```')
    rx_capture = re.compile('^(#+)(.*)$')

    # Print main heading
    print('## Table of Contents\n')

    # Find all headings and add them to the TOC
    for line in open(file_name).readlines():

        # Find out if we are in a code fence
        if rx_fence.match(line):
            in_fence = not in_fence
            continue

        # Ignore octothorps inside code fences
        if not in_fence:
            m = rx_capture.match(line)

            if m:
                level = len(m.group(1))
                indent = (level - 2) * "    "
                heading = m.group(2).strip()
                link = heading.lower().replace(' ', '-')

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
