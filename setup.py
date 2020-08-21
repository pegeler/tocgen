#!/usr/bin/env python3
from setuptools import setup

setup(name='toc_gen',
      version='0.0',
      author='Paul Egeler, MS',
      description='Create a Table of Contents from a Markdown Document',
      url='https://github.com/SpectrumHealthResearch/toc-gen/',
      license='GPL-3',
      py_modules=['toc_gen'],
      entry_points={'console_scripts': ['toc_gen = toc_gen:main']},
)
