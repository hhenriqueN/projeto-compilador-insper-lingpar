import sys
import re
from abc import ABC, abstractmethod

class PrePro:
    @staticmethod
    def filter(code: str) -> str:
        if re.search(r'([0-9A-Za-z\)])//([0-9A-Za-z\(])', code):
            raise Exception("Uso inválido de '//' como operador. Use '/' para divisão.")
        return re.sub(r'//.*', '', code)

class Token:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

class Lexer:
    RESERVED = {
        "Println": "PRINT",
        "if": "IF",
        "for": "WHILE",
        "else": "ELSE",
        "Scanln": "READ",
        "var": "VAR",
        "int": "TYPE",
        "string": "TYPE",
        "bool": "TYPE",
    }

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.next = None

    def _peek(self):
        if self.position < len(self.source):
            return self.source[self.position]
        return '\0'

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position] in (" ", "\t", "\r"):
            self.position += 1
        
        if self.position >= len(self.source):
            self.next = Token('EOF', '')
            return self.next
        
        ch = self.source[self.position]

        if ch == '\n':
            self.position += 1
            self.next = Token('END', '\n'); return self.next
        if ch == '"':
            self.position += 1
            buf = []
            while self.position < len(self.source) and self.source[self.position] != '"':
                buf.append(self.source[self.position])
                self.position += 1
            if self.position >= len(self.source):
                raise Exception("[Lexer] String não terminada")
            self.position += 1 # Consome o " final
            self.next = Token("STR", "".join(buf)); return self.next
        if ch == '(':
            self.position += 1; self.next = Token('OPEN_PAR', '('); return self.next
        if ch == ')':
            self.position += 1; self.next = Token('CLOSE_PAR', ')'); return self.next
        if ch == '{':
            self.position += 1; self.next = Token('OPEN_BRA', '{'); return self.next
        if ch == '}':
            self.position += 1; self.next = Token('CLOSE_BRA', '}'); return self.next
        if ch == '+':
            self.position += 1; self.next = Token('PLUS', '+'); return self.next
        if ch == '-':
            self.position += 1; self.next = Token('MINUS', '-'); return self.next
        if ch == '*':
            self.position += 1; self.next = Token('MULT', '*'); return self.next
        if ch == '/':
            self.position += 1; self.next = Token('DIV', '/'); return self.next
        if ch == '=':
            self.position += 1
            if self._peek() == '=':
                self.position += 1; self.next = Token('EQ', '==')
            else:
                self.next = Token('ASSIGN', '=')
            return self.next
        if ch == '>':
            self.position += 1; self.next = Token('GT', '>'); return self.next
        if ch == '<':
            self.position += 1; self.next = Token('LT', '<'); return self.next
        if ch == '&' and self._peek() == '&':
            self.position += 2; self.next = Token('AND', '&&'); return self.next
        if ch == '|' and self._peek() == '|':
            self.position += 2; self.next = Token('OR', '||'); return self.next
        if ch == '!':
            self.position += 1; self.next = Token('NOT', '!'); return self.next
        if ch.isdigit():
            num = []
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num.append(self.source[self.position])
                self.position += 1
            self.next = Token('INT', int(''.join(num))); return self.next
        if ch.isalpha():
            ident = []
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                ident.append(self.source[self.position]); self.position += 1
            ident_str = ''.join(ident)
            
            if ident_str == "true":
                self.next = Token("BOOL", True); return self.next
            if ident_str == "false":
                self.next = Token("BOOL", False); return self.next
            
            if ident_str in Lexer.RESERVED:
                self.next = Token(Lexer.RESERVED[ident_str], ident_str)
            else:
                self.next = Token('IDEN', ident_str)
            return self.next
        
        raise Exception(f"Caractere inválido: {ch}")

class Variable:
    def __init__(self, value, type: str):
        self.value = value
        self.type = type

