# Hack Assembler

## Background

Hack assembler translates symbolic Hack assembly language into binary code that can execute ont the Hack hardware platform built in the previous projects. For example, `@2` is translated into `0000000000000010`, `D=A` is translated into `1110110000010000`.

## Generate *.hack file

`python3.9 hack_assembler.py ${filepath}`

### Sample command

`python3.9 hack_assembler.py add/Add.asm`
