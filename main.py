import sys
from abc import ABC, abstractmethod

# ---------------------------
# Classe Token
# ---------------------------
class Token():
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value


# ---------------------------
# Lexer
# ---------------------------
class Lexer():
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.next = None

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position] == " ":
            self.position += 1

        if self.position == len(self.source):
            self.next = Token('EOF', '')
            return self.next

        elif self.source[self.position] == "+":
            self.next = Token('PLUS', '+')
            self.position += 1
            return self.next

        elif self.source[self.position] == "-":
            self.next = Token('MINUS', '-')
            self.position += 1
            return self.next

        elif self.source[self.position] == "*":
            self.next = Token('MULT', '*')
            self.position += 1
            return self.next

        elif self.source[self.position] == "/":
            self.next = Token('DIV', '/')
            self.position += 1
            return self.next

        elif self.source[self.position] == "(":
            self.next = Token('OPEN_PAR', '(')
            self.position += 1
            return self.next

        elif self.source[self.position] == ")":
            self.next = Token('CLOSE_PAR', ')')
            self.position += 1
            return self.next

        elif self.source[self.position].isdigit():
            numero = ''
            while self.position < len(self.source) and self.source[self.position].isdigit():
                numero += self.source[self.position]
                self.position += 1
            numero = int(numero)
            self.next = Token('INT', numero)
            return self.next

        else:
            raise Exception(f"Caractere inválido: {self.source[self.position]}")


# ---------------------------
# Classe base Node
# ---------------------------
class Node(ABC):
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []

    @abstractmethod
    def evaluate(self):
        pass


# ---------------------------
# Nó IntVal
# ---------------------------
class IntVal(Node):
    def __init__(self, value):
        super().__init__(value, [])

    def evaluate(self):
        return self.value


# ---------------------------
# Nó BinOp
# ---------------------------
class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self):
        left = self.children[0].evaluate()
        right = self.children[1].evaluate()

        if self.value == '+':
            return left + right
        elif self.value == '-':
            return left - right
        elif self.value == '*':
            return left * right
        elif self.value == '/':
            return left // right


# ---------------------------
# Nó UnOp
# ---------------------------
class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self):
        child = self.children[0].evaluate()
        if self.value == '+':
            return +child
        elif self.value == '-':
            return -child


# ---------------------------
# Parser
# ---------------------------
class Parser:
    @staticmethod
    def parse_expression(lex):
        node = Parser.parse_term(lex)

        while lex.next.kind in ("PLUS", "MINUS"):
            operador = lex.next.kind
            lex.select_next()
            right = Parser.parse_term(lex)
            op_symbol = '+' if operador == "PLUS" else '-'
            node = BinOp(op_symbol, [node, right])

        return node

    @staticmethod
    def parse_term(lex):
        node = Parser.parse_factor(lex)

        while lex.next.kind in ("MULT", "DIV"):
            operador = lex.next.kind
            lex.select_next()
            right = Parser.parse_factor(lex)
            op_symbol = '*' if operador == "MULT" else '/'
            node = BinOp(op_symbol, [node, right])

        return node

    @staticmethod
    def parse_factor(lex):
        if lex.next.kind == "INT":
            node = IntVal(lex.next.value)
            lex.select_next()
            return node

        elif lex.next.kind == "PLUS":
            lex.select_next()
            return UnOp('+', [Parser.parse_factor(lex)])

        elif lex.next.kind == "MINUS":
            lex.select_next()
            return UnOp('-', [Parser.parse_factor(lex)])

        elif lex.next.kind == "OPEN_PAR":
            lex.select_next()
            node = Parser.parse_expression(lex)
            if lex.next.kind != "CLOSE_PAR":
                raise Exception("Faltando fechar parêntese")
            lex.select_next()
            return node

        else:
            raise Exception(f"Token inesperado: {lex.next.kind}")

    @staticmethod
    def run(source_code):
        lex = Lexer(source_code)
        lex.select_next()
        node = Parser.parse_expression(lex)

        if lex.next.kind != "EOF":
            raise Exception("Erro de sintaxe: tokens sobrando no fim da expressão")

        return node


# ---------------------------
# Main
# ---------------------------
def main():
    source_code = sys.stdin.read().strip()

    if not source_code:
        try:
            source_code = input().strip()
        except EOFError:
            source_code = ""

    if not source_code and len(sys.argv) > 1:
        source_code = " ".join(sys.argv[1:]).strip()

    if not source_code:
        raise Exception("Nenhum código recebido!")

    ast_root = Parser.run(source_code)
    resultado = ast_root.evaluate()
    print(resultado)


if __name__ == '__main__':
    main()
