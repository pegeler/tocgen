Table of Contents Generator
===========================

## Description

This is a Python module and command-line tool that can parse a document and
produce a programmatically-generated table of contents for that document. In
fact, the [Table of Contents](#table-of-contents) of this _README.md_ file was
produced using `tocgen`. The table can be output to STDOUT or written to file.

Input and output formats can be mixed and matched. For example, the input file
could be a Markdown document but the output Table of Contents could be specified
as HTML. It is an extensible framework that supports additional formats for both
parsing and output.

This is non-production software that is still under development. The API is
subject to change (though it will be versioned). There is no guarantee that
the parsers or writers implement the full language specifications. Currently,
suggested usage is in interactive workflows when editing your own documents.
Use at your own risk.

## Table of Contents

* [Description](#description)
* [Supported Formats](#supported-formats)
* [Installation](#installation)
* [Usage](#usage)
* [Examples](#examples)
    * [Command Line](#command-line)
    * [From VIM](#from-vim)
* [Issues](#issues-and-contributing)

## Supported Formats

- Markdown
- HTML

More to come. Contributions welcome.

## Installation

Navigate to the project directory and run the following command:

```bash
pip install "git+https://github.com/pegeler/tocgen"
```

You may substitute with your Python command of choice and/or use a
virtual environment.

## Usage

```
usage: tocgen [-h] [-i INDENT] [-f {markdown,html}] [-c] [-o OUTFILE] infile

positional arguments:
  infile                The input file.

options:
  -h, --help            show this help message and exit
  -i INDENT, --indent INDENT
                        The width of indentation.
  -f {markdown,html}, --format {markdown,html}
                        The output format. (default: markdown)
  -c, --use-custom-anchors
                        Activates extended Markdown syntax support for custom
                        heading anchors. For example, "## Introduction
                        {#intro}" will result in the heading text
                        "Introduction" and the anchor link "#intro". Ignored
                        if the input file is not ".md" extension.
  -o OUTFILE, --outfile OUTFILE
                        A file to write output. Writes to STDOUT if not
                        specified.
```

After installation, you will have access to a console utility called `tocgen`.
Provide `tocgen` with the file name for which you would like to generate a
table of contents. The output is sent to _stdout_ by default, so it can be
copy-pasted manually. Or you can output directly into the document with certain
text editors like `vim` or `emacs`.

## Examples

### Command Line

The command `tocgen README.md` generates the output below, which represents
the structure of this document. The output can be copied from the terminal and
pasted into the file.

```md
* [Description](#description)
* [Supported Formats](#supported-formats)
* [Installation](#installation)
* [Usage](#usage)
* [Examples](#examples)
    * [Command Line](#command-line)
    * [From VIM](#from-vim)
* [Issues](#issues-and-contributing)
```

### From VIM

In command mode, bring your cursor to the location where you would like to
insert the table of contents and type `:r! tocgen %`.

<!-- TODO: add instructions for more text editors -->

## Issues and Contributing

This script is still under development. Anchor links may not be generated
correctly with some formatting or special characters. If you find an example,
please share in the form of an Issue or Pull Request!
