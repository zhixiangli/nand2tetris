import argparse
import glob
import os
from typing import Optional

from symbol_table import SymbolTable, SymbolKind
from tokenizer import Tokenizer, Token
from vm_writer import VMWriter


class Parser:
    def __init__(self, tokens: list[tuple[Token, str]], writer: VMWriter):
        self.__tokens = tokens
        self.__index = 0
        self.__vm_writer = writer
        self.__class_name = None
        self.__subroutine_name = None
        self.__subroutine_kind = None
        self.__symbol_table = SymbolTable()
        self.__label_id = 0

    def compile_class(self):
        def is_class_var_dec():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text in ["static", "field"]

        def is_subroutine_dec():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text in [
                "constructor",
                "function",
                "method",
            ]

        assert self.__compile_token(Token.KEYWORD, "class")
        _, self.__class_name = self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, "{")
        while is_class_var_dec():
            self.compile_class_var_dec()
        while is_subroutine_dec():
            self.compile_subroutine_dec()
        assert self.__compile_token(Token.SYMBOL, "}")

    def compile_class_var_dec(self):
        _, var_kind = self.__compile_token(
            Token.KEYWORD, "static"
        ) or self.__compile_token(Token.KEYWORD, "field")
        _, var_type = self.__compile_type()
        _, var_name = self.__compile_token(Token.IDENTIFIER)
        self.__symbol_table.define(var_name, var_type, SymbolKind[var_kind.upper()])

        while self.__has_more_var_name_or_expr():
            assert self.__compile_token(Token.SYMBOL, ",")
            _, var_name = self.__compile_token(Token.IDENTIFIER)
            self.__symbol_table.define(var_name, var_type, SymbolKind[var_kind.upper()])
        assert self.__compile_token(Token.SYMBOL, ";")

    def compile_subroutine_dec(self):
        self.__symbol_table.start_subroutine()
        _, self.__subroutine_kind = (
            self.__compile_token(Token.KEYWORD, "constructor")
            or self.__compile_token(Token.KEYWORD, "function")
            or self.__compile_token(Token.KEYWORD, "method")
        )
        if self.__subroutine_kind == "method":
            self.__symbol_table.define("this", self.__class_name, SymbolKind.ARGUMENT)
        assert self.__compile_token(Token.KEYWORD, "void") or self.__compile_type()
        _, self.__subroutine_name = self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_parameter_list()
        assert self.__compile_token(Token.SYMBOL, ")")
        self.compile_subroutine_body()

    def compile_parameter_list(self):
        type_token = self.__compile_type()
        if type_token is None:
            return
        _, var_type = type_token
        _, var_name = self.__compile_token(Token.IDENTIFIER)
        self.__symbol_table.define(var_name, var_type, SymbolKind.ARGUMENT)
        while self.__has_more_var_name_or_expr():
            assert self.__compile_token(Token.SYMBOL, ",")
            _, var_type = self.__compile_type()
            _, var_name = self.__compile_token(Token.IDENTIFIER)
            self.__symbol_table.define(var_name, var_type, SymbolKind.ARGUMENT)

    def compile_subroutine_body(self):
        def is_var_dec():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "var"

        assert self.__compile_token(Token.SYMBOL, "{")
        while is_var_dec():
            self.compile_var_dec()
        self.__vm_writer.write_function(
            f"{self.__class_name}.{self.__subroutine_name}",
            self.__symbol_table.var_count(SymbolKind.LOCAL),
        )
        if self.__subroutine_kind == "method":
            self.__vm_writer.write_push("argument", 0)
            self.__vm_writer.write_pop("pointer", 0)
        elif self.__subroutine_kind == "constructor":
            self.__vm_writer.write_push(
                "constant", self.__symbol_table.var_count(SymbolKind.FIELD)
            )
            self.__vm_writer.write_call("Memory.alloc", 1)
            self.__vm_writer.write_pop("pointer", 0)
        self.compile_statements()
        assert self.__compile_token(Token.SYMBOL, "}")

    def compile_var_dec(self):
        assert self.__compile_token(Token.KEYWORD, "var")
        _, var_type = self.__compile_type()
        _, var_name = self.__compile_token(Token.IDENTIFIER)
        self.__symbol_table.define(var_name, var_type, SymbolKind.LOCAL)
        while self.__has_more_var_name_or_expr():
            assert self.__compile_token(Token.SYMBOL, ",")
            _, var_name = self.__compile_token(Token.IDENTIFIER)
            self.__symbol_table.define(var_name, var_type, SymbolKind.LOCAL)
        assert self.__compile_token(Token.SYMBOL, ";")

    def compile_statements(self):
        def is_let():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "let"

        def is_if():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "if"

        def is_while():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "while"

        def is_do():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "do"

        def is_return():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "return"

        while is_let() or is_if() or is_while() or is_do() or is_return():
            if is_let():
                self.compile_let()
            elif is_if():
                self.compile_if()
            elif is_while():
                self.compile_while()
            elif is_do():
                self.compile_do()
            elif is_return():
                self.compile_return()

    def compile_let(self):
        def is_array():
            token, text = self.__tokens[self.__index]
            return token == Token.SYMBOL and text == "["

        assert self.__compile_token(Token.KEYWORD, "let")
        _, var_name = self.__compile_token(Token.IDENTIFIER)
        var_kind = self.__symbol_table.kind_of(var_name).value
        var_index = self.__symbol_table.index_of(var_name)
        is_array = is_array()
        if is_array:
            self.__vm_writer.write_push(var_kind, var_index)
            assert self.__compile_token(Token.SYMBOL, "[")
            self.compile_expression()
            self.__vm_writer.write_arithmetic("add")
            assert self.__compile_token(Token.SYMBOL, "]")
        assert self.__compile_token(Token.SYMBOL, "=")
        self.compile_expression()
        if is_array:
            self.__vm_writer.write_pop("temp", 0)
            self.__vm_writer.write_pop("pointer", 1)
            self.__vm_writer.write_push("temp", 0)
            self.__vm_writer.write_pop("that", 0)
        else:
            self.__vm_writer.write_pop(var_kind, var_index)
        assert self.__compile_token(Token.SYMBOL, ";")

    def compile_if(self):
        def is_else():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "else"

        skip_else_label = f"skip.else.label.{self.__label_id}"
        skip_if_label = f"skip.if.label.{self.__label_id}"
        self.__label_id += 1

        assert self.__compile_token(Token.KEYWORD, "if")
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_expression()
        self.__vm_writer.write_arithmetic("not")
        self.__vm_writer.write_if(skip_if_label)
        assert self.__compile_token(Token.SYMBOL, ")")
        assert self.__compile_token(Token.SYMBOL, "{")
        self.compile_statements()
        assert self.__compile_token(Token.SYMBOL, "}")
        self.__vm_writer.write_goto(skip_else_label)
        self.__vm_writer.write_label(skip_if_label)
        if is_else():
            self.__compile_token(Token.KEYWORD, "else")
            assert self.__compile_token(Token.SYMBOL, "{")
            self.compile_statements()
            assert self.__compile_token(Token.SYMBOL, "}")
        self.__vm_writer.write_label(skip_else_label)

    def compile_while(self):
        while_label = f"while.label.{self.__label_id}"
        skip_while_label = f"skip.while.label.{self.__label_id}"
        self.__label_id += 1
        self.__vm_writer.write_label(while_label)
        assert self.__compile_token(Token.KEYWORD, "while")
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_expression()
        self.__vm_writer.write_arithmetic("not")
        self.__vm_writer.write_if(skip_while_label)
        assert self.__compile_token(Token.SYMBOL, ")")
        assert self.__compile_token(Token.SYMBOL, "{")
        self.compile_statements()
        assert self.__compile_token(Token.SYMBOL, "}")
        self.__vm_writer.write_goto(while_label)
        self.__vm_writer.write_label(skip_while_label)

    def compile_do(self):
        assert self.__compile_token(Token.KEYWORD, "do")
        _, var_name = self.__compile_token(Token.IDENTIFIER)
        func_name = None
        if self.__compile_token(Token.SYMBOL, "."):
            _, func_name = self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, "(")
        var_kind = self.__symbol_table.kind_of(var_name)
        var_type = self.__symbol_table.type_of(var_name)
        var_index = self.__symbol_table.index_of(var_name)
        if not func_name:
            self.__vm_writer.write_push("pointer", 0)
        elif var_type:
            self.__vm_writer.write_push(var_kind.value, var_index)
        expr_count = self.compile_expression_list()
        assert self.__compile_token(Token.SYMBOL, ")")
        assert self.__compile_token(Token.SYMBOL, ";")
        if not func_name:
            self.__vm_writer.write_call(
                f"{self.__class_name}.{var_name}",
                expr_count + 1,
            )
        elif var_type:
            self.__vm_writer.write_call(
                f"{var_type}.{func_name}",
                expr_count + 1,
            )
        else:
            self.__vm_writer.write_call(
                f"{var_name}.{func_name}",
                expr_count,
            )
        self.__vm_writer.write_pop("temp", 0)

    def compile_return(self):
        assert self.__compile_token(Token.KEYWORD, "return")
        if self.__compile_token(Token.SYMBOL, ";"):
            self.__vm_writer.write_push("constant", 0)
        else:
            self.compile_expression()
            assert self.__compile_token(Token.SYMBOL, ";")
        self.__vm_writer.write_return()

    def compile_expression(self):
        def is_op():
            token, text = self.__tokens[self.__index]
            return token == Token.SYMBOL and text in [
                "+",
                "-",
                "*",
                "/",
                "&",
                "|",
                "<",
                ">",
                "=",
            ]

        self.compile_term()
        while is_op():
            _, op = self.__compile_token(Token.SYMBOL)
            self.compile_term()
            if op == "+":
                self.__vm_writer.write_arithmetic("add")
            elif op == "-":
                self.__vm_writer.write_arithmetic("sub")
            elif op == "*":
                self.__vm_writer.write_call("Math.multiply", 2)
            elif op == "/":
                self.__vm_writer.write_call("Math.divide", 2)
            elif op == "&":
                self.__vm_writer.write_arithmetic("and")
            elif op == "|":
                self.__vm_writer.write_arithmetic("or")
            elif op == "<":
                self.__vm_writer.write_arithmetic("lt")
            elif op == ">":
                self.__vm_writer.write_arithmetic("gt")
            elif op == "=":
                self.__vm_writer.write_arithmetic("eq")
            else:
                raise SyntaxError

    def compile_term(self):
        token, text = self.__tokens[self.__index]
        if text == "(":  # '('expression')'
            assert self.__compile_token(Token.SYMBOL, "(")
            self.compile_expression()
            assert self.__compile_token(Token.SYMBOL, ")")
        elif text in ["-", "~"]:  # unaryOp term
            assert self.__compile_token(Token.SYMBOL)
            self.compile_term()
            self.__vm_writer.write_arithmetic("neg" if text == "-" else "not")
        elif self.__compile_token(Token.INTEGER_CONSTANT):  # integerConstant
            self.__vm_writer.write_push("constant", int(text))
        elif self.__compile_token(Token.STRING_CONSTANT):  # stringConstant
            self.__vm_writer.write_push("constant", len(text))
            self.__vm_writer.write_call("String.new", 1)
            for ch in text:
                self.__vm_writer.write_push("constant", ord(ch))
                self.__vm_writer.write_call("String.appendChar", 2)
        elif text in ["true", "false", "null", "this"] and self.__compile_token(
            Token.KEYWORD
        ):  # keywordConstant
            if text == "true":
                self.__vm_writer.write_push("constant", 1)
                self.__vm_writer.write_arithmetic("neg")
            elif text in ["false", "null"]:
                self.__vm_writer.write_push("constant", 0)
            elif text == "this":
                self.__vm_writer.write_push("pointer", 0)
            else:
                raise SyntaxError
        elif self.__compile_token(Token.IDENTIFIER):
            if self.__compile_token(Token.SYMBOL, "["):  # varName '[' expression ']'
                var_kind = self.__symbol_table.kind_of(text).value
                var_index = self.__symbol_table.index_of(text)
                self.__vm_writer.write_push(var_kind, var_index)
                self.compile_expression()
                self.__vm_writer.write_arithmetic("add")
                self.__vm_writer.write_pop("pointer", 1)
                self.__vm_writer.write_push("that", 0)
                assert self.__compile_token(Token.SYMBOL, "]")
            else:  # subroutineName
                var_name, func_name = text, None
                if self.__compile_token(Token.SYMBOL, "."):
                    _, func_name = self.__compile_token(Token.IDENTIFIER)
                if self.__compile_token(Token.SYMBOL, "("):
                    var_kind = self.__symbol_table.kind_of(var_name)
                    var_type = self.__symbol_table.type_of(var_name)
                    var_index = self.__symbol_table.index_of(var_name)
                    if not func_name:
                        self.__vm_writer.write_push("pointer", 0)
                    elif var_type:
                        self.__vm_writer.write_push(var_kind.value, var_index)
                    expr_count = self.compile_expression_list()
                    assert self.__compile_token(Token.SYMBOL, ")")
                    if not func_name:
                        self.__vm_writer.write_call(
                            f"{self.__class_name}.{var_name}",
                            expr_count + 1,
                        )
                    elif var_type:
                        self.__vm_writer.write_call(
                            f"{var_type}.{func_name}",
                            expr_count + 1,
                        )
                    else:
                        self.__vm_writer.write_call(
                            f"{var_name}.{func_name}",
                            expr_count,
                        )
                else:  # varName
                    segment, index = self.__symbol_table.kind_of(
                        var_name
                    ).value, self.__symbol_table.index_of(var_name)
                    self.__vm_writer.write_push(segment, int(index))

        else:
            raise SyntaxError

    def compile_expression_list(self):
        def is_expression():
            token, text = self.__tokens[self.__index]
            return (
                token
                in [
                    Token.INTEGER_CONSTANT,
                    Token.STRING_CONSTANT,
                    Token.KEYWORD,
                    Token.IDENTIFIER,
                ]
                or (token == Token.SYMBOL and text in ["(", "-", "~"])
            )

        expr_count = 0
        if is_expression():
            self.compile_expression()
            expr_count += 1
            while self.__has_more_var_name_or_expr():
                assert self.__compile_token(Token.SYMBOL, ",")
                self.compile_expression()
                expr_count += 1
        return expr_count

    def __has_more_var_name_or_expr(self) -> bool:
        token, text = self.__tokens[self.__index]
        return token == Token.SYMBOL and text == ","

    def __compile_token(
        self, token: Token, text: str = None
    ) -> Optional[tuple[Token, str]]:
        actual_token, actual_text = self.__tokens[self.__index]
        if token != actual_token:
            return None
        if text is not None and text != actual_text:
            return None
        self.__index += 1
        return actual_token, actual_text

    def __compile_type(self) -> Optional[tuple[Token, str]]:
        type_tokens = [
            (Token.KEYWORD, "int"),
            (Token.KEYWORD, "char"),
            (Token.KEYWORD, "boolean"),
            (Token.IDENTIFIER, None),
        ]
        for token, text in type_tokens:
            compiled = self.__compile_token(token, text)
            if compiled:
                return compiled
        return None


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Jack Language Syntax Analysis")
    arg_parser.add_argument("directory", help="directory of Jack code")
    args = arg_parser.parse_args()
    directory = os.path.abspath(args.directory)
    for jack_filepath in glob.glob(f"{directory}/*.jack"):
        vm_writer: VMWriter = VMWriter(jack_filepath.replace(".jack", ".vm"))
        with open(jack_filepath, "r") as input_file:
            tokenizer: Tokenizer = Tokenizer(input_file.read())
            parser: Parser = Parser(list(tokenizer), vm_writer)
            parser.compile_class()
