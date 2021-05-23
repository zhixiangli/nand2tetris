import argparse
from typing import Optional


class VMTranslator:
    def __init__(self, filename: str):
        self.__label_id = 0
        self.__segment_map = {
            "argument": "ARG",
            "that": "THAT",
            "this": "THIS",
            "local": "LCL",
        }
        self.__filename = filename

    def translate(self, lines: list[str]) -> list[str]:
        return self.__handle_vm_code(
            self.__handle_spaces(self.__handle_comments(lines))
        )

    def __handle_vm_code(self, lines: list[str]) -> list[str]:
        results: list[str] = []
        for line in lines:
            tokens: list[str] = line.split()
            command: str = tokens[0]
            segment: Optional[str] = tokens[1] if len(tokens) > 1 else None
            index: Optional[int] = int(tokens[2]) if len(tokens) > 2 else None
            if command == "push":
                results.extend(self.__translate_push(segment, index))
            elif command == "pop":
                results.extend(self.__translate_pop(segment, index))
            else:
                results.extend(self.__translate_arithmetic(command))
        return results

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
        if segment == "constant":
            commands.extend([f"@{index}", "D=A"])
        else:
            commands.extend(["D=M"])
        commands.extend(
            [
                "@SP",
                "M=M+1",
                "A=M-1",
                "M=D",
            ]
        )
        return commands

    def __translate_pop(self, segment: str, index: int) -> list[str]:
        commands: list[str] = self.__select_address(segment, index)
        commands.extend(
            [
                "D=A",
                "@R13",  # R13 stores the target address
                "M=D",
            ]
        )
        commands.extend(
            [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                # set value to address *R13
                "@R13",
                "A=M",
                "M=D",
            ]
        )
        return commands

    def __translate_arithmetic(self, command: str) -> list[str]:
        def unary(operator: str):
            results.extend(self.__translate_pop("temp", 0))
            results.extend(self.__select_address("temp", 0))
            results.extend([f"M={operator}M"])
            results.extend(self.__translate_push("temp", 0))

        def binary(operator: str):
            results.extend(self.__translate_pop("temp", 1))
            results.extend(self.__translate_pop("temp", 0))

            results.extend(self.__select_address("temp", 1))
            results.extend(
                [
                    "D=A",
                    "@R13",
                    "M=D",
                ]
            )
            results.extend(self.__select_address("temp", 0))
            results.extend(["D=M", "@R13", "A=M", f"M=D{operator}M"])

            results.extend(self.__translate_push("temp", 1))

        def compare(jump: str):
            true_label, false_label, main_label = (
                f"true_label_{self.__label_id}",
                f"false_label_{self.__label_id}",
                f"main_label_{self.__label_id}",
            )
            self.__label_id += 1
            results.extend(self.__translate_pop("temp", 1))
            results.extend(self.__translate_pop("temp", 0))

            results.extend(self.__select_address("temp", 1))
            results.extend(
                [
                    "D=A",
                    "@R13",
                    "M=D",
                ]
            )
            results.extend(self.__select_address("temp", 0))
            results.extend(
                [
                    "D=M",
                    "@R13",
                    "A=M",
                    "D=D-M",
                    f"@{true_label}",
                    f"D;{jump}",
                    f"@{false_label}",
                    "0;JMP",
                    f"({true_label})",
                    "D=-1",
                    f"@{main_label}",
                    "0;JMP",
                    f"({false_label})",
                    "D=0",
                    f"@{main_label}",
                    "0;JMP",
                    f"({main_label})",
                ]
            )
            results.extend(self.__select_address("temp", 1))
            results.extend(["M=D"])
            results.extend(self.__translate_push("temp", 1))

        results: list[str] = []
        if command == "add":
            binary("+")
        elif command == "sub":
            binary("-")
        elif command == "neg":
            unary("-")
        elif command == "eq":
            compare("JEQ")
        elif command == "gt":
            compare("JGT")
        elif command == "lt":
            compare("JLT")
        elif command == "and":
            binary("&")
        elif command == "or":
            binary("|")
        elif command == "not":
            unary("!")
        else:
            raise NotImplementedError(f"Unknown command {command}")
        return results

    def __handle_spaces(self, lines: list[str]) -> list[str]:
        return [line.strip() for line in lines if line.strip()]

    def __handle_comments(self, lines: list[str]) -> list[str]:
        return [line.split("//")[0] for line in lines]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Translate VM Code to Hack Assembly Code"
    )
    parser.add_argument("vm", help="filepath of VM code")
    args = parser.parse_args()

    filepath: str = args.vm
    assert filepath.endswith(".vm"), f"{filepath} doesn't end with .vm"

    output: str = filepath.rstrip(".vm") + ".asm"
    translator: VMTranslator = VMTranslator(
        filename=filepath.split("/")[-1].split(".")[0]
    )
    with open(filepath, "r") as input_file:
        code: list[str] = input_file.read().splitlines()
        with open(output, "w") as output_file:
            output_file.write("\n".join(translator.translate(code)))
