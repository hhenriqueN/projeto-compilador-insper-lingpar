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
        "func": "FUNC", "return": "RETURN"
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
        if self.position >= len(self.source): self.next = Token('EOF', ''); return
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
        if ch == ',':
            self.position += 1; self.next = Token('COMMA', ','); return
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

class Code:
    instructions = []
    @staticmethod
    def append(code: str):
        if code is None:
            return
        Code.instructions.append(code)
    @staticmethod
    def header():
        return (
            "section .data\n"
            "  format_out: db \"%d\", 10, 0\n"
            "  format_in: db \"%d\", 0\n"
            "  scan_int: dd 0\n\n"
            "section .text\n\n"
            "  extern printf\n"
            "  extern scanf\n"
            "  global _start\n\n"
            "_start:\n"
            "  push ebp\n"
            "  mov ebp, esp\n\n"
        )
    @staticmethod
    def footer():
        return(
            "\n  mov esp, ebp\n"
            "  pop ebp\n"
            "  mov eax, 1\n"
            "  xor ebx, ebx\n"
            "  int 0x80\n"
        )
    @staticmethod
    def dump(filename: str):
        body = "\n".join(Code.instructions)
        content = Code.header() + body + Code.footer()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + "\n")

class Variable:
    def __init__(self, value, type: str, shift=None, func: bool=False):
        self.value = value
        self.type = type
        self.shift = shift
        self.func = func

class SymbolTable:
    def __init__(self, parent=None):
        self._table = {}
        self._shift = 0
        self.parent = parent
    def create_variable(self, name: str, type: str) -> int:
        if name in self._table:
            raise Exception(f"[Semantic] Variable '{name}' already declared.")
        self._shift -= 4
        self._table[name] = Variable(None, type, self._shift, func=False)
        return self._shift
    def create_function(self, name: str, func_node, return_type: str):
        if name in self._table:
            raise Exception(f"[Semantic] Variable '{name}' already declared.")
        self._table[name] = Variable(func_node, return_type, None, func=True)
    def set(self, name: str, var: Variable):
        if name in self._table:
            stored_var = self._table[name]
            if stored_var.func:
                raise Exception(f"[Semantic] '{name}' is a function and cannot be assigned.")
            if stored_var.type != var.type:
                raise Exception(f"[Semantic] Invalid type assignment for '{name}'. Expected '{stored_var.type}', received '{var.type}'.")
            stored_var.value = var.value
            return
        if self.parent:
            self.parent.set(name, var)
            return
        raise Exception(f"[Semantic] Variable '{name}' not declared.")
    def get(self, name: str) -> Variable:
        if name in self._table:
            var = self._table[name]
            if not var.func and var.value is None:
                raise Exception(f"[Semantic] Variable '{name}' used before initialization.")
            return var
        if self.parent:
            return self.parent.get(name)
        raise Exception(f"[Semantic] Variable '{name}' not defined.")
    def get_shift(self, name: str) -> int:
        if name in self._table:
            if self._table[name].shift is None:
                raise Exception(f"[Semantic] Internal Compiler Error: No shift assigned for '{name}'.")
            return self._table[name].shift
        if self.parent:
            return self.parent.get_shift(name)
        raise Exception(f"[Semantic] Variable '{name}' not declared.")

class Node(ABC):
    id = 0
    def __init__(self, value, children=None, id=0):
        self.value = value
        self.children = children or []
        self.my_id = Node.newId()
    @abstractmethod
    def evaluate(self, st: SymbolTable): pass
    @abstractmethod
    def generate(self, st: SymbolTable): pass
    @staticmethod
    def newId():
        Node.id += 1
        return Node.id

class IntVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "int")
    def generate(self, st: SymbolTable): Code.append(f"  mov eax, {self.value}")

class StringVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "string")
    def generate(self, st: SymbolTable): Code.append(f"  ; string")

class BoolVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "bool")
    def generate(self, st: SymbolTable): Code.append(f"  mov eax, {1 if self.value else 0}")

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
    def generate(self, st: SymbolTable):
        self.children[1].generate(st)
        Code.append("  push eax")
        self.children[0].generate(st)
        Code.append("  pop ecx")
        op = self.value
        if op == '+': Code.append("  add eax, ecx")
        elif op == '-': Code.append("  sub eax, ecx")
        elif op == '*': Code.append("  imul eax, ecx")
        elif op == '/': Code.append("  cdq"); Code.append("  idiv ecx")
        elif op in ('==', '>', '<'):
            Code.append("  cmp eax, ecx"); Code.append("  mov eax, 0"); Code.append("  mov ecx, 1")
            if op == '==': Code.append("  cmove eax, ecx")
            if op == '>': Code.append("  cmovg eax, ecx")
            if op == '<': Code.append("  cmovl eax, ecx")
        elif op == '&&': Code.append("  and eax, ecx")
        elif op == '||': Code.append("  or eax, ecx")

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
    def generate(self, st: SymbolTable):
        self.children[0].generate(st)
        op = self.value
        if op == '-': Code.append("  neg eax")
        if op == '!':
            Code.append("  cmp eax, 0"); Code.append("  mov eax, 0"); Code.append("  mov ecx, 1"); Code.append("  cmove eax, ecx")

