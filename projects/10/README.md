# Syntax Analyzer

## Background
It parses Jack programs according to the Jack grammar, producing an XML file that renders the program's structure using marked-up text.

## Setup

1. `virtualenv project10-venv`

1. `source project10-venv/bin/activate`

1. `pip3.9 install -r requirements.frozen`

1. run `pip3.9 freeze > requirements.frozen` to lock down your versions

## Tokenizer

### Example Commands

* `python3.9 tokenizer.py ./Square/`

## Parser

### Example Commands

* `python3.9 parser.py ./ArrayTest/`

* `python3.9 parser.py ./Square/`
