# VM to Assembly Translator

## Background

Extend the basic VM translator built in project 7 into a full-scale VM translator. In this project, it handles the VM language's branching and function calling commands.

## Setup

1. `virtualenv project08-venv`

1. `source project08-venv/bin/activate`

1. `pip3.9 install -r requirements.frozen`

1. run `pip3.9 freeze > requirements.frozen` to lock down versions

## Generate .asm file

Run `python3.9 vm_translator.py -h` to see usage

In **FunctionCalls/FibonacciElement** and **FunctionCalls/StaticsTest**, we need to enable booting to call **Sys.init**
and override **SP=261**.

### Sample commands

* `python3.9 vm_translator.py ProgramFlow/BasicLoop/BasicLoop.vm`

* `python3.9 vm_translator.py FunctionCalls/FibonacciElement/ --booting --sp 261`

* `python3.9 vm_translator.py FunctionCalls/StaticsTest/ --booting --sp 261`