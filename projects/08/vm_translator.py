import argparse
import glob
import os
from typing import Optional

from iteration_utilities import deepflatten


class VMTranslator:
    def __init__(self, filename: str):
        self.__label_id = 0
        self.__segment_map = {
            "argument": "ARG",
            "that": "THAT",
            "this": "THIS",
            "local": "LCL"
        }
        self.__filename = filename

    def translate(self, lines: list[str]) -> list[str]:
        return self.__handle_vm_code(
            self.__handle_spaces(
                self.__handle_comments(lines)
            )
        )

    def __handle_vm_code(self, lines: list[str]) -> list[str]:
        results: list[str] = []
        for line in lines:
            results.append(f"// {line}")
            tokens: list[str] = line.split()
            command: str = tokens[0]
            if command == 'push':
                segment: Optional[str] = tokens[1] if len(tokens) > 1 else None
                index: Optional[int] = int(tokens[2]) if len(tokens) > 2 else None
                results.extend(self.__translate_push(segment, index))
            elif command == 'pop':
                segment: Optional[str] = tokens[1] if len(tokens) > 1 else None
                index: Optional[int] = int(tokens[2]) if len(tokens) > 2 else None
                results.extend(self.__translate_pop(segment, index))
            elif command == 'label':
                results.extend(self.__translate_label(label=tokens[1]))
            elif command == 'goto':
                results.extend(self.__translate_goto(label=tokens[1]))
            elif command == 'if-goto':
                results.extend(self.__translate_if_goto(label=tokens[1]))
            elif command == "function":
                results.extend(self.__translate_function(function_name=tokens[1], n_vars=int(tokens[2])))
            elif command == "call":
                results.extend(self.__translate_call(function_name=tokens[1], n_args=int(tokens[2])))
            elif command == "return":
                results.extend(self.__translate_return())
            else:
                results.extend(self.__translate_arithmetic(command))
        return results

    def __translate_function(self, function_name: str, n_vars: int) -> list[str]:
        return [
            f"({function_name})",
            self.__select_address("temp", 6),
            "M=0",
            [self.__translate_push("temp", 6) for _ in range(n_vars)],
        ]

    def __translate_call(self, function_name: str, n_args: int) -> list[str]:
        def push_value(value: str, apply_address: Optional[bool] = None) -> list[str]:
            return [
                f"@{value}",
                "D=A" if apply_address else "D=M",
                self.__select_address("temp", 6),
                "M=D",
                self.__translate_push("temp", 6),
            ]

        ret_addr_label: str = f"{function_name}$ret.{self.__label_id}"
        self.__label_id += 1
        return [
            push_value(ret_addr_label, True),
            push_value("LCL"),
            push_value("ARG"),
            push_value("THIS"),
            push_value("THAT"),
            # ARG=SP-5-nArgs
            f"@{5 + n_args}",
            "D=A",
            "@SP",
            "D=M-D",
            "@ARG",
            "M=D",
            # LCL=SP
            "@SP",
            "D=M",
            "@LCL",
            "M=D",
            self.__translate_goto(function_name),
            f"({ret_addr_label})",
        ]

    def __translate_return(self) -> list[str]:
        def restore_value(base: str, offset: int, target: str) -> list[str]:
            return [
                f"@{abs(offset)}",
                "D=A",
                f"@{base}",
                f"A=M{'-' if offset < 0 else '+'}D",
                "D=M",
                f"@{target}",
                "M=D"
            ]

        return [
            # calc retAddr first to avoid being override if the function has no arguments
            "@5",
            "D=A",
            "@LCL",
            "D=M-D",
            "A=D",
            "D=M",
            "@retAddr",
            "M=D",
            # store the return value to ARG[0]
            self.__translate_pop("argument", 0),
            # set SP to ARG[1]
            self.__select_address("argument", 1),
            "D=A",
            "@SP",
            "M=D",
            # restore values
            "@LCL",
            "D=M",
            "@endFrame",
            "M=D",
            restore_value("endFrame", -4, "LCL"),
            restore_value("endFrame", -3, "ARG"),
            restore_value("endFrame", -2, "THIS"),
            restore_value("endFrame", -1, "THAT"),
            # return to the caller address
            "@retAddr",
            "A=M",
            "0;JMP",
        ]

    def __translate_label(self, label: str) -> list[str]:
        return [
            f"({label})",
        ]

    def __translate_goto(self, label: str) -> list[str]:
        return [
            f"@{label}",
            "0;JMP",
        ]

    def __translate_if_goto(self, label: str) -> list[str]:
        return [
            self.__translate_pop("temp", 6),
            self.__select_address("temp", 6),
            "D=M",
            f"@{label}",
            "D;JNE",
        ]

    def __select_address(self, segment: str, index: int) -> list[str]:
        if segment == "constant":
            # no address return for constant value
            return []
        if segment == "pointer":
            return [f"@{index + 3}"]
        if segment == "temp":
            # MUST NOT USE D REGISTER HERE!!!
            return [f"@{index + 5}"]
        if segment == "static":
            return [f"@{self.__filename}.{index}"]
        if segment in self.__segment_map.keys():
            return [
                f"@{self.__segment_map.get(segment)}",
                "D=M",
                f"@{index}",
                "A=A+D",
            ]
        raise NotImplementedError(f"Unknown segment {segment}")

    def __translate_push(self, segment: str, index: int) -> list[str]:
        commands: list[str] = self.__select_address(segment, index)
        if segment == 'constant':
            commands.extend([
                f"@{index}",
                "D=A"
            ])
        else:
            commands.extend([
                "D=M"
            ])
        commands.extend([
            "@SP",
            "M=M+1",
            "A=M-1",
            "M=D",
        ])
        return commands

    def __translate_pop(self, segment: str, index: int) -> list[str]:
        return [
            self.__select_address(segment, index),
            "D=A",
            "@R13",  # R13 stores the target address
            "M=D",
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            # set value to address *R13
            "@R13",
            "A=M",
            "M=D",
        ]

    def __translate_arithmetic(self, command: str) -> list[str]:
        def unary(operator: str) -> list[str]:
            return [
                self.__translate_pop("temp", 6),
                self.__select_address("temp", 6),
                f"M={operator}M",
                self.__translate_push("temp", 6)
            ]

        def binary(operator: str) -> list[str]:
            return [
                self.__translate_pop("temp", 7),
                self.__translate_pop("temp", 6),
                self.__select_address("temp", 7),
                "D=A",
                "@R13",
                "M=D",
                self.__select_address("temp", 6),
                "D=M",
                "@R13",
                "A=M",
                f"M=D{operator}M",
                self.__translate_push("temp", 7)
            ]

        def compare(jump: str):
            true_label, false_label, main_label = f"true_label_{self.__label_id}", f"false_label_{self.__label_id}", \
                                                  f"main_label_{self.__label_id}"
            self.__label_id += 1
            return [
                self.__translate_pop("temp", 7),
                self.__translate_pop("temp", 6),
                self.__select_address("temp", 7),
                "D=A",
                "@R13",
                "M=D",
                self.__select_address("temp", 6),

                "D=M",
                "@R13",
                "A=M",
                "D=D-M",
                f"@{true_label}",
                f"D;{jump}",
                self.__translate_goto(false_label),

                f"({true_label})",
                "D=-1",
                self.__translate_goto(main_label),

                f"({false_label})",
                "D=0",
                self.__translate_goto(main_label),

                f"({main_label})",
                self.__select_address("temp", 7),
                "M=D",
                self.__translate_push("temp", 7),
            ]

        if command == 'add':
            return binary("+")
        elif command == 'sub':
            return binary("-")
        elif command == 'neg':
            return unary("-")
        elif command == 'eq':
            return compare("JEQ")
        elif command == 'gt':
            return compare("JGT")
        elif command == 'lt':
            return compare("JLT")
        elif command == 'and':
            return binary("&")
        elif command == 'or':
            return binary("|")
        elif command == 'not':
            return unary("!")
        else:
            raise NotImplementedError(f"Unknown command {command}")

    def __handle_spaces(self, lines: list[str]) -> list[str]:
        return [line.strip() for line in lines if line.strip()]

    def __handle_comments(self, lines: list[str]) -> list[str]:
        return [line.split('//')[0] for line in lines]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Translate VM Code to Hack Assembly Code')
    parser.add_argument('vm', help='filepath or directory of VM code')
    parser.add_argument('--booting', default=False, action=argparse.BooleanOptionalAction,
                        help='call Sys.init if the function exist')
    parser.add_argument("--sp", type=int, default=None,
                        help="set the value to SP when booting is True")
    args = parser.parse_args()

    input_path: str = os.path.abspath(args.vm)
    vm_files: list[str] = glob.glob(f"{input_path}/*.vm") if os.path.isdir(input_path) \
        else ([input_path] if input_path.endswith(".vm") else [])
    assert len(vm_files) > 0, f"No *.vm file is found from {input_path}"

    asm_code: list[str] = []
    for vm_file in vm_files:
        input_filename = os.path.splitext(os.path.basename(vm_file))[0]
        translator: VMTranslator = VMTranslator(filename=input_filename)
        with open(vm_file, "r") as input_file:
            code: list[str] = input_file.read().splitlines()
            asm_code.extend(translator.translate(code))
    output_path = (input_path + f"/{os.path.basename(input_path)}" if os.path.isdir(input_path)
                   else input_path.rstrip(".vm")) + ".asm"

    asm_code = list(deepflatten(asm_code, ignore=str))
    if args.booting and "(Sys.init)" in asm_code:
        # inject the bootstrap code
        asm_code = ([
                        f"@{args.sp}",
                        "D=A",
                        "@SP",
                        "M=D",
                    ] if args.sp is not None else []) + [
                       "@Sys.init",
                       "0;JMP",
                   ] + asm_code
    with open(output_path, "w") as output_file:
        output_file.write("\n".join(asm_code))
