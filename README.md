Table of Contents Generator
===========================

## Table of Contents

* [Description](#description)
* [Usage](#usage)
* [Examples](#examples)
    * [Command Line](#command-line)
    * [From VIM](#from-vim)
* [Issues](#issues)

## Description

This is a small Python module that can be used to create a table of contents
for a document, such as this _README.md_ file. It can both parse and write in
the following formats:

- Markdown
- HTML

It can easily be extended to other document formats as well.

## Usage

```
usage: toc_gen [-h] [-i INDENT] [-f {markdown,html}] [-o OUTFILE] file

Make Tables of Contents

Generates a Table of Contents for Markdown and HTML documents. The table will
be output to STDOUT or to file.

This is non-production software that is somewhat fragile. User input is not
carefully validated. Suggested usage is in interactive workflows when editing
your own documents. Use at your own risk.

positional arguments:
  file                  The input file.

options:
  -h, --help            show this help message and exit
  -i INDENT, --indent INDENT
                        The width of indentation.
  -f {markdown,html}, --format {markdown,html}
                        The output format. (default: markdown)
  -o OUTFILE, --outfile OUTFILE
                        A file to write output. Writes to STDOUT if not specified.
```

After installation, you will have access to a console utility called `toc_gen`.
Provide `toc_gen` with the file name for which you would like to generate a
table of contents. The output is sent to _stdout_ so it can be copy-pasted
manually or you can output directly into the document with certain text
editors like `vim`.

## Examples

### Command Line

The command `toc_gen README.md` generates the output below, which represents
the structure of this document. The output can be copied from the terminal and
pasted into the file.

```md
* [Description](#description)
* [Usage](#usage)
* [Examples](#examples)
    * [Command Line](#command-line)
    * [From VIM](#from-vim)
* [Issues](#issues)
```


### From VIM

In command mode, bring your cursor to the location where you would like to
insert the table of contents and type `r! toc_gen %`.

## Issues

This script is still under development. Anchor links may not be generated
correctly with some formatting or special characters. If you find an example,
please share in the form of an Issue or Pull Request!
