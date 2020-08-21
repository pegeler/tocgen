# toc-gen

Create a table of contents from a markdown document.

## Table of Contents

* [Description](#description)
* [Usage](#usage)
* [Examples](#examples)
    * [Command Line](#command-line)
    * [From VIM](#from-vim)
* [Issues](#issues)

## Description

This is a small Python module that can be used to create a table of contents
for a markdown document, such as this _README.md_ file.

## Usage

```bash
toc_gen FILE
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
