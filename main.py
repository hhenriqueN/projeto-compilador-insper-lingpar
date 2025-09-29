import sys
import re
from abc import ABC, abstractmethod


class PrePro:
    @staticmethod
    def filter(code: str) -> str:
      
        if re.search(r'([0-9A-Za-z\)])//([0-9A-Za-z\(])', code):
            raise Exception("Uso inválido de '//' como operador. Use '/' para divisão.")

        return re.sub(r'//[^\n]*', '', code)

class Token:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

class Lexer:
    RESERVED = {"Println": "PRINT"}

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.next = None

    def _peek(self):
        if self.position < len(self.source):
            return self.source[self.position]
        return '\0'

    def select_next(self):
        # Ignora espaços, tabs e \r (não cria tokens a partir disso)
        while self.position < len(self.source) and self.source[self.position] in (" ", "\t", "\r"):
            self.position += 1

        if self.position >= len(self.source):
            self.next = Token('EOF', '')
            return self.next

        ch = self.source[self.position]

        # Nova linha -> END
        if ch == '\n':
            self.position += 1
            self.next = Token('END', '\n')
            return self.next

        # Parênteses
        if ch == '(':
            self.position += 1
            self.next = Token('OPEN_PAR', '(')
            return self.next
        if ch == ')':
            self.position += 1
            self.next = Token('CLOSE_PAR', ')')
            return self.next

        # Operadores
        if ch == '+':
            self.position += 1
            self.next = Token('PLUS', '+')
            return self.next
        if ch == '-':
            self.position += 1
            self.next = Token('MINUS', '-')
            return self.next
        if ch == '*':
            self.position += 1
            self.next = Token('MULT', '*')
            return self.next
        if ch == '/':
            # Se ainda restar um '/', é inválido (comentários já foram removidos no PrePro)
            if self.position + 1 < len(self.source) and self.source[self.position + 1] == '/':
                raise Exception("Uso inválido de '//' como operador. Use '/' para divisão.")
            self.position += 1
            self.next = Token('DIV', '/')
            return self.next
        if ch == '=':
            self.position += 1
            self.next = Token('ASSIGN', '=')
            return self.next

        # Inteiros
        if ch.isdigit():
            num = []
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num.append(self.source[self.position])
                self.position += 1
            self.next = Token('INT', int(''.join(num)))
            return self.next

        # Identificadores (começam com letra; podem conter letras, dígitos e '_')
        if ch.isalpha():
            ident = []
            while (self.position < len(self.source) and
                   (self.source[self.position].isalnum() or self.source[self.position] == '_')):
                ident.append(self.source[self.position])
                self.position += 1
            ident_str = ''.join(ident)
            if ident_str in Lexer.RESERVED:
                self.next = Token(Lexer.RESERVED[ident_str], ident_str)
            else:
                self.next = Token('IDEN', ident_str)
            return self.next

        raise Exception(f"Caractere inválido: {ch}")


class Variable:
    def __init__(self, value: int):
        self.value = value

class SymbolTable:
    def __init__(self):
        self._table = {}

    # Recupera valor de variável; erro se não existir
    def get(self, name: str) -> int:
        if name not in self._table:
            raise Exception(f"Variável '{name}' não definida")
        return self._table[name].value

    # Define/atualiza variável
    def set(self, name: str, value: int):
        self._table[name] = Variable(value)

class Node(ABC):
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    @abstractmethod
    def evaluate(self, st: SymbolTable):
        pass

class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st: SymbolTable):
        return self.value

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        if self.value == '+':
            return left + right
        elif self.value == '-':
            return left - right
        elif self.value == '*':
            return left * right
        elif self.value == '/':
            return left // right

class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        child = self.children[0].evaluate(st)
        if self.value == '+':
            return +child
        elif self.value == '-':
            return -child

class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self, st: SymbolTable):
        return st.get(self.value)

class Assignment(Node):
    def __init__(self, children):
        super().__init__('=', children)

    def evaluate(self, st: SymbolTable):

        name = self.children[0].value
        val = self.children[1].evaluate(st)
        st.set(name, val)

