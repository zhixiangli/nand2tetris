import argparse
import glob
import os

from lxml import etree
from lxml.etree import Element

from tokenizer import Tokenizer, Token


class Parser:
    def __init__(self, tokens: list[tuple[Token, str]]):
        self.__tokens = tokens
        self.__index = 0
        self.__stack: list[Element] = []

    def compile_class(self):
        def is_class_var_dec():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text in ["static", "field"]

        def is_subrouting_dec():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text in [
                "constructor",
                "function",
                "method",
            ]

        self.__start_nonterminal_symbol("class")
        assert self.__compile_token(Token.KEYWORD, "class")
        assert self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, "{")
        while is_class_var_dec():
            self.compile_class_var_dec()
        while is_subrouting_dec():
            self.compile_subrouting_dec()
        assert self.__compile_token(Token.SYMBOL, "}")
        return self.__end_nonterminal_symbol()

    def compile_class_var_dec(self):
        self.__start_nonterminal_symbol("classVarDec")
        assert self.__compile_token(Token.KEYWORD, "static") or self.__compile_token(
            Token.KEYWORD, "field"
        )
        assert self.__compile_type()
        assert self.__compile_token(Token.IDENTIFIER)
        while self.__has_more_var_name_or_expr():
            assert self.__compile_token(Token.SYMBOL, ",")
            assert self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, ";")
        self.__end_nonterminal_symbol()

    def compile_subrouting_dec(self):
        self.__start_nonterminal_symbol("subroutineDec")
        assert (
            self.__compile_token(Token.KEYWORD, "constructor")
            or self.__compile_token(Token.KEYWORD, "function")
            or self.__compile_token(Token.KEYWORD, "method")
        )
        assert self.__compile_token(Token.KEYWORD, "void") or self.__compile_type()
        assert self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_parameter_list()
        assert self.__compile_token(Token.SYMBOL, ")")
        self.compile_subrouting_body()
        self.__end_nonterminal_symbol()

    def compile_parameter_list(self):
        self.__start_nonterminal_symbol("parameterList")
        if self.__compile_type():
            assert self.__compile_token(Token.IDENTIFIER)
            while self.__has_more_var_name_or_expr():
                assert self.__compile_token(Token.SYMBOL, ",")
                assert self.__compile_type()
                assert self.__compile_token(Token.IDENTIFIER)
        self.__end_nonterminal_symbol()

    def compile_subrouting_body(self):
        def is_var_dec():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "var"

        self.__start_nonterminal_symbol("subroutineBody")
        assert self.__compile_token(Token.SYMBOL, "{")
        while is_var_dec():
            self.compile_var_dec()
        self.compile_statements()
        assert self.__compile_token(Token.SYMBOL, "}")
        self.__end_nonterminal_symbol()

    def compile_var_dec(self):
        self.__start_nonterminal_symbol("varDec")
        assert self.__compile_token(Token.KEYWORD, "var")
        assert self.__compile_type()
        assert self.__compile_token(Token.IDENTIFIER)
        while self.__has_more_var_name_or_expr():
            assert self.__compile_token(Token.SYMBOL, ",")
            assert self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, ";")
        self.__end_nonterminal_symbol()

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

        self.__start_nonterminal_symbol("statements")
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
        self.__end_nonterminal_symbol()

    def compile_let(self):
        def is_array():
            token, text = self.__tokens[self.__index]
            return token == Token.SYMBOL and text == "["

        self.__start_nonterminal_symbol("letStatement")
        assert self.__compile_token(Token.KEYWORD, "let")
        assert self.__compile_token(Token.IDENTIFIER)
        if is_array():
            assert self.__compile_token(Token.SYMBOL, "[")
            self.compile_expression()
            assert self.__compile_token(Token.SYMBOL, "]")
        assert self.__compile_token(Token.SYMBOL, "=")
        self.compile_expression()
        assert self.__compile_token(Token.SYMBOL, ";")
        self.__end_nonterminal_symbol()

    def compile_if(self):
        def is_else():
            token, text = self.__tokens[self.__index]
            return token == Token.KEYWORD and text == "else"

        self.__start_nonterminal_symbol("ifStatement")
        assert self.__compile_token(Token.KEYWORD, "if")
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_expression()
        assert self.__compile_token(Token.SYMBOL, ")")
        assert self.__compile_token(Token.SYMBOL, "{")
        self.compile_statements()
        assert self.__compile_token(Token.SYMBOL, "}")
        if is_else():
            self.__compile_token(Token.KEYWORD, "else")
            assert self.__compile_token(Token.SYMBOL, "{")
            self.compile_statements()
            assert self.__compile_token(Token.SYMBOL, "}")
        self.__end_nonterminal_symbol()

    def compile_while(self):
        self.__start_nonterminal_symbol("whileStatement")
        assert self.__compile_token(Token.KEYWORD, "while")
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_expression()
        assert self.__compile_token(Token.SYMBOL, ")")
        assert self.__compile_token(Token.SYMBOL, "{")
        self.compile_statements()
        assert self.__compile_token(Token.SYMBOL, "}")
        self.__end_nonterminal_symbol()

    def compile_do(self):
        self.__start_nonterminal_symbol("doStatement")
        assert self.__compile_token(Token.KEYWORD, "do")
        assert self.__compile_token(Token.IDENTIFIER)
        if self.__compile_token(Token.SYMBOL, "."):
            assert self.__compile_token(Token.IDENTIFIER)
        assert self.__compile_token(Token.SYMBOL, "(")
        self.compile_expression_list()
        assert self.__compile_token(Token.SYMBOL, ")")
        assert self.__compile_token(Token.SYMBOL, ";")
        self.__end_nonterminal_symbol()

    def compile_return(self):
        def is_expression():
            token, text = self.__tokens[self.__index]
            return not (token == Token.SYMBOL and text == ";")

        self.__start_nonterminal_symbol("returnStatement")
        assert self.__compile_token(Token.KEYWORD, "return")
        if is_expression():
            self.compile_expression()
        assert self.__compile_token(Token.SYMBOL, ";")
        self.__end_nonterminal_symbol()

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

        self.__start_nonterminal_symbol("expression")
        self.compile_term()
        while is_op():
            assert self.__compile_token(Token.SYMBOL)
            self.compile_term()
        self.__end_nonterminal_symbol()

    def compile_term(self):
        self.__start_nonterminal_symbol("term")
        token, text = self.__tokens[self.__index]
        if text == "(":  # '('expression')'
            assert self.__compile_token(Token.SYMBOL, "(")
            self.compile_expression()
            assert self.__compile_token(Token.SYMBOL, ")")
        elif text in ["-", "~"]:  # unaryOp term
            assert self.__compile_token(Token.SYMBOL)
            self.compile_term()
        elif self.__compile_token(Token.INTEGER_CONSTANT):  # integerConstant
            pass
        elif self.__compile_token(Token.STRING_CONSTANT):  # stringConstant
            pass
        elif text in ["true", "false", "null", "this"] and self.__compile_token(
            Token.KEYWORD
        ):  # keywordConstant
            pass
        elif self.__compile_token(Token.IDENTIFIER):
            if self.__compile_token(Token.SYMBOL, "["):  # varName '[' expression ']'
                self.compile_expression()
                assert self.__compile_token(Token.SYMBOL, "]")
            else:  # subroutineName
                if self.__compile_token(Token.SYMBOL, "."):
                    assert self.__compile_token(Token.IDENTIFIER)
                if self.__compile_token(Token.SYMBOL, "("):
                    self.compile_expression_list()
                    assert self.__compile_token(Token.SYMBOL, ")")
                # default is varName
        else:
            raise SyntaxError
        self.__end_nonterminal_symbol()

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

        self.__start_nonterminal_symbol("expressionList")
        if is_expression():
            self.compile_expression()
            while self.__has_more_var_name_or_expr():
                assert self.__compile_token(Token.SYMBOL, ",")
                self.compile_expression()
        self.__end_nonterminal_symbol()

    def __has_more_var_name_or_expr(self) -> bool:
        token, text = self.__tokens[self.__index]
        return token == Token.SYMBOL and text == ","

    def __compile_token(self, token: Token, text: str = None) -> bool:
        actual_token, actual_text = self.__tokens[self.__index]
        if token != actual_token:
            return False
        if text is not None and text != actual_text:
            return False
        tag = self.__create_xml_element(actual_token.value, actual_text)
        self.__write_terminal_symbol(tag)
        self.__index += 1
        return True

    def __compile_type(self) -> bool:
        type_tokens = [
            (Token.KEYWORD, "int"),
            (Token.KEYWORD, "char"),
            (Token.KEYWORD, "boolean"),
            (Token.IDENTIFIER, None),
        ]
        for token, text in type_tokens:
            if self.__compile_token(token, text):
                return True
        return False

    def __start_nonterminal_symbol(self, text):
        tag = self.__create_xml_element(text)
        self.__write_terminal_symbol(tag)
        self.__stack.append(tag)

    def __write_terminal_symbol(self, tag: Element):
        if len(self.__stack) > 0:
            self.__stack[-1].append(tag)

    def __end_nonterminal_symbol(self) -> Element:
        return self.__stack.pop()

    def __create_xml_element(self, tag_name: str, text: str = "\n"):
        tag = etree.Element(tag_name)
        tag.text = text
        tag.tail = "\n"
        return tag


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Jack Language Syntax Analysis")
    arg_parser.add_argument("directory", help="directory of Jack code")
    args = arg_parser.parse_args()
    directory = os.path.abspath(args.directory)
    for jack_filepath in glob.glob(f"{directory}/*.jack"):
        with open(jack_filepath, "r") as input_file:
            tokenizer: Tokenizer = Tokenizer(input_file.read())
            parser: Parser = Parser(list(tokenizer))
            root = parser.compile_class()
            parsed_filepath = f"{os.path.splitext(jack_filepath)[0]}Parsed.xml"
            with open(parsed_filepath, "wb") as output_file:
                output_file.write(etree.tostring(root))
