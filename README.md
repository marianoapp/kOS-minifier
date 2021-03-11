kOS minifier
============

Minify your kOS scripts down to as little as 30% of their original size.

## Requirements
Python 3

## Usage

minifier.py [options] file

### Options
* -a, --all                 apply all transformations (default option if none specified)
* -c, --remove-comments     remove comments
* -i, --remove-indentation  remove leading whitespace
* -s, --remove-spaces       remove spaces within instructions
* -n, --remove-newlines     merge the script into a single line
* -v, --replace-vars        replace variable names with shorter ones