import sys
import re
from abc import ABC, abstractmethod

class PrePro:
    @staticmethod
    def filter(code: str) -> str:
        if re.search(r'([0-9A-Za-z\)])//([0-9A-Za-z\(])', code):
            raise Exception("[Parser] Invalid use of '//' as an operator. Use '/' for division.")
        return re.sub(r'//.*', '', code)

class Token:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

class Lexer:
    RESERVED = {
        "Println": "PRINT", "if": "IF", "for": "WHILE", "else": "ELSE",
        "Scanln": "READ", "var": "VAR", "int": "TYPE", "string": "TYPE", "bool": "TYPE",
    }

    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.next = None

    def _peek(self):
        if self.position < len(self.source): return self.source[self.position]
        return '\0'

    def select_next(self):
        while self.position < len(self.source) and self.source[self.position] in (" ", "\t", "\r"):
            self.position += 1
        
        if self.position >= len(self.source):
            self.next = Token('EOF', ''); return
        
        ch = self.source[self.position]

        if ch == '\n': self.position += 1; self.next = Token('END', '\n'); return
        if ch == '"':
            self.position += 1; buf = []
            while self.position < len(self.source) and self.source[self.position] != '"':
                buf.append(self.source[self.position]); self.position += 1
            if self.position >= len(self.source): raise Exception("[Lexer] Unterminated string")
            self.position += 1; self.next = Token("STR", "".join(buf)); return
        if ch == '(': self.position += 1; self.next = Token('OPEN_PAR', '('); return
        if ch == ')': self.position += 1; self.next = Token('CLOSE_PAR', ')'); return
        if ch == '{': self.position += 1; self.next = Token('OPEN_BRA', '{'); return
        if ch == '}': self.position += 1; self.next = Token('CLOSE_BRA', '}'); return
        if ch == '+': self.position += 1; self.next = Token('PLUS', '+'); return
        if ch == '-': self.position += 1; self.next = Token('MINUS', '-'); return
        if ch == '*': self.position += 1; self.next = Token('MULT', '*'); return
        if ch == '/': self.position += 1; self.next = Token('DIV', '/'); return
        if ch == '=':
            self.position += 1
            if self._peek() == '=': self.position += 1; self.next = Token('EQ', '==')
            else: self.next = Token('ASSIGN', '=')
            return
        if ch == '>': self.position += 1; self.next = Token('GT', '>'); return
        if ch == '<': self.position += 1; self.next = Token('LT', '<'); return
        if ch == '&' and self._peek() == '&': self.position += 2; self.next = Token('AND', '&&'); return
        if ch == '|' and self._peek() == '|': self.position += 2; self.next = Token('OR', '||'); return
        if ch == '!': self.position += 1; self.next = Token('NOT', '!'); return
        if ch.isdigit():
            num = []
            while self.position < len(self.source) and self.source[self.position].isdigit():
                num.append(self.source[self.position]); self.position += 1
            self.next = Token('INT', int(''.join(num))); return
        if ch.isalpha():
            ident = []
            while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                ident.append(self.source[self.position]); self.position += 1
            ident_str = ''.join(ident)
            if ident_str == "true": self.next = Token("BOOL", True); return
            if ident_str == "false": self.next = Token("BOOL", False); return
            if ident_str in Lexer.RESERVED: self.next = Token(Lexer.RESERVED[ident_str], ident_str)
            else: self.next = Token('IDEN', ident_str)
            return
        raise Exception(f"[Lexer] Invalid character: {ch}")

class Variable:
    def __init__(self, value, type: str):
        self.value = value
        self.type = type

class SymbolTable:
    def __init__(self):
        self._table = {}

    def create_variable(self, name: str, type: str):
        if name in self._table:
            raise Exception(f"[Semantic] Variable '{name}' already declared.")
        self._table[name] = Variable(None, type)

    def set(self, name: str, var: Variable):
        if name not in self._table:
            raise Exception(f"[Semantic] Variable '{name}' not declared.")
        if self._table[name].type != var.type:
            raise Exception(f"[Semantic] Invalid type assignment for '{name}'. Expected '{self._table[name].type}', received '{var.type}'.")
        self._table[name] = var

    def get(self, name: str) -> Variable:
        if name not in self._table:
            raise Exception(f"[Semantic] Variable '{name}' not defined.")
        var = self._table[name]
        if var.value is None:
            raise Exception(f"[Semantic] Variable '{name}' used before initialization.")
        return var

