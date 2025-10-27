import sys
import re
from abc import ABC, abstractmethod

class PrePro:
    @staticmethod
    def filter(code: str) -> str:
        # [Parser] Erro de sintaxe, pois a regra da linguagem proíbe o uso de '//' como operador.
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
        while self.position < len(self.source) and self.source[self.position] in (" ", "\t", "\r"): self.position += 1
        if self.position >= len(self.source): self.next = Token('EOF', ''); return
        ch = self.source[self.position]
        if ch == '\n': self.position += 1; self.next = Token('END', '\n'); return
        if ch == '"':
            self.position += 1; buf = []
            while self.position < len(self.source) and self.source[self.position] != '"':
                buf.append(self.source[self.position]); self.position += 1
            # [Lexer] Erro de token malformado.
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
        # [Lexer] Erro de caractere inválido que não pertence a nenhum token.
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
            "  format_out: db \"%d\", 10, 0 ; format do printf\n"
            "  format_in: db \"%d\", 0 ; format do scanf\n"
            "  scan_int: dd 0; 32-bits integer\n\n"
            "section .text\n\n"
            "  extern printf ; usar _printf para Windows\n"
            "  extern scanf ; usar _scanf para Windows\n"
            "  ; extern _ExitProcess@4 ; usar para Windows\n"
            "  global _start ; início do programa\n\n"
            "_start:\n"
            "  push ebp ; guarda o EBP\n"
            "  mov ebp, esp ; zera a pilha\n\n"
            "  ; aqui começa o codigo gerado:\n"
        )
    
    @staticmethod
    def footer():
        return(
            "\n  ; aqui termina o código gerado\n\n"
            "  mov esp, ebp ; reestabelece a pilha\n"
            "  pop ebp\n\n"
            "  ; chamada da interrupcao de saida (Linux)\n"
            "  mov eax, 1   \n"
            "  xor ebx, ebx \n"
            "  int 0x80     \n"
            "  ; Para Windows:\n"
            "  ; push dword 0        \n"
            "  ; call _ExitProcess@4\n"
        )
    
    @staticmethod
    def dump(filename: str):
        body = "\n".join(Code.instructions)
        content = Code.header() + body + Code.footer()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content + "\n")

    

class Variable:
    def __init__(self, value, type: str, shift=None):
        self.value = value
        self.type = type
        self.shift = shift

class SymbolTable:
    # A SymbolTable é o coração da análise semântica. Todos os erros aqui são [Semantic].
    def __init__(self):
        self._table = {}
        self._shift = 0 

    def create_variable(self, name: str, type: str) -> int:
        if name in self._table:
            raise Exception(f"[Semantic] Variable '{name}' already declared.")
        
        self._shift -= 4
        self._table[name] = Variable(None, type, self._shift)
        return self._shift 

    def set(self, name: str, var: Variable):
        if name not in self._table:
            raise Exception(f"[Semantic] Variable '{name}' not declared.")
        
        stored_var = self._table[name]
        if stored_var.type != var.type:
            raise Exception(f"[Semantic] Invalid type assignment for '{name}'. Expected '{stored_var.type}', received '{var.type}'.")
       
        stored_var.value = var.value

    def get(self, name: str) -> Variable:
        if name not in self._table:
            raise Exception(f"[Semantic] Variable '{name}' not defined.")
        var = self._table[name]
        
        if var.value is None:
            raise Exception(f"[Semantic] Variable '{name}' used before initialization.")
        return var

    def get_shift(self, name: str) -> int:
        if name not in self._table:
            raise Exception(f"[Semantic] Variable '{name}' not declared.")
        if self._table[name].shift is None:
             raise Exception(f"[Semantic] Internal Compiler Error: No shift assigned for '{name}'.")
        return self._table[name].shift

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
    
    def generate(self, st: SymbolTable):
        Code.append(f"  mov eax, {self.value}")

class StringVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "string")

    def generate(self, st: SymbolTable):
        Code.append(f"  ; StringVal '{self.value}' not implemented")