class Identifier(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return st.get(self.value)
    def generate(self, st: SymbolTable):
        shift = st.get_shift(self.value)
        Code.append(f"  mov eax, [ebp{shift}]")

class VarDec(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        has_init = len(self.children) > 1
        if var_type is None:
            raise Exception(f"[Semantic] Missing type in 'var' declaration for '{var_name}'. Use: var {var_name} <type> [= expr]")
        st.create_variable(var_name, var_type)
        if has_init:
            expr_val = self.children[1].evaluate(st)
            if var_type != expr_val.type:
                raise Exception(f"[Semantic] Cannot use value of type '{expr_val.type}' to initialize variable '{var_name}' of type '{var_type}'.")
            st.set(var_name, expr_val)
    def generate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        has_init = len(self.children) > 1
        shift = st.create_variable(var_name, var_type)
        Code.append(f"  sub esp, 4")
        if has_init:
            self.children[1].generate(st)
            Code.append(f"  mov [ebp{shift}], eax")

class Assignment(Node):
    def __init__(self, children): super().__init__('=', children)
    def evaluate(self, st: SymbolTable):
        name = self.children[0].value
        val = self.children[1].evaluate(st)
        st.set(name, val)
    def generate(self, st: SymbolTable):
        name = self.children[0].value
        shift = st.get_shift(name)
        self.children[1].generate(st)
        Code.append(f"  mov [ebp{shift}], eax")

class Print(Node):
    def __init__(self, children): super().__init__('print', children)
    def evaluate(self, st: SymbolTable):
        val = self.children[0].evaluate(st)
        if val.type == "bool": print(str(val.value).lower())
        else: print(val.value)
    def generate(self, st: SymbolTable):
        self.children[0].generate(st)
        Code.append("  push eax"); Code.append("  push format_out"); Code.append("  call printf"); Code.append("  add esp, 8")

class Block(Node):
    def __init__(self, children): super().__init__('block', children)
    def evaluate(self, st: SymbolTable):
        for child in self.children:
            if isinstance(child, Block):
                child_st = SymbolTable(parent=st)
                ret = child.evaluate(child_st)
                if isinstance(ret, Variable): return ret
            else:
                res = child.evaluate(st)
                if isinstance(res, Variable): return res
        return None
    def generate(self, st: SymbolTable):
        for child in self.children:
            child.generate(st)

class NoOp(Node):
    def __init__(self): super().__init__('noop', [])
    def evaluate(self, st: SymbolTable): return None
    def generate(self, st: SymbolTable): pass

class Read(Node):
    def __init__(self): super().__init__('read', [])
    def evaluate(self, st: SymbolTable):
        try: return Variable(int(input().strip()), "int")
        except (ValueError, TypeError): raise Exception("[Semantic] Scanln input must be an integer.")
    def generate(self, st: SymbolTable):
        Code.append("  push scan_int"); Code.append("  push format_in"); Code.append("  call scanf"); Code.append("  add esp, 8"); Code.append("  mov eax, dword [scan_int]")

class If(Node):
    def __init__(self, children): super().__init__('if', children)
    def evaluate(self, st: SymbolTable):
        cond = self.children[0].evaluate(st)
        if cond.type != "bool": raise Exception("[Semantic] 'if' condition must be a boolean.")
        if cond.value:
            ret = self.children[1].evaluate(st)
            if isinstance(ret, Variable): return ret
        elif len(self.children) == 3:
            ret = self.children[2].evaluate(st)
            if isinstance(ret, Variable): return ret
    def generate(self, st: SymbolTable):
        has_else = len(self.children) == 3
        label_else = f"L_else_{self.my_id}"
        label_endif = f"L_endif_{self.my_id}"
        self.children[0].generate(st)
        Code.append("  cmp eax, 0")
        if has_else: Code.append(f"  je {label_else}")
        else: Code.append(f"  je {label_endif}")
        self.children[1].generate(st)
        if has_else:
            Code.append(f"  jmp {label_endif}"); Code.append(f"{label_else}:"); self.children[2].generate(st)
        Code.append(f"{label_endif}:")

class While(Node):
    def __init__(self, children): super().__init__('while', children)
    def evaluate(self, st: SymbolTable):
        while True:
            cond = self.children[0].evaluate(st)
            if cond.type != "bool": raise Exception("[Semantic] 'while' condition must be a boolean.")
            if not cond.value: break
            ret = self.children[1].evaluate(st)
            if isinstance(ret, Variable): return ret
    def generate(self, st: SymbolTable):
        label_loop = f"L_loop_{self.my_id}"
        label_exit = f"L_exit_{self.my_id}"
        Code.append(f"{label_loop}:")
        self.children[0].generate(st)
        Code.append("  cmp eax, 0")
        Code.append(f"  je {label_exit}")
        self.children[1].generate(st)
        Code.append(f"  jmp {label_loop}")
        Code.append(f"{label_exit}:")

class FuncDec(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        name = self.children[0].value
        st.create_function(name, self, self.value)
    def generate(self, st: SymbolTable):
        Code.append(f"  ; func {self.children[0].value}")

class FuncCall(Node):
    def __init__(self, value, children): super().__init__(value, children)
    def evaluate(self, st: SymbolTable):
        try:
            func_var = st.get(self.value)
        except Exception:
            raise Exception("[Semantic] Function not declared or invalid call.")
        if not func_var.func:
            raise Exception("[Semantic] Call to non-function.")
        func_node: FuncDec = func_var.value
        declared_params = func_node.children[1:-1]
        if len(self.children) != len(declared_params):
            raise Exception("[Semantic] Incorrect number of arguments in function call.")
        call_st = SymbolTable(parent=st)
        for idx, p in enumerate(declared_params):
            ident = p.children[0].value
            ptype = p.value
            call_st.create_variable(ident, ptype)
            arg_val = self.children[idx].evaluate(st)
            if arg_val.type != ptype:
                raise Exception(f"[Semantic] Argument type mismatch in call to '{self.value}' for parameter '{ident}'.")
            call_st.set(ident, arg_val)
        body = func_node.children[-1]
        ret = body.evaluate(call_st)
        if func_node.value is None:
            if isinstance(ret, Variable):
                raise Exception("[Semantic] Void function returned a value.")
            return None
        else:
            if isinstance(ret, Variable):
                if ret.type != func_node.value:
                    raise Exception(f"[Semantic] Function '{self.value}' returned wrong type. Expected '{func_node.value}', got '{ret.type}'.")
                return ret
            raise Exception(f"[Semantic] Function '{self.value}' missing return (expected '{func_node.value}').")
    def generate(self, st: SymbolTable):
        Code.append(f"  ; call {self.value}")

class Return(Node):
    def __init__(self, children): super().__init__('return', children)
    def evaluate(self, st: SymbolTable):
        val = self.children[0].evaluate(st)
        return val
    def generate(self, st: SymbolTable):
        if self.children:
            self.children[0].generate(st)
        Code.append("  ; return")

class Parser:
    @staticmethod
    def parseProgram(lex: Lexer):
        children = []
        while lex.next.kind != "EOF":
            if lex.next.kind == "END":
                lex.select_next()
                continue
            if lex.next.kind == "FUNC":
                func = Parser.parse_func_declaration(lex)
                children.append(func)
                continue
            stmt = Parser.parseStatement(lex)
            children.append(stmt)
        children.append(FuncCall("main", []))
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
        if lex.next.kind == "IDEN":
            name = lex.next.value
            lex.select_next()
            if lex.next.kind == "OPEN_PAR":
                lex.select_next()
                args = []
                if lex.next.kind != "CLOSE_PAR":
                    args.append(Parser.parseBoolExpression(lex))
                    while lex.next.kind == "COMMA":
                        lex.select_next()
                        args.append(Parser.parseBoolExpression(lex))
                if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Missing closing parenthesis in function call")
                lex.select_next()
                return FuncCall(name, args)
            else:
                return Identifier(name)
        if lex.next.kind in ("MULT", "DIV"):
            op_val = lex.next.value; raise Exception(f"[Parser] Expression cannot start with binary operator '{op_val}'")
        raise Exception(f"[Parser] Invalid factor or start of expression. Unexpected token: {lex.next.kind}")
    @staticmethod
    def parseStatement(lex: Lexer):
        if lex.next.kind == "OPEN_BRA": return Parser.parseBlock(lex)
        node = None
        if lex.next.kind == "VAR":
            lex.select_next()
            if lex.next.kind != "IDEN":
                raise Exception("[Parser] Expected identifier after 'var'")
            iden = Identifier(lex.next.value)
            lex.select_next()
            if lex.next.kind != "TYPE":
                raise Exception("[Parser] TYPE not found")
            var_type = lex.next.value
            lex.select_next()
            children = [iden]
            if lex.next.kind == "ASSIGN":
                lex.select_next()
                if lex.next.kind in ("END", "EOF"):
                    raise Exception("[Parser] Expected expression after '=' in declaration")
                expr = Parser.parseBoolExpression(lex)
                children.append(expr)
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
            if lex.next.kind == "ASSIGN":
                lex.select_next(); expr = Parser.parseBoolExpression(lex)
                node = Assignment([iden, expr])
            elif lex.next.kind == "OPEN_PAR":
                lex.select_next()
                args = []
                if lex.next.kind != "CLOSE_PAR":
                    args.append(Parser.parseBoolExpression(lex))
                    while lex.next.kind == "COMMA":
                        lex.select_next()
                        args.append(Parser.parseBoolExpression(lex))
                if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Missing closing parenthesis in function call")
                lex.select_next()
                node = FuncCall(iden.value, args)
            else:
                raise Exception("[Parser] Expected '=' for assignment or '(' for function call")
        elif lex.next.kind == "PRINT":
            lex.select_next()
            if lex.next.kind != "OPEN_PAR": raise Exception("[Parser] Expected '(' after Println")
            lex.select_next(); expr = Parser.parseBoolExpression(lex)
            if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Expected ')' after Println expression")
            lex.select_next(); node = Print([expr])
        elif lex.next.kind == "END":
            lex.select_next(); return NoOp()
        elif lex.next.kind == "RETURN":
            lex.select_next()
            expr = Parser.parseBoolExpression(lex)
            node = Return([expr])
        else:
            raise Exception(f"[Parser] Invalid statement. Token: {lex.next.kind}")
        if lex.next.kind == "END":
            lex.select_next(); return node
        elif lex.next.kind == "EOF":
            return node
        else:
            raise Exception(f"[Parser] Unexpected token '{lex.next.value}' after statement. Expected end of line.")
    @staticmethod
    def parse_func_declaration(lex: Lexer):
        lex.select_next()
        if lex.next.kind != "IDEN": raise Exception("[Parser] Expected function name after 'func'")
        func_name = lex.next.value
        ident_node = Identifier(func_name)
        lex.select_next()
        if lex.next.kind != "OPEN_PAR": raise Exception("[Parser] Expected '(' after function name")
        lex.select_next()
        params = []
        if lex.next.kind != "CLOSE_PAR":
            while True:
                if lex.next.kind != "IDEN": raise Exception("[Parser] Expected parameter name")
                param_name = lex.next.value
                param_ident = Identifier(param_name)
                lex.select_next()
                if lex.next.kind != "TYPE": raise Exception("[Parser] Expected parameter type after name")
                param_type = lex.next.value
                lex.select_next()
                params.append(VarDec(param_type, [param_ident]))
                if lex.next.kind == "COMMA":
                    lex.select_next()
                    continue
                break
        if lex.next.kind != "CLOSE_PAR": raise Exception("[Parser] Missing ')' after function parameters")
        lex.select_next()
        ret_type = None
        if lex.next.kind == "TYPE":
            ret_type = lex.next.value
            lex.select_next()
        body = Parser.parseBlock(lex)
        children = [ident_node] + params + [body]
        return FuncDec(ret_type, children)
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
    if filename.endswith(".go"):
        output_filename = filename[:-3] + ".asm"
    else:
        output_filename = filename + ".asm"
    try:
        with open(filename, "r", encoding="utf-8") as f: code = f.read()
        ast = Parser.run(code)
        st = SymbolTable()
        ast.evaluate(st)
        ast.generate(st)
        Code.dump(output_filename)
        print(f"Assembly code successfully generated: {output_filename}")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.", file=sys.stderr); sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()