class SymbolTable:
    def __init__(self):
        self._table = {}

    def create_variable(self, name: str, type: str):
        if name in self._table:
            raise Exception(f"[Semântico] Variável '{name}' já declarada.")
        self._table[name] = Variable(None, type)

    def set(self, name: str, var: Variable):
        if name not in self._table:
            raise Exception(f"[Semântico] Variável '{name}' não declarada.")
        if self._table[name].type != var.type:
            raise Exception(f"[Semântico] Atribuição de tipo inválido para '{name}'. Esperado '{self._table[name].type}', recebido '{var.type}'.")
        self._table[name] = var

    def get(self, name: str) -> Variable:
        if name not in self._table:
            raise Exception(f"[Semântico] Variável '{name}' não definida.")
        var = self._table[name]
        if var.value is None:
            raise Exception(f"[Semântico] Variável '{name}' usada antes de ser inicializada.")
        return var

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
        return Variable(self.value, "int")

class StringVal(Node):
    def __init__(self, value):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return Variable(self.value, "string")

class BoolVal(Node):
    def __init__(self, value):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return Variable(self.value, "bool")

class BinOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    
    def evaluate(self, st: SymbolTable):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        
        op = self.value

        if op == '+':
            def _coerce_to_string(var: Variable) -> str:
                if var.type == "string":
                    return var.value
                if var.type == "bool":
                    return str(var.value).lower()
                return str(var.value)

            if left.type == "int" and right.type == "int":
                return Variable(left.value + right.value, "int")
            
            if left.type == "string" or right.type == "string":
                return Variable(_coerce_to_string(left) + _coerce_to_string(right), "string")
            
            raise Exception("[Semântico] Operação '+' inválida para os tipos")

        if op in ('-', '*', '/'):
            if left.type != "int" or right.type != "int":
                raise Exception(f"[Semântico] Operador '{op}' requer dois inteiros.")
            if op == '/' and right.value == 0:
                raise Exception("[Semântico] Divisão por zero.")
            if op == '-': return Variable(left.value - right.value, "int")
            if op == '*': return Variable(left.value * right.value, "int")
            if op == '/': return Variable(left.value // right.value, "int")

        if op in ('==', '>', '<'):
            if left.type != right.type:
                raise Exception(f"[Semântico] Comparação '{op}' requer tipos iguais.")
            if op == '==': return Variable(left.value == right.value, "bool")
            if op == '>': return Variable(left.value > right.value, "bool")
            if op == '<': return Variable(left.value < right.value, "bool")
        
        if op in ('&&', '||'):
            if left.type != "bool" or right.type != "bool":
                raise Exception(f"[Semântico] Operador lógico '{op}' requer dois booleanos.")
            if op == '&&': return Variable(left.value and right.value, "bool")
            if op == '||': return Variable(left.value or right.value, "bool")

        raise Exception(f"Operador binário desconhecido: {op}")

class UnOp(Node):
    def __init__(self, value, children):
        super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        child = self.children[0].evaluate(st)
        op = self.value
        
        if op in ('+', '-'):
            if child.type != "int":
                raise Exception(f"[Semântico] Operador unário '{op}' requer um inteiro.")
            return Variable(+child.value if op == '+' else -child.value, "int")
        
        if op == '!':
            if child.type != "bool":
                raise Exception("[Semântico] Operador '!' requer um booleano.")
            return Variable(not child.value, "bool")
        
        raise Exception(f"Operador unário desconhecido: {op}")

class Identifier(Node):
    def __init__(self, value):
        super().__init__(value, [])
    def evaluate(self, st: SymbolTable):
        return st.get(self.value)

class VarDec(Node):
    def __init__(self, value, children):
        super().__init__(value, children) # value é o tipo (string)
    def evaluate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        st.create_variable(var_name, var_type)
        if len(self.children) > 1:
            expr_val = self.children[1].evaluate(st)
            st.set(var_name, expr_val)

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
        if val.type == "bool":
            print(str(val.value).lower())
        else:
            print(val.value)

class Block(Node):
    def __init__(self, children):
        super().__init__('block', children)
    def evaluate(self, st: SymbolTable):
        for child in self.children:
            child.evaluate(st)

class NoOp(Node):
    def __init__(self):
        super().__init__('noop', [])
    def evaluate(self, st: SymbolTable):
        return None

class Read(Node):
    def __init__(self):
        super().__init__('read', [])
    def evaluate(self, st: SymbolTable):
        try:
            return Variable(int(input().strip()), "int")
        except (ValueError, TypeError):
            raise Exception("[Semântico] Entrada de Scanln deve ser um inteiro.")

class If(Node):
    def __init__(self, children):
        super().__init__('if', children)
    def evaluate(self, st: SymbolTable):
        cond = self.children[0].evaluate(st)
        if cond.type != "bool":
            raise Exception("[Semântico] Condição do 'if' deve ser booleana.")
        if cond.value:
            self.children[1].evaluate(st)
        elif len(self.children) == 3:
            self.children[2].evaluate(st)

class While(Node):
    def __init__(self, children):
        super().__init__('while', children)
    def evaluate(self, st: SymbolTable):
        while True:
            cond = self.children[0].evaluate(st)
            if cond.type != "bool":
                raise Exception("[Semântico] Condição do 'while' deve ser booleana.")
            if not cond.value:
                break
            self.children[1].evaluate(st)

class Parser:
    @staticmethod
    def parseProgram(lex: Lexer):
        children = []
        while lex.next.kind != "EOF":
            stmt = Parser.parseStatement(lex)
            children.append(stmt)
        return Block(children)

    @staticmethod
    def parseBlock(lex: Lexer):
        if lex.next.kind != "OPEN_BRA":
            raise Exception("Esperado '{' para iniciar bloco")
        lex.select_next()
        if lex.next.kind == "CLOSE_BRA":
            raise Exception("Bloco '{ }' mal formatado (misaligned '}')")
        children = []
        while lex.next.kind != "CLOSE_BRA":
            if lex.next.kind == "END":
                lex.select_next()
                continue
            children.append(Parser.parseStatement(lex))
            if lex.next.kind == "EOF":
                raise Exception("Bloco não fechado antes do EOF")
        lex.select_next()
        return Block(children)

    @staticmethod
    def parseBoolExpression(lex: Lexer):
        node = Parser.parseBoolTerm(lex)
        while lex.next.kind == "OR":
            op = lex.next.value; lex.select_next()
            right = Parser.parseBoolTerm(lex)
            node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseBoolTerm(lex: Lexer):
        node = Parser.parseRelExpression(lex)
        while lex.next.kind == "AND":
            op = lex.next.value; lex.select_next()
            right = Parser.parseRelExpression(lex)
            node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseRelExpression(lex: Lexer):
        left = Parser.parseExpression(lex)
        if lex.next.kind in ("EQ", "GT", "LT"):
            op = lex.next.value; lex.select_next()
            right = Parser.parseExpression(lex)
            return BinOp(op, [left, right])
        return left

    @staticmethod
    def parseExpression(lex: Lexer):
        node = Parser.parseTerm(lex)
        while lex.next.kind in ("PLUS", "MINUS"):
            op = lex.next.value
            lex.select_next()
            if lex.next.kind == "EOF" or lex.next.kind == "END":
                raise Exception(f"[Parser] Expressão incompleta após o operador '{op}'")
            right = Parser.parseTerm(lex)
            node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseTerm(lex: Lexer):
        node = Parser.parseFactor(lex)
        while lex.next.kind in ("MULT", "DIV"):
            op = lex.next.value
            lex.select_next()
            if lex.next.kind == "EOF" or lex.next.kind == "END":
                raise Exception(f"[Parser] Expressão incompleta após o operador '{op}'")
            right = Parser.parseFactor(lex)
            node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseFactor(lex: Lexer):
        if lex.next.kind == "INT":
            node = IntVal(lex.next.value); lex.select_next(); return node
        if lex.next.kind == "STR":
            node = StringVal(lex.next.value); lex.select_next(); return node
        if lex.next.kind == "BOOL":
            node = BoolVal(lex.next.value); lex.select_next(); return node
        if lex.next.kind == "PLUS":
            lex.select_next(); return UnOp('+', [Parser.parseFactor(lex)])
        if lex.next.kind == "MINUS":
            lex.select_next(); return UnOp('-', [Parser.parseFactor(lex)])
        if lex.next.kind == "NOT":
            lex.select_next(); return UnOp('!', [Parser.parseFactor(lex)])
        if lex.next.kind == "OPEN_PAR":
            lex.select_next()
            node = Parser.parseBoolExpression(lex)
            if lex.next.kind != "CLOSE_PAR":
                raise Exception("Faltando fechar parêntese")
            lex.select_next()
            return node
        if lex.next.kind == "READ":
            lex.select_next()
            if lex.next.kind != "OPEN_PAR": raise Exception("Esperado '(' após Scanln")
            lex.select_next()
            if lex.next.kind != "CLOSE_PAR": raise Exception("Esperado ')'")
            lex.select_next()
            return Read()
        if lex.next.kind == "IDEN":
            node = Identifier(lex.next.value); lex.select_next(); return node
        
        raise Exception(f"Fator inválido. Token inesperado: {lex.next.kind}")

    @staticmethod
    def parseStatement(lex: Lexer):
        if lex.next.kind == "OPEN_BRA":
            return Parser.parseBlock(lex)
        
        if lex.next.kind == "VAR":
            lex.select_next() # Consome 'var'
            if lex.next.kind != "IDEN": raise Exception("Esperado identificador após 'var'")
            iden = Identifier(lex.next.value); lex.select_next()
            
            if lex.next.kind != "TYPE": raise Exception("Esperado tipo (int, string, bool) após identificador")
            var_type = lex.next.value; lex.select_next()
            
            children = [iden]
            if lex.next.kind == "ASSIGN":
                lex.select_next() # Consome '='
                expr = Parser.parseBoolExpression(lex)
                children.append(expr)
            
            if lex.next.kind != "END": raise Exception("Esperado fim de linha após declaração")
            lex.select_next()
            return VarDec(var_type, children)

        if lex.next.kind == "IF":
            lex.select_next()
            cond = Parser.parseBoolExpression(lex)
            if lex.next.kind != "OPEN_BRA": raise Exception("Esperado '{' após condição do if")
            then_stmt = Parser.parseBlock(lex)
            children = [cond, then_stmt]
            if lex.next.kind == "ELSE":
                lex.select_next()
                if lex.next.kind != "OPEN_BRA": raise Exception("Esperado '{' após 'else'")
                else_stmt = Parser.parseBlock(lex)
                children.append(else_stmt)
            return If(children)

        if lex.next.kind == "WHILE":
            lex.select_next()
            cond = Parser.parseBoolExpression(lex)
            if lex.next.kind != "OPEN_BRA": raise Exception("Esperado '{' após condição do for/while")
            body = Parser.parseBlock(lex)
            return While([cond, body])

        if lex.next.kind == "IDEN":
            iden = Identifier(lex.next.value); lex.select_next()
            if lex.next.kind != "ASSIGN": raise Exception("Esperado '=' para atribuição")
            lex.select_next()
            expr = Parser.parseBoolExpression(lex)
            if lex.next.kind != "END": raise Exception("Esperado fim de linha após atribuição")
            lex.select_next()
            return Assignment([iden, expr])

        if lex.next.kind == "PRINT":
            lex.select_next()
            if lex.next.kind != "OPEN_PAR": raise Exception("Esperado '(' após Println")
            lex.select_next()
            expr = Parser.parseBoolExpression(lex)
            if lex.next.kind != "CLOSE_PAR": raise Exception("Esperado ')'")
            lex.select_next()
            if lex.next.kind != "END": raise Exception("Esperado fim de linha após Println")
            lex.select_next()
            return Print([expr])

        if lex.next.kind == "END":
            lex.select_next()
            return NoOp()
        
        raise Exception(f"Instrução inválida. Token: {lex.next.kind}")

    @staticmethod
    def run(source_code):
        filtered_code = PrePro.filter(source_code)
        lex = Lexer(filtered_code)
        lex.select_next()
        ast = Parser.parseProgram(lex)
        if lex.next.kind != "EOF":
            raise Exception("[Parser] Código extra encontrado no final do arquivo.")
        return ast

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 main.py <arquivo.go>", file=sys.stderr)
        sys.exit(1)
        
    filename = sys.argv[1]
    try:
        with open(filename, "r", encoding='utf-8') as f:
            code = f.read()
        
        ast = Parser.run(code)
        st = SymbolTable()
        ast.evaluate(st)

    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()