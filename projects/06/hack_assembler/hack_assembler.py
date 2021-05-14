import argparse


class HackAssembler:
    def __init__(self):
        self.__comp_code = {
            '0': '0101010',
            '1': '0111111',
            '-1': '0111010',
            'D': '0001100',
            'A': '0110000',
            '!D': '0001101',
            '!A': '0110001',
            '-D': '0001111',
            '-A': '0110011',
            'D+1': '0011111',
            'A+1': '0110111',
            'D-1': '0001110',
            'A-1': '0110010',
            'D+A': '0000010',
            'D-A': '0010011',
            'A-D': '0000111',
            'D&A': '0000000',
            'D|A': '0010101',
            'M': '1110000',
            '!M': '1110001',
            '-M': '1110011',
            'M+1': '1110111',
            'M-1': '1110010',
            'D+M': '1000010',
            'D-M': '1010011',
            'M-D': '1000111',
            'D&M': '1000000',
            'D|M': '1010101'
        }
        self.__jump_code = ['', 'JGT', 'JEQ', 'JGE', 'JLT', 'JNE', 'JLE', 'JMP']
        self.__defined_symbols = {'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
                                  'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3,
                                  'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7,
                                  'R8': 8, 'R9': 9, 'R10': 10, 'R11': 11,
                                  'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15,
                                  'SCREEN': 0x4000, 'KBD': 0x6000}

    def translate(self, lines: list[str]) -> list[str]:
        return self.__handle_instructions(
            self.__handle_symbols(
                self.__handle_spaces(
                    self.__handle_comments(lines)
                )
            )
        )

    def __handle_symbols(self, lines: list[str]) -> list[str]:
        symbols = self.__defined_symbols.copy()
        results: list[str] = []
        for line in lines:
            if line[0] == '(' and line[-1] == ')':
                symbols[line[1:-1]] = len(results)
            else:
                results.append(line)
        counter = 16
        for (idx, line) in enumerate(results):
            if self.__is_a_instruction(line):
                value: str = line[1:]
                if value.isdigit():
                    continue
                if value not in symbols:
                    symbols[value] = counter
                    counter += 1
                results[idx] = line[0] + str(symbols[value])
        return results

    def __translate_dest(self, line: str) -> str:
        result = 0
        if '=' in line:
            dest = line.split('=')[0]
            if 'M' in dest:
                result |= 1
            if 'D' in dest:
                result |= 1 << 1
            if 'A' in dest:
                result |= 1 << 2
        return format(result, '03b')

    def __translate_comp(self, line: str) -> str:
        st = line.index('=') + 1 if '=' in line else 0
        nd = line.index(';') if ';' in line else len(line)
        comp = line[st:nd]
        return self.__comp_code.get(comp)

    def __translate_jump(self, line: str) -> str:
        jump = None
        if ';' in line:
            jump = line.split(';')[1]
        result = self.__jump_code.index(jump or '')
        return format(result, '03b')

    def __is_a_instruction(self, line: str) -> bool:
        return line[0] == '@'

    def __translate_a_instruction(self, line: str) -> str:
        return '0' + format(int(line[1:]), '015b')[-15:]

    def __translate_c_instruction(self, line: str) -> str:
        return '111' + self.__translate_comp(line) + self.__translate_dest(line) + self.__translate_jump(line)

    def __handle_instructions(self, lines: list[str]) -> list[str]:
        result: list[str] = []
        for line in lines:
            if self.__is_a_instruction(line):
                result.append(self.__translate_a_instruction(line))
            else:
                result.append(self.__translate_c_instruction(line))
        return result

    def __handle_spaces(self, lines: list[str]) -> list[str]:
        return ["".join(line.split()) for line in lines if line.strip()]

    def __handle_comments(self, lines: list[str]) -> list[str]:
        return [line.split('//')[0] for line in lines]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Translate Hack assembly code to Hack binary code')
    parser.add_argument('asm', help='filepath of Hack assembly code')
    args = parser.parse_args()

    filepath: str = args.asm
    assert filepath.endswith(".asm"), f"{filepath} doesn't end with .asm"

    output: str = filepath.rstrip(".asm") + ".hack"
    assembler: HackAssembler = HackAssembler()
    with open(filepath, "r") as input_file:
        code: list[str] = input_file.read().splitlines()
        with open(output, "w") as output_file:
            output_file.write("\n".join(assembler.translate(code)))