class BoolVal(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return Variable(self.value, "bool")

    def generate(self, st: SymbolTable):
        Code.append(f"  mov eax, {1 if self.value else 0}")

class BinOp(Node):
    # Erros em BinOp são semânticos, pois a sintaxe está correta, mas a lógica (tipos) não.
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
        elif op == '/':
            Code.append("  cdq")
            Code.append("  idiv ecx")
        
        elif op in ('==', '>', '<'):
            Code.append("  cmp eax, ecx")
            Code.append("  mov eax, 0")
            Code.append("  mov ecx, 1")
            if op == '==': Code.append("  cmove eax, ecx")
            if op == '>': Code.append("  cmovg eax, ecx")
            if op == '<': Code.append("  cmovl eax, ecx")
        
        elif op == '&&': Code.append("  and eax, ecx")
        elif op == '||': Code.append("  or eax, ecx")

class UnOp(Node):
    # Erros em UnOp são semânticos.
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
        if op == '+': pass
        if op == '!':
            Code.append("  cmp eax, 0")
            Code.append("  mov eax, 0")
            Code.append("  mov ecx, 1")
            Code.append("  cmove eax, ecx")

class Identifier(Node):
    def __init__(self, value): super().__init__(value, [])
    def evaluate(self, st: SymbolTable): return st.get(self.value)

    def generate(self, st: SymbolTable):
        shift = st.get_shift(self.value)
        Code.append(f"  mov eax, [ebp{shift}] ; recupera {self.value}")

class VarDec(Node):
    # Neste modelo, a ausência de TYPE é um erro SEMÂNTICO,
    # mesmo quando há inicialização.
    def __init__(self, value, children):
        super().__init__(value, children)

    def evaluate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        has_init = len(self.children) > 1

        if var_type is None:
            raise Exception(
                f"[Semantic] Missing type in 'var' declaration for '{var_name}'. "
                f"Use: var {var_name} <type> [= expr]"
            )

        st.create_variable(var_name, var_type)
        
        if has_init:
            expr_val = self.children[1].evaluate(st)
            if var_type != expr_val.type:
                raise Exception(
                    f"[Semantic] Cannot use value of type '{expr_val.type}' to initialize "
                    f"variable '{var_name}' of type '{var_type}'."
                )
            st.set(var_name, expr_val)

    def generate(self, st: SymbolTable):
        var_name = self.children[0].value
        var_type = self.value
        has_init = len(self.children) > 1

        shift = st.create_variable(var_name, var_type)
        
        Code.append(f"  sub esp, 4 ; var {var_name} {var_type} [EBP{shift}]")
        
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
        
        Code.append(f"  mov [ebp{shift}], eax ; {name} = EAX")

class Print(Node):
    def __init__(self, children): super().__init__('print', children)
    def evaluate(self, st: SymbolTable):
        val = self.children[0].evaluate(st)
        if val.type == "bool": print(str(val.value).lower())
        else: print(val.value)

    def generate(self, st: SymbolTable):
        self.children[0].generate(st)
        
        Code.append("  push eax")
        Code.append("  push format_out")
        Code.append("  call printf")
        Code.append("  add esp, 8 ; limpa argumentos da pilha")

class Block(Node):
    def __init__(self, children): super().__init__('block', children)
    def evaluate(self, st: SymbolTable):
        for child in self.children: child.evaluate(st)

    def generate(self, st: SymbolTable):
        for child in self.children:
            child.generate(st)

class NoOp(Node):
    def __init__(self): super().__init__('noop', [])
    def evaluate(self, st: SymbolTable): return None

    def generate(self, st: SymbolTable):
        pass

class Read(Node):
    def __init__(self): super().__init__('read', [])
    def evaluate(self, st: SymbolTable):
        try: return Variable(int(input().strip()), "int")
        # [Semantic] Erro de tipo em tempo de execução.
        except (ValueError, TypeError): raise Exception("[Semantic] Scanln input must be an integer.")

    def generate(self, st: SymbolTable):
        Code.append("  push scan_int ; endereço de memória de suporte")
        Code.append("  push format_in ; formato de entrada (int)")
        Code.append("  call scanf")
        Code.append("  add esp, 8 ; Remove os argumentos da pilha")
        Code.append("  mov eax, dword [scan_int]")


class If(Node):
    def __init__(self, children): super().__init__('if', children)
    def evaluate(self, st: SymbolTable):
        cond = self.children[0].evaluate(st)
        # [Semantic] A sintaxe 'if (1+1)' é válida, mas o significado é incorreto.
        if cond.type != "bool": raise Exception("[Semantic] 'if' condition must be a boolean.")
        if cond.value: self.children[1].evaluate(st)
        elif len(self.children) == 3: self.children[2].evaluate(st)

    def generate(self, st: SymbolTable):
        has_else = len(self.children) == 3
        
        label_else = f"L_else_{self.my_id}"
        label_endif = f"L_endif_{self.my_id}"

        self.children[0].generate(st)
        
        Code.append("  cmp eax, 0")
        
        if has_else:
            Code.append(f"  je {label_else}")
        else:
            Code.append(f"  je {label_endif}")
            
        self.children[1].generate(st)
        
        if has_else:
            Code.append(f"  jmp {label_endif}")
            Code.append(f"{label_else}:")
            self.children[2].generate(st)
            
        Code.append(f"{label_endif}:")


class While(Node):
    def __init__(self, children): super().__init__('while', children)
    def evaluate(self, st: SymbolTable):
        while True:
            cond = self.children[0].evaluate(st)
            # [Semantic] A sintaxe 'while (variavel_int)' é válida, mas o significado é incorreto.
            if cond.type != "bool": raise Exception("[Semantic] 'while' condition must be a boolean.")
            if not cond.value: break
            self.children[1].evaluate(st)

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


class Parser:
    # O Parser verifica a gramática. Todos os erros aqui são [Parser].
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
            if lex.next.kind != "IDEN":
                raise Exception("[Parser] Expected identifier after 'var'")
            iden = Identifier(lex.next.value)
            lex.select_next()

            # TYPE agora é opcional no parser
            var_type = None
            if lex.next.kind == "TYPE":
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

        # Lógica de fim de linha
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
    
    if filename.endswith(".go"):
        output_filename = filename[:-3] + ".asm"
    else:
        output_filename = filename + ".asm"

    try:
        with open(filename, "r", encoding='utf-8') as f: code = f.read()
        
        ast = Parser.run(code)
        st = SymbolTable()
        
        ast.generate(st)
        
        Code.dump(output_filename)
        print(f"Assembly code successfully generated: {output_filename}")
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.", file=sys.stderr); sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()