from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


class SymbolKind(Enum):
    STATIC = "static"
    FIELD = "this"
    ARGUMENT = "argument"
    LOCAL = "local"


@dataclass
class Symbol:
    type: str
    kind: SymbolKind
    index: int


class SymbolTable:
    def __init__(self):
        self.__class_scope: Dict[str, Symbol] = dict()
        self.__subroutine_scope: Dict[str, Symbol] = dict()

    def start_subroutine(self):
        self.__subroutine_scope.clear()

    def var_count(self, kind: SymbolKind):
        if kind == SymbolKind.STATIC or kind == SymbolKind.FIELD:
            return sum(symbol.kind == kind for symbol in self.__class_scope.values())
        elif kind == SymbolKind.ARGUMENT or kind == SymbolKind.LOCAL:
            return sum(
                symbol.kind == kind for symbol in self.__subroutine_scope.values()
            )
        raise SyntaxError

    def define(self, name: str, type: str, kind: SymbolKind):
        if kind == SymbolKind.STATIC or kind == SymbolKind.FIELD:
            if name not in self.__class_scope:
                self.__class_scope[name] = Symbol(
                    type=type, kind=kind, index=self.var_count(kind)
                )
        elif kind == SymbolKind.ARGUMENT or kind == SymbolKind.LOCAL:
            if name not in self.__subroutine_scope:
                self.__subroutine_scope[name] = Symbol(
                    type=type, kind=kind, index=self.var_count(kind)
                )
        else:
            raise SyntaxError

    def kind_of(self, name: str):
        symbol = self.__subroutine_scope.get(name, self.__class_scope.get(name))
        return None if symbol is None else symbol.kind

    def type_of(self, name: str):
        symbol = self.__subroutine_scope.get(name, self.__class_scope.get(name))
        return None if symbol is None else symbol.type

    def index_of(self, name: str):
        symbol = self.__subroutine_scope.get(name, self.__class_scope.get(name))
        return None if symbol is None else symbol.index