class Print(Node):
    def __init__(self, children):
        super().__init__('print', children)

    def evaluate(self, st: SymbolTable):
        val = self.children[0].evaluate(st)
        print(val)

class Block(Node):
    def __init__(self, children):
        super().__init__('block', children)

    def evaluate(self, st: SymbolTable):
        for child in self.children:
            child.evaluate(st)
        # Sem retorno

class NoOp(Node):
    def __init__(self):
        super().__init__('noop', [])

    def evaluate(self, st: SymbolTable):
        return None


class Parser:
    @staticmethod
    def parseProgram(lex: Lexer):
        """
        Novo ponto de entrada: consome uma sequência de statements até EOF,
        acumulando-os como filhos de um nó Block.
        """
        if lex.next.kind == "EOF":
          
            return Block([])

        children = []
        while lex.next.kind != "EOF":
            stmt = Parser.parseStatement(lex)
            children.append(stmt)
        return Block(children)

    @staticmethod
    def parseStatement(lex: Lexer):
        # Atribuição: IDEN '=' expr END
        if lex.next.kind == "IDEN":
            iden = Identifier(lex.next.value)
            lex.select_next()
            if lex.next.kind != "ASSIGN":
                raise Exception("Esperado '=' após identificador")
            lex.select_next()
            expr = Parser.parseExpression(lex)
            if lex.next.kind != "END":
                raise Exception("Esperado fim de linha")
            lex.select_next()
            return Assignment([iden, expr])

        # Print: 'print' '(' expr ')' END
        elif lex.next.kind == "PRINT":
            lex.select_next()
            if lex.next.kind != "OPEN_PAR":
                raise Exception("Esperado '(' após 'print'")
            lex.select_next()
            expr = Parser.parseExpression(lex)
            if lex.next.kind != "CLOSE_PAR":
                raise Exception("Esperado ')'")
            lex.select_next()
            if lex.next.kind != "END":
                raise Exception("Esperado fim de linha")
            lex.select_next()
            return Print([expr])

        # Linha vazia: END -> NoOp
        elif lex.next.kind == "END":
            lex.select_next()
            return NoOp()

        else:
            raise Exception(f"Instrução inválida: {lex.next.kind}")

    @staticmethod
    def parseExpression(lex: Lexer):
        node = Parser.parseTerm(lex)
        while lex.next.kind in ("PLUS", "MINUS"):
            op = lex.next.value
            lex.select_next()
            right = Parser.parseTerm(lex)
            node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseTerm(lex: Lexer):
        node = Parser.parseFactor(lex)
        while lex.next.kind in ("MULT", "DIV"):
            op = lex.next.value
            lex.select_next()
            right = Parser.parseFactor(lex)
            node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseFactor(lex: Lexer):
        if lex.next.kind == "INT":
            node = IntVal(lex.next.value)
            lex.select_next()
            return node

        elif lex.next.kind == "PLUS":
            lex.select_next()
            return UnOp('+', [Parser.parseFactor(lex)])

        elif lex.next.kind == "MINUS":
            lex.select_next()
            return UnOp('-', [Parser.parseFactor(lex)])

        elif lex.next.kind == "OPEN_PAR":
            lex.select_next()
            node = Parser.parseExpression(lex)
            if lex.next.kind != "CLOSE_PAR":
                raise Exception("Faltando fechar parêntese")
            lex.select_next()
            return node

        elif lex.next.kind == "IDEN":
            node = Identifier(lex.next.value)
            lex.select_next()
            return node

        else:
            raise Exception(f"Token inesperado: {lex.next.kind}")

    @staticmethod
    def run(source_code):
        lex = Lexer(source_code)
        lex.select_next()
        return Parser.parseProgram(lex)


def main():
    if len(sys.argv) < 2:
        raise Exception("Uso: python3 main.py <arquivo>")
    filename = sys.argv[1]
    with open(filename, "r") as f:
        code = f.read()


    code = PrePro.filter(code)

    lex = Lexer(code)
    lex.select_next()
    ast = Parser.parseProgram(lex)

    st = SymbolTable()
    ast.evaluate(st)

if __name__ == "__main__":
    main()