class Node(ABC):
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or []
    @abstractmethod
    def evaluate(self, st: SymbolTable):
        pass

class IntVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "int")

class StringVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "string")

class BoolVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "bool")

class BinOp(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        left = self.children[0].evaluate(st)
        right = self.children[1].evaluate(st)
        op = self.value
        if op == '+':
            def _coerce_to_string(var: Variable) -> str:
                if var.type == "string": return var.value
                if var.type == "bool": return str(var.value).lower()
                return str(var.value)
            if left.type == "int" and right.type == "int": return Variable(left.value + right.value, "int")
            if left.type == "string" or right.type == "string": return Variable(_coerce_to_string(left) + _coerce_to_string(right), "string")
            raise Exception("[Semantic] Invalid types for '+' operation.")
        if op in ('-', '*', '/'):
            if left.type != "int" or right.type != "int": raise Exception(f"[Semantic] Operator '{op}' requires two integers.")
            if op == '/' and right.value == 0: raise Exception("[Semantic] Division by zero.")
            if op == '-': return Variable(left.value - right.value, "int")
            if op == '*': return Variable(left.value * right.value, "int")
            if op == '/': return Variable(left.value // right.value, "int")
        if op in ('==', '>', '<'):
            if left.type != right.type: raise Exception(f"[Semantic] Comparison '{op}' requires equal types.")
            if op == '==': return Variable(left.value == right.value, "bool")
            if op == '>': return Variable(left.value > right.value, "bool")
            if op == '<': return Variable(left.value < right.value, "bool")
        if op in ('&&', '||'):
            if left.type != "bool" or right.type != "bool": raise Exception(f"[Semantic] Logical operator '{op}' requires two booleans.")
            if op == '&&': return Variable(left.value and right.value, "bool")
            if op == '||': return Variable(left.value or right.value, "bool")
        raise Exception(f"[Semantic] Unknown binary operator: {op}")

class UnOp(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        child = self.children[0].evaluate(st)
        op = self.value
        if op in ('+', '-'):
            if child.type != "int": raise Exception(f"[Semantic] Unary operator '{op}' requires an integer.")
            return Variable(+child.value if op == '+' else -child.value, "int")
        if op == '!':
            if child.type != "bool": raise Exception("[Semantic] Operator '!' requires a boolean.")
            return Variable(not child.value, "bool")
        raise Exception(f"[Semantic] Unknown unary operator: {op}")

class Identifier(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return st.get(self.value)

class VarDec(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        st.create_variable(var_name, var_type)
        if len(self.children) > 1:
            expr_val = self.children[1].evaluate(st)
            if var_type != expr_val.type:
                raise Exception(f"[Semantic] Cannot use value of type '{expr_val.type}' to initialize variable '{var_name}' of type '{var_type}'.")
            st.set(var_name, expr_val)

class Assignment(Node):
    def __init__(self, children): super().__init__('=', children)
    def evaluate(self, st: SymbolTable):
        name = self.children[0].value
        val = self.children[1].evaluate(st)
        st.set(name, val)

class Print(Node):
    def __init__(self, children): super().__init__('print', children)
    def evaluate(self, st: SymbolTable):
        val = self.children[0].evaluate(st)
        if val.type == "bool": print(str(val.value).lower())
        else: print(val.value)

class Block(Node):
    def __init__(self, children): super().__init__('block', children)
    def evaluate(self, st: SymbolTable):
        for child in self.children: child.evaluate(st)

class NoOp(Node):
    def __init__(self): super().__init__('noop', [])
    def evaluate(self, st: SymbolTable): return None

class Read(Node):
    def __init__(self): super().__init__('read', [])
    def evaluate(self, st: SymbolTable):
        try: return Variable(int(input().strip()), "int")
        except (ValueError, TypeError): raise Exception("[Semantic] Scanln input must be an integer.")

class If(Node):
    def __init__(self, children): super().__init__('if', children)
    def evaluate(self, st: SymbolTable):
        cond = self.children[0].evaluate(st)
        if cond.type != "bool": raise Exception("[Semantic] 'if' condition must be a boolean.")
        if cond.value: self.children[1].evaluate(st)
        elif len(self.children) == 3: self.children[2].evaluate(st)

class While(Node):
    def __init__(self, children): super().__init__('while', children)
    def evaluate(self, st: SymbolTable):
        while True:
            cond = self.children[0].evaluate(st)
            if cond.type != "bool": raise Exception("[Semantic] 'while' condition must be a boolean.")
            if not cond.value: break
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
        if lex.next.kind != "OPEN_BRA": raise Exception("[Parser] Expected '{' to start a block")
        lex.select_next()
        if lex.next.kind == "CLOSE_BRA": raise Exception("[Parser] Malformed block '{ }' (misaligned '}')")
        children = []
        while lex.next.kind != "CLOSE_BRA":
            if lex.next.kind == "END": lex.select_next(); continue
            children.append(Parser.parseStatement(lex))
            if lex.next.kind == "EOF": raise Exception("[Parser] Block not closed before EOF")
        lex.select_next()
        return Block(children)

    @staticmethod
    def parseBoolExpression(lex: Lexer):
        node = Parser.parseBoolTerm(lex)
        while lex.next.kind == "OR":
            op = lex.next.value; lex.select_next()
            right = Parser.parseBoolTerm(lex); node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseBoolTerm(lex: Lexer):
        node = Parser.parseRelExpression(lex)
        while lex.next.kind == "AND":
            op = lex.next.value; lex.select_next()
            right = Parser.parseRelExpression(lex); node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseRelExpression(lex: Lexer):
        left = Parser.parseExpression(lex)
        if lex.next.kind in ("EQ", "GT", "LT"):
            op = lex.next.value; lex.select_next()
            right = Parser.parseExpression(lex); return BinOp(op, [left, right])
        return left

    @staticmethod
    def parseExpression(lex: Lexer):
        node = Parser.parseTerm(lex)
        while lex.next.kind in ("PLUS", "MINUS"):
            op = lex.next.value; lex.select_next()
            if lex.next.kind == "EOF" or lex.next.kind == "END": raise Exception(f"[Parser] Incomplete expression after operator '{op}'")
            right = Parser.parseTerm(lex); node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseTerm(lex: Lexer):
        node = Parser.parseFactor(lex)
        while lex.next.kind in ("MULT", "DIV"):
            op = lex.next.value; lex.select_next()
            if lex.next.kind == "EOF" or lex.next.kind == "END": raise Exception(f"[Parser] Incomplete expression after operator '{op}'")
            right = Parser.parseFactor(lex); node = BinOp(op, [node, right])
        return node

    @staticmethod
    def parseFactor(lex: Lexer):
        if lex.next.kind == "INT": node = IntVal(lex.next.value); lex.select_next(); return node
        if lex.next.kind == "STR": node = StringVal(lex.next.value); lex.select_next(); return node
        if lex.next.kind == "BOOL": node = BoolVal(lex.next.value); lex.select_next(); return node
        if lex.next.kind == "PLUS":
            op = lex.next.value; lex.select_next()
            if lex.next.kind in ("EOF", "END"): raise Exception(f"[Parser] Incomplete expression after unary operator '{op}'")
            return UnOp('+', [Parser.parseFactor(lex)])
        if lex.next.kind == "MINUS":
            op = lex.next.value; lex.select_next()
            if lex.next.kind in ("EOF", "END"): raise Exception(f"[Parser] Incomplete expression after unary operator '{op}'")
            return UnOp('-', [Parser.parseFactor(lex)])
        if lex.next.kind == "NOT":
            op = lex.next.value; lex.select_next()
            if lex.next.kind in ("EOF", "END"): raise Exception(f"[Parser] Incomplete expression after unary operator '{op}'")
            return UnOp('!', [Parser.parseFactor(lex)])
        if lex.next.kind == "OPEN_PAR":
            lex.select_next(); node = Parser.parseBoolExpression(lex)
            if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Missing closing parenthesis")
            lex.select_next(); return node
        if lex.next.kind == "READ":
            lex.select_next()
            if lex.next.kind != "OPEN_PAR": raise Exception("[Parser] Expected '(' after Scanln")
            lex.select_next()
            if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Expected ')' after Scanln")
            lex.select_next(); return Read()
        if lex.next.kind == "IDEN": node = Identifier(lex.next.value); lex.select_next(); return node
        if lex.next.kind in ("MULT", "DIV"):
            op_val = lex.next.value; raise Exception(f"[Parser] Expression cannot start with binary operator '{op_val}'")
        raise Exception(f"[Parser] Invalid factor or start of expression. Unexpected token: {lex.next.kind}")

    @staticmethod
    def parseStatement(lex: Lexer):
        if lex.next.kind == "OPEN_BRA": return Parser.parseBlock(lex)
        
        node = None
        if lex.next.kind == "VAR":
            lex.select_next()
            if lex.next.kind != "IDEN": raise Exception("[Parser] Expected identifier after 'var'")
            iden = Identifier(lex.next.value); lex.select_next()
            if lex.next.kind != "TYPE": raise Exception("[Parser] Expected type (int, string, bool) after identifier")
            var_type = lex.next.value; lex.select_next()
            children = [iden]
            if lex.next.kind == "ASSIGN":
                lex.select_next()
                if lex.next.kind in ("END", "EOF"): raise Exception("[Parser] Expected expression after '=' in declaration")
                expr = Parser.parseBoolExpression(lex); children.append(expr)
            node = VarDec(var_type, children)
        elif lex.next.kind == "IF":
            lex.select_next(); cond = Parser.parseBoolExpression(lex)
            if lex.next.kind != "OPEN_BRA": raise Exception("[Parser] Expected '{' after if condition")
            then_stmt = Parser.parseBlock(lex); children = [cond, then_stmt]
            if lex.next.kind == "ELSE":
                lex.select_next()
                if lex.next.kind != "OPEN_BRA": raise Exception("[Parser] Expected '{' after 'else'")
                else_stmt = Parser.parseBlock(lex); children.append(else_stmt)
            return If(children)
        elif lex.next.kind == "WHILE":
            lex.select_next(); cond = Parser.parseBoolExpression(lex)
            if lex.next.kind != "OPEN_BRA": raise Exception("[Parser] Expected '{' after while condition")
            body = Parser.parseBlock(lex); return While([cond, body])
        elif lex.next.kind == "IDEN":
            iden = Identifier(lex.next.value); lex.select_next()
            if lex.next.kind != "ASSIGN": raise Exception("[Parser] Expected '=' for assignment")
            lex.select_next(); expr = Parser.parseBoolExpression(lex)
            node = Assignment([iden, expr])
        elif lex.next.kind == "PRINT":
            lex.select_next()
            if lex.next.kind != "OPEN_PAR": raise Exception("[Parser] Expected '(' after Println")
            lex.select_next(); expr = Parser.parseBoolExpression(lex)
            if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Expected ')' after Println expression")
            lex.select_next(); node = Print([expr])
        elif lex.next.kind == "END":
            lex.select_next(); return NoOp()
        else:
            raise Exception(f"[Parser] Invalid statement. Token: {lex.next.kind}")

        if lex.next.kind == "END":
            lex.select_next(); return node
        elif lex.next.kind == "EOF":
            return node
        else:
            raise Exception(f"[Parser] Unexpected token '{lex.next.value}' after statement. Expected end of line.")

    @staticmethod
    def run(source_code):
        filtered_code = PrePro.filter(source_code)
        lex = Lexer(filtered_code)
        lex.select_next()
        ast = Parser.parseProgram(lex)
        if lex.next.kind != "EOF":
            raise Exception("[Parser] Extra code found at the end of the file.")
        return ast

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <file.go>", file=sys.stderr); sys.exit(1)
    filename = sys.argv[1]
    try:
        with open(filename, "r", encoding='utf-8') as f: code = f.read()
        ast = Parser.run(code)
        st = SymbolTable()
        ast.evaluate(st)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.", file=sys.stderr); sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()