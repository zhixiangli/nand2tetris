from enum import Enum


class Token(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    INTEGER_CONSTANT = "integerConstant"
    STRING_CONSTANT = "stringConstant"
    IDENTIFIER = "identifier"


class Tokenizer:
    def __init__(self, code: str):
        self.__keywords = [
            "class",
            "method",
            "function",
            "constructor",
            "int",
            "boolean",
            "char",
            "void",
            "var",
            "static",
            "field",
            "let",
            "do",
            "if",
            "else",
            "while",
            "return",
            "true",
            "false",
            "null",
            "this",
        ]
        self.__symbols = "{}()[].,;+-*/&|<>=~"
        self.__code = code

    def __iter__(self):
        self.__index = 0
        return self

    def __next__(self) -> tuple[Token, str]:
        """
        :return: [token name (e.g. "keyword"), token value (e.g. int)]
        """
        while self.__skip_comments() or self.__skip_spaces():
            pass
        if self.__index >= len(self.__code):
            raise StopIteration
        # STRING_CONSTANT
        if self.__code[self.__index] == '"':
            pos = self.__code.find('"', self.__index + 1)
            if pos < 0:
                raise SyntaxError
            val: str = self.__code[self.__index + 1 : pos]
            self.__index = pos + 1
            return Token.STRING_CONSTANT, val
        # SYMBOL
        elif self.__code[self.__index] in self.__symbols:
            val: str = self.__code[self.__index]
            self.__index += 1
            return Token.SYMBOL, val
        # INTEGER_CONSTANT
        elif self.__code[self.__index].isdigit():
            start = self.__index
            while (
                self.__index < len(self.__code) and self.__code[self.__index].isdigit()
            ):
                self.__index += 1
            return Token.INTEGER_CONSTANT, self.__code[start : self.__index]
        # KEY_WORD or IDENTIFIER
        else:
            start = self.__index
            while self.__index < len(self.__code) and (
                self.__code[self.__index].isalnum() or self.__code[self.__index] == "_"
            ):
                self.__index += 1
            val: str = self.__code[start : self.__index]
            if val in self.__keywords:
                return Token.KEYWORD, val
            else:
                return Token.IDENTIFIER, val

    def __skip_spaces(self) -> bool:
        if self.__index < len(self.__code) and self.__code[self.__index].isspace():
            self.__index += 1
            return True
        return False

    def __skip_comments(self) -> bool:
        curr: str = self.__code[self.__index :]
        if curr.startswith("//"):
            pos = self.__code.find("\n", self.__index)
            self.__index = len(self.__code) if pos < 0 else pos + 1
            return True
        elif curr.startswith("/*"):
            pos = self.__code.find("*/", self.__index)
            self.__index = len(self.__code) if pos < 0 else pos + 2
            return True
        return False
