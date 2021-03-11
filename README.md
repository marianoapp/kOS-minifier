kOS minifier
============

Minify your kOS scripts down to as little as 30% of their original size.

## Requirements
Python 3

## Usage

minifier.py [options] file

### Options
* `-a, --all`

Apply all transformations (default option if none specified)
* `-c, --remove-comments`

Remove comments
* `-i, --remove-indentation`

Remove leading whitespace

* `-s, --remove-spaces`

Remove spaces within instructions

* `-n, --remove-newlines`

Merge the script into a single line

* `-v, --replace-vars`

Replace variable names with shorter ones